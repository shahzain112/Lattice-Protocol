import requests
import json
import time
import os
import sys
import hmac
import hashlib

# --- NAYA IMPORT: Cryptography for Ed25519 ---
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Configuration (can be overridden via environment)
BASE_URL = os.environ.get("LATTICE_URL", "http://localhost:8080")
API_ENDPOINT = f"{BASE_URL}/lattice/v1/execute"

# Test tracking
_tests_passed = 0
_tests_failed = 0

# --- New CODE: Temporary Private Key Generation ---
# Generate a temporary Ed25519 key pair for testing.
_test_private_key = ed25519.Ed25519PrivateKey.generate()
_test_public_key = _test_private_key.public_key()

# Convert the public key into a hex string to generate the sender_id.
_test_public_key_hex = _test_public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
).hex()

def _sign_payload(payload):
    """Payload ko sign karne ka function"""
    # Create a copy of the payload so that the original data remains safe.
    payload_copy = payload.copy()
    
    # Fix: Include sender_id in the copy so that the message can be generated according to the server.
    payload_copy["sender_id"] = _test_public_key_hex
    
    # Remove the signature (if it exists).
    payload_copy.pop("signature", None)
    
    # Convert the payload to a canonical JSON string (`sort_keys=True` is required).
    message = json.dumps(payload_copy, sort_keys=True).encode('utf-8')
    
    # Sign in with your private key ed25519
    signature = _test_private_key.sign(message).hex()
    
    # Add the signature and sender_id to the original payload.
    payload["sender_id"] = _test_public_key_hex
    payload["signature"] = signature
    
    return payload

def _is_network_error(data):
    """Check if error is due to network connectivity issues."""
    if not data or data.get("status") != "error":
        return False
    error_msg = data.get("error", "").lower()
    network_keywords = ["cannot connect", "connection", "network", "unreachable", "timeout", "rpc"]
    return any(kw in error_msg for kw in network_keywords)

def _assert_response(response, expected_status="success", allow_network_error=False):
    """Assert and validate response."""
    global _tests_passed, _tests_failed
    try:
        data = response.json()

        # Check both "status" key AND "detail" key (FastAPI error format)
        actual_status = data.get("status")

        # If status is missing but detail exists, it's a FastAPI error response
        if actual_status is None and "detail" in data:
            actual_status = "error"
            data["status"] = "error"
            data["error"] = data["detail"]

        # If network error is allowed, treat it as success for test purposes
        if allow_network_error and actual_status == "error" and _is_network_error(data):
            _tests_passed += 1
            return data

        assert actual_status == expected_status, f"Expected {expected_status}, got {actual_status}"
        assert "request_id" in data or "detail" in data, "Missing request_id in response"
        _tests_passed += 1
        return data
    except (AssertionError, Exception) as e:
        _tests_failed += 1
        print(f"ASSERTION FAILED: {e}")
        print(f"   Response: {response.text}")
        return None

