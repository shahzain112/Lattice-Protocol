import hashlib
import hmac
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.fernet import Fernet
import base64

class LatticeVault:
    @staticmethod
    def generate_keys():
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def sign_request(private_key: ed25519.Ed25519PrivateKey, payload: dict) -> str:
        sorted_payload = json.dumps(payload, sort_keys=True)
        signature = private_key.sign(sorted_payload.encode())
        return base64.b64encode(signature).decode()

    @staticmethod
    def verify_signature(public_key: ed25519.Ed25519PublicKey, payload: dict, signature_b64: str) -> bool:
        try:
            sorted_payload = json.dumps(payload, sort_keys=True)
            signature = base64.b64decode(signature_b64)
            public_key.verify(signature, sorted_payload.encode())
            return True
        except Exception:
            return False

    @staticmethod
    def seal_file(data: str, secret_key: bytes) -> str:
        f = Fernet(base64.urlsafe_b64encode(secret_key.ljust(32, b'\0')))
        return f.encrypt(data.encode()).decode()