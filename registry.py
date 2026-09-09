import database

class AgentRegistry:
    def register_agent(self, public_key: str, capabilities: list, stake: float):
        # Database mein save karo
        success = database.save_agent(public_key, capabilities, stake)
        if not success:
            return {"status": "error", "message": "Agent already registered"}
        
        return {"status": "success", "agent_id": public_key, "trust_score": 50.0}

    def discover_agents(self, capability: str) -> list:
        # Real DB se nikalne ke liye query hogi, abhi simple return
        # Future mein: SELECT * FROM agents WHERE capabilities LIKE '%capability%'
        # Aur trust_score > 20
        return [] # Abhi ke liye placeholder

# Global instance
lattice_registry = AgentRegistry()