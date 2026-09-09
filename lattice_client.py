# lattice_client.py
import requests
import json
import time
import os
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class LatticeClient:
    """
    Lattice Protocol ka Official Client SDK.
    Developers ko sirf itna karna hai:
    client = LatticeClient()
    result = client.execute("health_check")
    """
    def __init__(self, server_url="http://localhost:8080", key_file="lattice_client_key.pem"):
        self.server_url = server_url.rstrip("/")
        self.api_endpoint = f"{self.server_url}/lattice/v1/execute"
        self.key_file = key_file
        
        # Keys load karo ya naya bana lo
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(f.read())
        else:
            self.private_key = ed25519.Ed25519PrivateKey.generate()
            with open(key_file, "wb") as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                ))
        
        self.public_key = self.private_key.public_key()
        self.public_key_hex = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        ).hex()

    def _sign_payload(self, payload):
        """Payload ko Ed25519 se sign karta hai"""
        payload_to_sign = payload.copy()
        payload_to_sign["sender_id"] = self.public_key_hex
        
        # JSON ko sort karke string banao (server ke hisaab se)
        message = json.dumps(payload_to_sign, sort_keys=True).encode('utf-8')
        signature = self.private_key.sign(message).hex()
        
        payload["sender_id"] = self.public_key_hex
        payload["signature"] = signature
        return payload

    def execute(self, action: str, payload_data: dict = None):
        """Server pe request bhejne ke liye main function"""
        if payload_data is None:
            payload_data = {}
            
        request_body = {
            "request_id": f"req_{int(time.time() * 1000)}",
            "action": action,
            "payload": payload_data,
            "timestamp": int(time.time())
        }
        
        signed_request = self._sign_payload(request_body)
        
        try:
            response = requests.post(self.api_endpoint, json=signed_request, timeout=10)
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}