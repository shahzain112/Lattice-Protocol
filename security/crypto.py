"""
Lattice Cryptographic Vault
Handles key generation, signing, and encryption.
"""

from typing import Tuple
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


class LatticeVault:
    """
    Cryptographic vault for Lattice protocol.

    Provides:
    - Ed25519 key pair generation
    - Message signing and verification
    - Key serialization
    """

    @staticmethod
    def generate_keys() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
        """Generate a new Ed25519 key pair."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def sign_message(private_key: ed25519.Ed25519PrivateKey, message: bytes) -> bytes:
        """Sign a message with private key."""
        return private_key.sign(message)

    @staticmethod
    def verify_signature(public_key: ed25519.Ed25519PublicKey, message: bytes, signature: bytes) -> bool:
        """Verify a signature with public key."""
        try:
            public_key.verify(signature, message)
            return True
        except Exception:
            return False

    @staticmethod
    def serialize_private_key(private_key: ed25519.Ed25519PrivateKey) -> bytes:
        """Serialize private key to bytes."""
        return private_key.private_bytes_raw()

    @staticmethod
    def serialize_public_key(public_key: ed25519.Ed25519PublicKey) -> bytes:
        """Serialize public key to bytes."""
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )