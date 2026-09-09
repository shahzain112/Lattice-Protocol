# registry.py
import time
from typing import Dict, List

class AgentRegistry:
    def __init__(self):
        self.agents: Dict[str, dict] = {} # public_key: agent_data

    def register_agent(self, public_key: str, capabilities: List[str], stake: float):
        if public_key in self.agents:
            return {"status": "error", "message": "Agent already registered"}
        
        self.agents[public_key] = {
            "capabilities": capabilities,
            "stake": stake,
            "trust_score": 50.0, # Starting trust
            "last_seen": time.time(),
            "tasks_completed": 0
        }
        return {"status": "success", "agent_id": public_key}

    def discover_agents(self, capability: str) -> List[dict]:
        """Find agents that can perform a specific task"""
        available = []
        for pub_key, data in self.agents.items():
            if capability in data["capabilities"] and data["trust_score"] > 20:
                available.append({
                    "agent_id": pub_key,
                    "fee": 0.5, # Dynamic pricing can be added later
                    "trust_score": data["trust_score"]
                })
        # Sort by trust score
        available.sort(key=lambda x: x["trust_score"], reverse=True)
        return available

# Global instance
lattice_registry = AgentRegistry()