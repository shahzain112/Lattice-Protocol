"""
Lattice Discovery Protocol
Agents automatically discover each other using gossip and DHT.
"""

import random
import time
import hashlib
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from .identity import AgentIdentity
from .registry import AgentRegistry, RegistryEntry


@dataclass
class GossipMessage:
    """Message propagated through the mesh."""
    message_type: str  # "peer_list", "capability_ad", "heartbeat"
    payload: dict
    ttl: int = 10
    origin: str = ""
    timestamp: float = 0.0


class DiscoveryProtocol:
    """
    Gossip-based Discovery Protocol

    Unlike MCP's static server list, Lattice uses:
    - Gossip protocol for peer discovery
    - Kademlia-style DHT for agent lookup
    - Bootstrap nodes for new agents
    """

    def __init__(self, registry: AgentRegistry, bootstrap_peers: List[str] = None):
        self.registry = registry
        self.bootstrap_peers = bootstrap_peers or []
        self._known_peers: Set[str] = set()
        self._gossip_history: Set[str] = set()  # Prevent loops
        self._dht_table: Dict[str, List[str]] = {}  # Hash -> agent_ids

    def bootstrap(self):
        """Connect to bootstrap peers and discover network."""
        for peer in self.bootstrap_peers:
            self._connect_to_peer(peer)

    def _connect_to_peer(self, peer_address: str):
        """Attempt to connect to a peer."""
        # In production, this would establish WebSocket/QUIC connection
        self._known_peers.add(peer_address)

    def gossip(self, message: GossipMessage) -> int:
        """
        Propagate message to random subset of peers.
        Returns number of peers messaged.
        """
        if message.ttl <= 0:
            return 0

        # Create message hash to prevent duplicate propagation
        msg_hash = hashlib.sha256(
            f"{message.origin}:{message.timestamp}:{message.message_type}".encode()
        ).hexdigest()

        if msg_hash in self._gossip_history:
            return 0

        self._gossip_history.add(msg_hash)

        # Select random peers (gossip factor)
        peers = list(self._known_peers)
        if len(peers) > 3:
            peers = random.sample(peers, 3)

        message.ttl -= 1

        # In production, send to peers via WebSocket
        return len(peers)

    def advertise_capabilities(self, identity: AgentIdentity):
        """Broadcast agent capabilities to the network."""
        message = GossipMessage(
            message_type="capability_ad",
            payload={
                "agent_id": identity.agent_id,
                "public_key": identity.public_key.hex(),
                "capabilities": [c.name for c in identity.capabilities],
                "trust_score": identity.trust_score,
                "endpoints": []  # Would be populated in production
            },
            origin=identity.agent_id,
            timestamp=time.time()
        )

        return self.gossip(message)

    def find_agent(self, agent_id: str) -> Optional[RegistryEntry]:
        """Find an agent by ID using DHT."""
        # Check local registry first
        entry = self.registry._entries.get(agent_id)
        if entry:
            return entry

        # Query DHT
        agent_hash = hashlib.sha256(agent_id.encode()).hexdigest()[:8]
        if agent_hash in self._dht_table:
            # Ask known holders
            pass

        return None

    def get_nearby_agents(self, capability: str, count: int = 5) -> List[str]:
        """Find nearby agents with a specific capability."""
        # In production, this would use network latency metrics
        return [
            e.identity.agent_id 
            for e in self.registry.discover(capability=capability, max_results=count)
        ]
