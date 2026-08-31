"""
Lattice Agent Registry
Global directory where agents register and discover each other.
This is the backbone of the Lattice mesh network.
"""

import time
import json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from .identity import AgentIdentity, AgentCapability, LatticeID


@dataclass
class RegistryEntry:
    """An entry in the global agent registry."""
    identity: AgentIdentity
    endpoints: List[str] = field(default_factory=list)  # WebSocket, HTTP, etc.
    region: str = "global"
    network_tier: str = "standard"  # standard, premium, validator
    is_relay: bool = False
    max_connections: int = 100
    current_connections: int = 0


class AgentRegistry:
    """
    Global Agent Registry

    Unlike MCP where tools are statically defined, Lattice agents:
    - Dynamically register/unregister
    - Update capabilities in real-time
    - Have health status
    - Can be discovered by location, trust, or capability
    """

    def __init__(self):
        self._entries: Dict[str, RegistryEntry] = {}
        self._id_system = LatticeID()
        self._subscribers: List[Callable] = []
        self._health_check_interval = 30  # seconds

    def register(self, entry: RegistryEntry) -> bool:
        """Register an agent in the global registry."""
        agent_id = entry.identity.agent_id

        if agent_id in self._entries:
            # Update existing entry
            self._entries[agent_id] = entry
            self._notify_subscribers("updated", entry)
            return True

        # New registration
        self._entries[agent_id] = entry
        self._id_system.register_agent(entry.identity)
        self._notify_subscribers("registered", entry)

        return True

    def unregister(self, agent_id: str) -> bool:
        """Remove an agent from registry."""
        if agent_id in self._entries:
            entry = self._entries.pop(agent_id)
            self._notify_subscribers("unregistered", entry)
            return True
        return False

    def discover(self, 
                 capability: Optional[str] = None,
                 min_trust: float = 50.0,
                 region: Optional[str] = None,
                 max_results: int = 10) -> List[RegistryEntry]:
        """
        Discover agents based on criteria.
        This is the core of Lattice's decentralized routing.
        """
        results = []

        for entry in self._entries.values():
            # Trust filter
            if entry.identity.trust_score < min_trust:
                continue

            # Region filter
            if region and entry.region != region:
                continue

            # Capability filter
            if capability:
                cap_names = [c.name for c in entry.identity.capabilities]
                if capability not in cap_names:
                    continue

            results.append(entry)

            if len(results) >= max_results:
                break

        # Sort by trust score (highest first)
        results.sort(key=lambda e: e.identity.trust_score, reverse=True)
        return results

    def get_relay_nodes(self) -> List[RegistryEntry]:
        """Get agents that can act as relay nodes."""
        return [e for e in self._entries.values() if e.is_relay]

    def get_validator_nodes(self) -> List[RegistryEntry]:
        """Get validator-tier agents."""
        return [e for e in self._entries.values() if e.network_tier == "validator"]

    def subscribe(self, callback: Callable):
        """Subscribe to registry events."""
        self._subscribers.append(callback)

    def _notify_subscribers(self, event: str, entry: RegistryEntry):
        for callback in self._subscribers:
            try:
                callback(event, entry)
            except Exception:
                pass

    def health_check(self) -> Dict[str, bool]:
        """Check health of all registered agents."""
        now = time.time()
        health = {}

        for agent_id, entry in self._entries.items():
            # Consider unhealthy if not seen in 2 minutes
            is_healthy = (now - entry.identity.last_seen) < 120
            health[agent_id] = is_healthy

            if not is_healthy:
                # Reduce trust for unhealthy agents
                entry.identity.update_trust(-5.0)

        return health

    def get_stats(self) -> Dict:
        """Get registry statistics."""
        return {
            "total_agents": len(self._entries),
            "total_capabilities": len(self._id_system._capability_index),
            "relay_nodes": len(self.get_relay_nodes()),
            "validator_nodes": len(self.get_validator_nodes()),
            "avg_trust": sum(e.identity.trust_score for e in self._entries.values()) / max(len(self._entries), 1),
            "timestamp": time.time()
        }
