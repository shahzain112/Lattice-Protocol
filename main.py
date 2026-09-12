import json
import time
import logging
import hmac
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives.asymmetric import ed25519

# Lattice Core Imports
from security.crypto import LatticeVault
from core.messages import parse_secure_request, LatticeResponse, LatticeRequest
from data_engine.pipeline import DataEngineCore

# -------------------- DATABASE IMPORT --------------------
import database
database.init_db()  # Initialize DB on startup

# -------------------- LATTICE ECOSYSTEM IMPORTS --------------------
# Yeh MCP se bilkul alag hai - Agent Mesh Protocol
from core.identity import AgentIdentity, AgentCapability
from core.registry import AgentRegistry, RegistryEntry
from core.trust import TrustEngine, TrustEvent

# Global ecosystem instances (in-memory for v2.0)
_lattice_registry = AgentRegistry()
_lattice_trust = TrustEngine()

# -------------------- SECURITY SETUP --------------------
# Audit Log: Har request ka record rakhta hai
logging.basicConfig(
    filename='lattice_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiting storage (simple in-memory)
_request_counts: Dict[str, list] = {}
RATE_LIMIT = 100  # requests per minute

# Load secrets from environment (NEVER hardcode!)
GAMING_SECRET = os.environ.get('LATTICE_GAMING_SECRET', 'Lattice_Gaming_Secret_2024').encode()

# Generate or Load Server Private Key (DO NOT SHARE THIS FILE)
_private_key: Optional[ed25519.Ed25519PrivateKey] = None
_public_key: Optional[ed25519.Ed25519PublicKey] = None

try:
    with open("server_private.pem", "rb") as f:
        _private_key = ed25519.Ed25519PrivateKey.from_private_bytes(f.read())
        _public_key = _private_key.public_key()
    print("🔑 Existing Server Key Loaded.")
except FileNotFoundError:
    _private_key, _public_key = LatticeVault.generate_keys()
    with open("server_private.pem", "wb") as f:
        f.write(_private_key.private_bytes_raw())
    print("🔐 New Secure Keys Generated. Keep 'server_private.pem' SAFE!")

# -------------------- RATE LIMITER --------------------
def _check_rate_limit(client_id: str) -> bool:
    """Check if client has exceeded rate limit."""
    current_time = time.time()
    if client_id not in _request_counts:
        _request_counts[client_id] = []

    # Remove old entries (older than 60 seconds)
    _request_counts[client_id] = [
        t for t in _request_counts[client_id] 
        if current_time - t < 60
    ]

    if len(_request_counts[client_id]) >= RATE_LIMIT:
        return False

    _request_counts[client_id].append(current_time)
    return True


# -------------------- LATTICE ECOSYSTEM FUNCTIONS --------------------

def register_agent(sender_id: str, capabilities: list, stake: float = 0.0) -> dict:
    """
    Register a new agent in the Lattice ecosystem.
    """
    agent = AgentIdentity()
    
    # Set the agent ID to the test public ID (sender_id).
    agent.agent_id = sender_id
    
    for cap in capabilities:
        agent.add_capability(AgentCapability(**cap))

    agent.stake_amount = stake
    agent.update_trust(stake / 10)

    entry = RegistryEntry(
        identity=agent,
        endpoints=["ws://localhost:8080"],
        network_tier="premium" if stake > 1000 else "standard"
    )

    _lattice_registry.register(entry)
    _lattice_trust.update_stake(agent.agent_id, stake)

    # This line has been added to save it in the DB.
    database.add_agent(agent.agent_id, str([c.name for c in agent.capabilities]), stake, agent.trust_score, 0, "active")

    return {
        "agent_id": agent.agent_id,
        "public_key": agent.public_key.hex()[:32] + "...",
        "trust_score": agent.trust_score,
        "stake_amount": agent.stake_amount,
        "capabilities": [c.name for c in agent.capabilities],
        "status": "registered"
    }

def discover_agents(capability: str, min_trust: float = 50.0) -> list:
    """
    Discover agents by capability.
    MCP mein yeh NAHI hai!
    """
    agents = _lattice_registry.discover(
        capability=capability,
        min_trust=min_trust
    )
    return [
        {
            "agent_id": e.identity.agent_id,
            "trust_score": e.identity.trust_score,
            "stake": e.identity.stake_amount,
            "tier": e.network_tier,
            "fee": next((c.fee for c in e.identity.capabilities if c.name == capability), 0)
        }
        for e in agents
    ]

def get_agent_trust(agent_id: str) -> dict:
    """
    Get trust report for an agent.
    MCP mein yeh NAHI hai!
    """
    return _lattice_trust.get_trust_report(agent_id)

def get_ecosystem_stats() -> dict:
    """Get ecosystem statistics."""
    return {
        "registry": _lattice_registry.get_stats(),
        "total_agents": len(_lattice_registry.get_all_agents()),
        "avg_trust": _lattice_registry.get_stats()["avg_trust"]
    }

# -------------------- MAIN REQUEST HANDLER --------------------
def handle_request(raw_input: bytes, client_id: Optional[str] = None) -> str:
    """
    Handle incoming Lattice protocol requests.

    Args:
        raw_input: Raw JSON bytes
        client_id: Optional client identifier for rate limiting

    Returns:
        JSON response string
    """
    # Rate limiting check
    if client_id and not _check_rate_limit(client_id):
        return json.dumps({
            "request_id": client_id or "unknown",
            "status": "error", 
            "error": "Rate limit exceeded. Max 100 requests/minute."
        })

    # 1. Parser: Stops malicious requests right here.
    try:
        req: LatticeRequest = parse_secure_request(raw_input)
    except ValueError as e:
        return json.dumps({"request_id": "unknown", "status": "error", "error": str(e)})
    except json.JSONDecodeError:
        return json.dumps({"request_id": "unknown", "status": "error", "error": "Invalid JSON format"})

    # 2. Anti-Replay Protection: 60 second se purani request reject
    try:
        current_time = int(time.time())
        req_timestamp = int(req.timestamp) if req.timestamp is not None else 0

        if not isinstance(req_timestamp, int) or req_timestamp <= 0:
            return json.dumps({"request_id": req.request_id, "status": "error", "error": "Invalid timestamp"})

        if current_time - req_timestamp > 60:
            return json.dumps({"request_id": req.request_id, "status": "error", "error": "Request expired"})

        if req_timestamp > current_time + 10:
            return json.dumps({"request_id": req.request_id, "status": "error", "error": "Future timestamp not allowed"})
    except (TypeError, ValueError):
        return json.dumps({"request_id": req.request_id, "status": "error", "error": "Timestamp parsing failed"})

    # 3. Action Router
    response: Optional[LatticeResponse] = None

    if req.action == "health_check":
        response = LatticeResponse(
            request_id=req.request_id,
            status="success",
            data={"message": "Lattice is alive", "version": "2.0"}
        )

    elif req.action == "process_data":
        try:
            result = DataEngineCore.process_batch("sample.csv", req.payload)
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data={"result": result}
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Data processing error: {str(e)}"
            )

    elif req.action == "get_balance":
        try:
            from blockchain.ethereum import EthereumAdapter
            eth = EthereumAdapter()
            address = req.payload.get("address")
            if not address or not isinstance(address, str):
                raise ValueError("Valid address string required in payload")
            balance = eth.get_balance(address)
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data={"balance": balance}
            )
        except ImportError as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Blockchain module not available: {str(e)}"
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Blockchain error: {str(e)}"
            )

    elif req.action == "check_multisig":
        try:
            from blockchain.multisig import MultiSigHelper
            ms = MultiSigHelper()
            address = req.payload.get("address")
            if not address or not isinstance(address, str):
                raise ValueError("Valid address string required in payload")
            result = ms.is_multisig(address)
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data=result
            )
        except ImportError as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"MultiSig module not available: {str(e)}"
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Multi-Sig check error: {str(e)}"
            )

    elif req.action == "submit_game_score":
        try:
            player = req.payload.get("player")
            score = req.payload.get("score")
            provided_signature = req.payload.get("signature")

            if not player or not isinstance(player, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid player name"
                )
            elif score is None or not isinstance(score, (int, float)):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid score"
                )
            elif not provided_signature or not isinstance(provided_signature, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid signature"
                )
            else:
                computed = hmac.new(
                    GAMING_SECRET, 
                    f"{player}:{score}".encode(), 
                    hashlib.sha256
                ).hexdigest()
                if hmac.compare_digest(computed, provided_signature):
                    response = LatticeResponse(
                        request_id=req.request_id,
                        status="success",
                        data={"message": f"Score {score} verified for {player}!"}
                    )
                else:
                    response = LatticeResponse(
                        request_id=req.request_id,
                        status="error",
                        error="Cheating detected! Invalid signature."
                    )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Gaming error: {str(e)}"
            )

    elif req.action == "migrate_database":
        try:
            from adapters.sql import DataMigrationEngine
            source = req.payload.get("source_uri")
            target = req.payload.get("target_uri")
            tables = req.payload.get("tables")
            batch_size = req.payload.get("batch_size", 5000)

            if not source or not isinstance(source, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid source_uri"
                )
            elif not target or not isinstance(target, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid target_uri"
                )
            else:
                result = DataMigrationEngine.migrate_data(source, target, tables, batch_size)
                if result.get("status") == "success":
                    response = LatticeResponse(
                        request_id=req.request_id,
                        status="success",
                        data={"logs": result.get("logs", [])}
                    )
                else:
                    response = LatticeResponse(
                        request_id=req.request_id,
                        status="error",
                        error=result.get("error", "Unknown migration error")
                    )
        except ImportError as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Migration module not available: {str(e)}"
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Migration error: {str(e)}"
            )

    elif req.action == "enable_extension":
        try:
            from adapters.sql import DataMigrationEngine
            db_uri = req.payload.get("db_uri")
            ext_name = req.payload.get("extension_name")

            if not db_uri or not isinstance(db_uri, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid db_uri"
                )
            elif not ext_name or not isinstance(ext_name, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid extension_name"
                )
            else:
                result = DataMigrationEngine.create_postgres_extension(db_uri, ext_name)
                if result.get("status") == "success":
                    response = LatticeResponse(
                        request_id=req.request_id,
                        status="success",
                        data={"message": result.get("message", "Extension enabled")}
                    )
                else:
                    response = LatticeResponse(
                        request_id=req.request_id,
                        status="error",
                        error=result.get("error", "Unknown extension error")
                    )
        except ImportError as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Extension module not available: {str(e)}"
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Extension error: {str(e)}"
            )

    elif req.action == "run_swarm":
        try:
            from agents.swarm import AgentSwarm
            swarm = AgentSwarm()
            tasks = req.payload.get("tasks", [])
            if not isinstance(tasks, list):
                raise ValueError("tasks must be a list")
            for task in tasks:
                if not isinstance(task, dict) or "name" not in task:
                    raise ValueError("Each task must have a 'name' field")
                swarm.add_task(task["name"], task.get("data", {}))
            results = swarm.run_swarm()
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data={"results": results}
            )
        except ImportError as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Swarm module not available: {str(e)}"
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Swarm error: {str(e)}"
            )

    elif req.action == "store_vector":
        try:
            from adapters.vectordb import VectorStore
            db_uri = req.payload.get("db_uri")
            table = req.payload.get("table")
            embedding = req.payload.get("embedding")
            metadata = req.payload.get("metadata", {})

            if not db_uri or not isinstance(db_uri, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid db_uri"
                )
            elif not table or not isinstance(table, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid table"
                )
            elif not embedding or not isinstance(embedding, list):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid embedding (must be list)"
                )
            else:
                vs = VectorStore(db_uri)
                result = vs.store_embedding(table, embedding, metadata)
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="success",
                    data=result
                )
        except ImportError as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"VectorDB module not available: {str(e)}"
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Vector store error: {str(e)}"
            )

    elif req.action == "multichain_balance":
        try:
            from blockchain.multichain import MultiChain
            mc = MultiChain()
            chain = req.payload.get("chain")
            address = req.payload.get("address")

            if not chain or not isinstance(chain, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid chain"
                )
            elif not address or not isinstance(address, str):
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="error",
                    error="Missing or invalid address"
                )
            else:
                balance = mc.get_balance(chain, address)
                response = LatticeResponse(
                    request_id=req.request_id,
                    status="success",
                    data={"chain": chain, "address": address, "balance": balance}
                )
        except ImportError as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"MultiChain module not available: {str(e)}"
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Multi-chain error: {str(e)}"
            )


    # ==================== LATTICE ECOSYSTEM ACTIONS ====================
    # These actions are completely different from the MCP—Agent Mesh Protocol.

    elif req.action == "register_agent":
        try:
            capabilities = req.payload.get("capabilities", [])
            stake = req.payload.get("stake", 0.0)

            # Extract the sender_id (public key) from the request.
            sender_id = getattr(req, "sender_id", None) or req.payload.get("sender_id", "unknown")
            
            if not isinstance(capabilities, list):
                raise ValueError("capabilities must be a list")

            # Pass the Sender_ID.
            result = register_agent(sender_id, capabilities, stake)
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data=result
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Agent registration error: {str(e)}"
            )

    elif req.action == "discover_agents":
        try:
            capability = req.payload.get("capability", "")
            min_trust = req.payload.get("min_trust", 50.0)

            if not capability or not isinstance(capability, str):
                raise ValueError("capability string required")

            results = discover_agents(capability, min_trust)
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data={
                    "capability": capability,
                    "agents_found": len(results),
                    "agents": results
                }
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Discovery error: {str(e)}"
            )

    elif req.action == "get_agent_trust":
        try:
            agent_id = req.payload.get("agent_id", "")
            if not agent_id or not isinstance(agent_id, str):
                raise ValueError("agent_id string required")

            report = get_agent_trust(agent_id)
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data=report
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Trust report error: {str(e)}"
            )

    elif req.action == "get_ecosystem_stats":
        try:
            stats = get_ecosystem_stats()
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data=stats
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Stats error: {str(e)}"
            )

    # ==================== MCP BRIDGE MODULE ====================
    elif req.action == "bridge_mcp_tool":
        try:
            tool_name = req.payload.get("tool_name")
            arguments = req.payload.get("arguments", {})
            agent_id = req.payload.get("agent_id")
            
            if not tool_name or not isinstance(tool_name, str):
                raise ValueError("tool_name string required")
            
            # --- REAL MCP BRIDGE LOGIC ---
            # Here Lattice will call the actual Mcp Server
            # For now, we are decoupling this from real API calls.
            # So that an entry appears in your logs and there is proof that the tool was called..
            
            import requests as req_lib
            task_result = {}
            
            # Suppose that MCP tool is"get_crypto_price"
            if tool_name == "get_crypto_price":
                api_res = req_lib.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
                if api_res.status_code == 200:
                    task_result = {"tool": tool_name, "price": api_res.json().get("price")}
                    status_msg = "Success"
                    
                    # Agent ka trust score bhi badhao kyunki usne tool sahi chalaya
                    if agent_id:
                        agent_info = database.get_agent(agent_id)
                        if agent_info:
                            new_trust = min(100.0, agent_info[3] + 1.0)
                            database.update_trust(agent_id, new_trust)
                else:
                    task_result = {"error": "MCP Tool API failed"}
                    status_msg = "Failed"
            else:
                task_result = {"message": f"Tool {tool_name} not found in Lattice Bridge"}
                status_msg = "Unknown Tool"
            
            # Audit Log mein daalo
            if agent_id:
                database.log_task(agent_id, f"MCP Tool: {tool_name}", status_msg)
            
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data={"mcp_bridge_result": task_result, "log_status": status_msg}
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"MCP Bridge error: {str(e)}"
            )

    # ==================== NAYA LOGIC: EXECUTE_TASK & PAY_AGENT ====================
    
    elif req.action == "execute_task":
        try:
            agent_id = req.payload.get("agent_id")
            task_data = req.payload.get("task_data") or {}
            
            # 1. Checking if Agent is in Db or not
            agent_info = database.get_agent(agent_id)
            if not agent_info:
                raise ValueError("Agent not registered in Lattice")
                
            if agent_info[5] == 'slashed': # status check
                raise ValueError("Agent is slashed and cannot perform tasks")
            
            # --- New CODE: REAL API CALL (Like MCP Tool) ---
            import requests as req_lib
            
            task_result = {}
            new_trust = agent_info[3] # Current trust score
            
            # Maan lo agent ko Bitcoin ki price nikalni hai
            if task_data.get("query") == "get_btc_price":
                # Calling the public api of binance
                api_response = req_lib.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
                
                if api_response.status_code == 200:
                    btc_price = api_response.json().get("price")
                    task_result = {"tool": "crypto_api", "btc_price": btc_price}
                    
                    # 2. Increase Trust score (because Api is sccessfull)
                    new_trust = min(100.0, agent_info[3] + 2.0) 
                    database.update_trust(agent_id, new_trust)
                else:
                    # if Api fails decrease trust score
                    task_result = {"error": "External API failed"}
                    new_trust = max(0.0, agent_info[3] - 5.0)
                    database.update_trust(agent_id, new_trust)
            else:
                task_result = {"result": "Unknown query, no action taken"}
            
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data={
                    "agent_id": agent_id,
                    "result": task_result,
                    "new_trust_score": new_trust
                }
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Task execution error: {str(e)}"
            )

    elif req.action == "pay_agent":
        try:
            agent_id = req.payload.get("agent_id")
            amount = req.payload.get("amount")
            payer = req.payload.get("payer", "unknown")

            if not agent_id or not isinstance(agent_id, str):
                raise ValueError("agent_id string required")
            if not isinstance(amount, (int, float)) or amount <= 0:
                raise ValueError("amount must be a positive number")
            if not isinstance(payer, str):
                raise ValueError("payer must be a string")

            # Verify agent exists & is active
            agent_info = database.get_agent(agent_id)
            if not agent_info:
                raise ValueError("Agent not registered in Lattice")
            if agent_info[4] == 'slashed':
                raise ValueError("Cannot pay a slashed agent")

            # Record payment in DB
            database.record_payment(agent_id, amount, payer)

            # Refresh agent info for response
            updated = database.get_agent(agent_id)
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data={
                    "agent_id": agent_id,
                    "payer": payer,
                    "amount_paid": amount,
                    "new_stake": updated[5],
                    "message": f"Payment of {amount} recorded for agent {agent_id}"
                }
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=f"Payment error: {str(e)}"
            )

    # ==================== New LOGIC: SLASH_AGENT ====================

    elif req.action == "slash_agent":
        # Yeh NOV feature hai! Agar agent ne galat kiya, to trust zero karo
        try:
            agent_id = req.payload.get("agent_id")
            reason = req.payload.get("reason", "Bad behavior")
            
            # Yahan Financial Slashing hogi (Stake = 0)
            database.burn_stake(agent_id)
            
            # Audit log mein entry karo
            database.log_task(agent_id, f"Slashed: {reason}", "Stake Burned")
            
            response = LatticeResponse(
                request_id=req.request_id,
                status="success",
                data={"message": f"Agent {agent_id} slashed. Stake burned (0.0). Reason: {reason}"}
            )
        except Exception as e:
            response = LatticeResponse(
                request_id=req.request_id,
                status="error",
                error=str(e)
            )

    # ==================== END ECOSYSTEM ACTIONS ====================

    else:
        response = LatticeResponse(
            request_id=req.request_id,
            status="error",
            error="Unknown action"
        )

    # 4. Audit Trail
    if response:
        logging.info(f"ReqID: {req.request_id} | Action: {req.action} | Status: {response.status}")
        return response.model_dump_json()
    else:
        return json.dumps({"request_id": req.request_id ,"status": "error", "error": "Internal server error"})


