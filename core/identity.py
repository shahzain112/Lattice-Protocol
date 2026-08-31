"""
Lattice Identity System
Every agent in the Lattice ecosystem has a unique cryptographic identity.
This is fundamentally different from MCP where there is no identity layer.
"""

import uuid
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import hashlib


@dataclass
class AgentCapability:
    """What an agent can do."""
    name: str
    description: str
    input_schema: Dict
    output_schema: Dict
    fee: float = 0.0  # LTT tokens
    avg_latency_ms: int = 0
    success_rate: float = 1.0


@dataclass 
class AgentIdentity:
    """
    Lattice Agent Identity

    Unlike MCP's simple tool listing, Lattice agents have:
    - Cryptographic identity (Ed25519)
    - Trust score (reputation)
    - Capability advertisement
    - Stake amount (economic security)
    """
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    public_key: bytes = field(default=b"")
    capabilities: List[AgentCapability] = field(default_factory=list)
    trust_score: float = 50.0  # 0-100
    stake_amount: float = 0.0  # LTT tokens
    registered_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    total_tasks: int = 0
    successful_tasks: int = 0
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.public_key:
            private_key = ed25519.Ed25519PrivateKey.generate()
            self.public_key = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            # Store private key securely (in production, use HSM)
            self._private_key = private_key

    def sign_message(self, message: bytes) -> bytes:
        """Sign a message with agent's private key."""
        return self._private_key.sign(message)

    def verify_signature(self, message: bytes, signature: bytes) -> bool:
        """Verify a signature from another agent."""
        try:
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(self.public_key)
            public_key.verify(signature, message)
            return True
        except Exception:
            return False

    def add_capability(self, capability: AgentCapability):
        """Advertise a new capability."""
        self.capabilities.append(capability)

    def update_trust(self, delta: float):
        """Update trust score (e.g., after task completion or slashing)."""
        self.trust_score = max(0.0, min(100.0, self.trust_score + delta))

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "public_key": self.public_key.hex(),
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description,
                    "fee": c.fee,
                    "success_rate": c.success_rate
                }
                for c in self.capabilities
            ],
            "trust_score": self.trust_score,
            "stake_amount": self.stake_amount,
            "registered_at": self.registered_at,
            "last_seen": self.last_seen,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AgentIdentity":
        agent = cls(
            agent_id=data["agent_id"],
            public_key=bytes.fromhex(data["public_key"]),
            trust_score=data.get("trust_score", 50.0),
            stake_amount=data.get("stake_amount", 0.0),
            registered_at=data.get("registered_at", time.time()),
            last_seen=data.get("last_seen", time.time()),
            total_tasks=data.get("total_tasks", 0),
            successful_tasks=data.get("successful_tasks", 0),
            metadata=data.get("metadata", {})
        )
        for cap in data.get("capabilities", []):
            agent.capabilities.append(AgentCapability(**cap))
        return agent


class LatticeID:
    """Central identity manager for the Lattice ecosystem."""

    def __init__(self):
        self._identities: Dict[str, AgentIdentity] = {}
        self._capability_index: Dict[str, Set[str]] = {}  # capability -> agent_ids

    def register_agent(self, identity: AgentIdentity) -> bool:
        """Register a new agent in the ecosystem."""
        if identity.agent_id in self._identities:
            return False

        self._identities[identity.agent_id] = identity

        # Index capabilities
        for cap in identity.capabilities:
            if cap.name not in self._capability_index:
                self._capability_index[cap.name] = set()
            self._capability_index[cap.name].add(identity.agent_id)

        return True

    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        return self._identities.get(agent_id)

    def find_agents_by_capability(self, capability_name: str, min_trust: float = 0.0) -> List[AgentIdentity]:
        """Find agents that can perform a specific capability."""
        agent_ids = self._capability_index.get(capability_name, set())
        agents = [self._identities[aid] for aid in agent_ids]
        return [a for a in agents if a.trust_score >= min_trust]

    def get_all_agents(self) -> List[AgentIdentity]:
        return list(self._identities.values())

    def heartbeat(self, agent_id: str):
        """Update last seen timestamp."""
        if agent_id in self._identities:
            self._identities[agent_id].last_seen = time.time()