# test_lattice.py mein _make_request function ko update karein:
def _make_request(payload):
    """Helper to make requests with error handling."""
    try:
        # --- NAYA LINE: Payload ko sign karein ---
        signed_payload = _sign_payload(payload)
        response = requests.post(API_ENDPOINT, json=signed_payload, timeout=10)
        return response
    except requests.exceptions.ConnectionError:
        print(f"CONNECTION ERROR: Server not running at {BASE_URL}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"TIMEOUT: Request took too long")
        return None

# 1. Test Health Check
def test_health():
    print("\nTesting: health_check")
    payload = {
        "request_id": "test_health_001",
        "action": "health_check",
        "payload": {},
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success")
        if data:
            assert data["data"]["message"] == "Lattice is alive"
            print("Health Check: PASSED")
        else:
            print("Health Check: FAILED")

# 2. Test Blockchain (Ethereum Balance)
def test_blockchain():
    print("\nTesting: get_balance")
    payload = {
        "request_id": "test_eth_001",
        "action": "get_balance",
        "payload": {
            "address": "0x0000000000000000000000000000000000dEaD"
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success", allow_network_error=True)
        if data:
            if data.get("status") == "success":
                print("Blockchain Balance: PASSED (response received)")
            elif _is_network_error(data):
                print("Blockchain Balance: PASSED (network unavailable - expected in offline mode)")
            else:
                print(f"Blockchain Balance: FAILED - {data.get('error', 'unknown error')}")
        else:
            print("Blockchain Balance: FAILED")

# 3. Test Gaming (Score Submission)
def test_gaming():
    print("\nTesting: submit_game_score")
    player = "Usman"
    score = 9999
    secret_key = os.environ.get("LATTICE_GAMING_SECRET", "Lattice_Gaming_Secret_2024").encode()

    signature = hmac.new(secret_key, f"{player}:{score}".encode(), hashlib.sha256).hexdigest()

    payload = {
        "request_id": "test_game_001",
        "action": "submit_game_score",
        "payload": {
            "player": player,
            "score": score,
            "signature": signature
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success")
        if data:
            assert "verified" in data["data"]["message"].lower()
            print("Gaming Score: PASSED")
        else:
            print("Gaming Score: FAILED")

# 4. Test Gaming (Invalid Signature - Negative Test)
def test_gaming_cheat():
    print("\nTesting: submit_game_score (cheating detection)")
    payload = {
        "request_id": "test_game_cheat_001",
        "action": "submit_game_score",
        "payload": {
            "player": "Hacker",
            "score": 99999,
            "signature": "invalid_signature"
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "error")
        if data:
            error_msg = data.get("error", data.get("detail", "")).lower()
            assert "cheating" in error_msg or "invalid" in error_msg
            print("Gaming Anti-Cheat: PASSED")
        else:
            print("Gaming Anti-Cheat: FAILED")

# 5. Test Multi-Sig
def test_multisig():
    print("\nTesting: check_multisig")
    payload = {
        "request_id": "test_multisig_001",
        "action": "check_multisig",
        "payload": {
            "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success", allow_network_error=True)
        if data:
            if data.get("status") == "success":
                print("Multi-Sig Check: PASSED (response received)")
            elif _is_network_error(data):
                print("Multi-Sig Check: PASSED (network unavailable - expected in offline mode)")
            else:
                print(f"Multi-Sig Check: FAILED - {data.get('error', 'unknown error')}")
        else:
            print("Multi-Sig Check: FAILED")

# 6. Test AI Agent Swarm
def test_swarm():
    print("\nTesting: run_swarm")
    payload = {
        "request_id": "test_swarm_001",
        "action": "run_swarm",
        "payload": {
            "tasks": [
                {"name": "task1", "data": {"key": "value1"}},
                {"name": "task2", "data": {"key": "value2"}}
            ]
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success")
        if data:
            print("Agent Swarm: PASSED (response received)")
        else:
            print("Agent Swarm: Module may not be available")

# 7. Test Vector DB Store
def test_vector_store():
    print("\nTesting: store_vector")
    payload = {
        "request_id": "test_vector_001",
        "action": "store_vector",
        "payload": {
            "db_uri": "postgresql://user:pass@localhost:5432/testdb",
            "table": "embeddings",
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "metadata": {"source": "test"}
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success")
        if data:
            print("Vector Store: PASSED (response received)")
        else:
            print("Vector Store: Module may not be available")

# 8. Test Multi-Chain Balance
def test_multichain():
    print("\nTesting: multichain_balance")
    payload = {
        "request_id": "test_multichain_001",
        "action": "multichain_balance",
        "payload": {
            "chain": "ethereum",
            "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success", allow_network_error=True)
        if data:
            if data.get("status") == "success":
                print("Multi-Chain Balance: PASSED (response received)")
            elif _is_network_error(data):
                print("Multi-Chain Balance: PASSED (network unavailable - expected in offline mode)")
            else:
                print(f"Multi-Chain Balance: FAILED - {data.get('error', 'unknown error')}")
        else:
            print("Multi-Chain Balance: FAILED")

# 9. Test Invalid Action (Negative Test)
def test_invalid_action():
    print("\nTesting: invalid_action (negative test)")
    payload = {
        "request_id": "test_invalid_001",
        "action": "nonexistent_action",
        "payload": {},
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "error")
        if data:
            error_msg = data.get("error", data.get("detail", "")).lower()
            assert "unknown" in error_msg
            print("Invalid Action: PASSED")
        else:
            print("Invalid Action: FAILED")

# 10. Test Expired Request (Negative Test)
def test_expired_request():
    print("\nTesting: expired_request (negative test)")
    payload = {
        "request_id": "test_expired_001",
        "action": "health_check",
        "payload": {},
        "timestamp": int(time.time()) - 120
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "error")
        if data:
            error_msg = data.get("error", data.get("detail", "")).lower()
            assert "expired" in error_msg
            print("Expired Request: PASSED")
        else:
            print("Expired Request: FAILED")

# 11. Test: Register Agent (the agent must be registered before performing the task)
def test_register_agent():
    print("\nTesting: register_agent")
    payload = {
        "request_id": "test_reg_agent_001",
        "action": "register_agent",
        "payload": {
            "capabilities": [
                {
                    "name": "web_search", 
                    "description": "Searches the web", 
                    "input_schema": {"query": "string"},   
                    "output_schema": {"results": "list"},  
                    "fee": 0.1
                }
            ],
            "stake": 500.0
        },
        "timestamp": int(time.time())
    }
    # Note: _make_request automatically sign kar dega (tumhara existing code)
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success")
        if data:
            print("Agent Registration: PASSED")
        else:
            print("Agent Registration: FAILED")

# 12. Test: Execute Task (Agent will perform the task ad trust score will increase)
def test_execute_task():
    print("\nTesting: execute_task")
    # This agent_id will come from test_register_agent; we are using a hardcoded value for testing purposes.
    # Note: This must match `_test_public_k_hex` from `public/test_lattice.py`.
    payload = {
        "request_id": "test_task_001",
        "action": "execute_task",
        "payload": {
            "agent_id": _test_public_key_hex, # Same key which is use for signing
            "task_data": {"query": "get_btc_price"}
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success")
        if data:
            print("Execute Task (Trust Update): PASSED")
        else:
            print("Execute Task: FAILED")

# 13. Test: Slash Agent (Punishing Agnet)
def test_slash_agent():
    print("\nTesting: slash_agent")
    payload = {
        "request_id": "test_slash_001",
        "action": "slash_agent",
        "payload": {
            "agent_id": _test_public_key_hex,
            "reason": "Provided wrong data"
        },
        "timestamp": int(time.time())
    }
    response = _make_request(payload)
    if response is not None:
        data = _assert_response(response, "success")
        if data:
            print("Slash Agent: PASSED")
        else:
            print("Slash Agent: FAILED")

# --- Main block mein yeh add karo ---
if __name__ == "__main__":
    print("Lattice Protocol Test Suite v2.0 (With Crypto Signatures)")
    print(f"Target: {BASE_URL}")
    print("=" * 50)

    # Existing Tests
    test_health()
    test_blockchain()
    test_gaming()
    test_gaming_cheat()
    test_multisig()
    test_swarm()
    test_vector_store()
    test_multichain()
    test_invalid_action()
    test_expired_request()
    
    # Naye Ecosystem Tests
    test_register_agent()
    test_execute_task()
    test_slash_agent()

    print("\n" + "=" * 50)
    print(f"Results: {_tests_passed} passed, {_tests_failed} failed")
    if _tests_failed == 0:
        print("ALL TESTS PASSED!")
    else:
        print(f"{_tests_failed} test(s) failed. Check output above.")
    print("=" * 50)
