# crypto_auth.py
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import json
import time

REPLAY_WINDOW = 60 # seconds

def verify_lattice_signature(payload: dict) -> bool:
    """
    Verifies if the request was actually signed by the agent's private key.
    """
    public_key_hex = payload.get("sender_id")
    signature_hex = payload.get("signature")
    
    if not public_key_hex or not signature_hex:
        return False
            
    # Anti-Replay Check
    current_time = time.time()
    request_time = payload.get("timestamp", 0)
    if isinstance(request_time, str):
        try: 
            request_time = int(request_time)
        except: 
            return False
    if abs(current_time - request_time) > REPLAY_WINDOW:
        return False

    try:
        verify_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        
        # Create a copy of payload WITHOUT the signature to verify it
        payload_to_verify = payload.copy()
        del payload_to_verify["signature"]
        
        message = json.dumps(payload_to_verify, sort_keys=True).encode()
        verify_key.verify(bytes.fromhex(signature_hex), message)
        return True
    except Exception:
        return False