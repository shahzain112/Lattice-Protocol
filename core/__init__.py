"""
Lattice Core Module
"""

# Try to import ecosystem modules (may not exist yet)
try:
    from .identity import AgentIdentity, AgentCapability, LatticeID
    from .registry import AgentRegistry, RegistryEntry
    from .discovery import DiscoveryProtocol, GossipMessage
    from .trust import TrustEngine, TrustEvent
    ECOSYSTEM_AVAILABLE = True
except ImportError:
    ECOSYSTEM_AVAILABLE = False

# Always import messages (required by main.py)
from .messages import LatticeRequest, LatticeResponse, parse_secure_request

__all__ = [
    "LatticeRequest", "LatticeResponse", "parse_secure_request"
]

if ECOSYSTEM_AVAILABLE:
    __all__.extend([
        "AgentIdentity", "AgentCapability", "LatticeID",
        "AgentRegistry", "RegistryEntry",
        "DiscoveryProtocol", "GossipMessage", 
        "TrustEngine", "TrustEvent"
    ])