# -------------------- TEST RUN (LOCAL) --------------------
if __name__ == "__main__":
    print("🚀 Lattice Secure Core v2.0 + Ecosystem Loaded!")
    print("⚡ Features: Health, Balance, MultiSig, Gaming, Migration, Extensions, Swarm, VectorDB, MultiChain, MCP Bridge.")
    print("🌐 Ecosystem: Agent Identity, Trust Scoring, Registry, Discovery")
    print(f"🔒 Rate Limit: {RATE_LIMIT} requests/minute per client")

    # Test 1: Health Check
    test_payload = {
        "request_id": "test_1234567890",
        "action": "health_check",
        "payload": {},
        "timestamp": int(time.time())
    }
    response = handle_request(json.dumps(test_payload).encode())
    print(f"✅ Health Check: {response}")

    # Test 2: Register Agent (Ecosystem)
    test_agent = {
        "request_id": "test_agent_001",
        "action": "register_agent",
        "payload": {
            "capabilities": [
                {"name": "eth_balance", "description": "Get ETH balance", "input_schema": {"address": "string"}, "output_schema": {"balance": "float"}, "fee": 0.5}
            ],
            "stake": 1500
        },
        "timestamp": int(time.time())
    }
    response = handle_request(json.dumps(test_agent).encode())
    print(f"✅ Agent Registration: {response}")

    # Test 3: Discover Agents
    test_discover = {
        "request_id": "test_disc_001",
        "action": "discover_agents",
        "payload": {"capability": "eth_balance", "min_trust": 0},
        "timestamp": int(time.time())
    }
    response = handle_request(json.dumps(test_discover).encode())
    print(f"✅ Agent Discovery: {response}")
    
    # Test 4: MCP Bridge
    test_mcp = {
        "request_id": "test_mcp_001",
        "action": "bridge_mcp_tool",
        "payload": {"tool_name": "search_web", "arguments": {"query": "Lattice Protocol"}},
        "timestamp": int(time.time())
    }
    response = handle_request(json.dumps(test_mcp).encode())
    print(f"✅ MCP Bridge: {response}")

    print("\n💡 To start the HTTP server, run: python server.py")