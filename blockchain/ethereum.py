"""
Lattice Protocol - Ethereum Blockchain Adapter
Provides ETH balance queries and multi-sig detection.
"""

from web3 import Web3
from typing import Dict, Any

# Default provider (can be overridden via environment or constructor)
DEFAULT_PROVIDER = "https://eth.llamarpc.com"


class EthereumAdapter:
    """
    Ethereum blockchain adapter for Lattice Protocol.

    Features:
    - ETH balance queries
    - Multi-sig wallet detection
    - Address validation
    """

    def __init__(self, provider_url: str = None):
        """
        Initialize Ethereum adapter.

        Args:
            provider_url: Ethereum RPC endpoint. Defaults to public LlamaRPC.
        """
        self.provider_url = provider_url or DEFAULT_PROVIDER
        self.w3 = Web3(Web3.HTTPProvider(self.provider_url))

    def _normalize_address(self, address: str) -> str:
        """
        Normalize Ethereum address for consistent handling.
        Handles mixed-case addresses and auto-corrects length issues.

        Args:
            address: Raw address string

        Returns:
            Validated lowercase address string

        Raises:
            ValueError: If address format is invalid
        """
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")

        address = address.strip().lower()

        if not address.startswith("0x"):
            raise ValueError(f"Address must start with '0x': {address}")

        # Use Web3's built-in validation which is more robust
        # and handles edge cases better than manual length checks
        if not self.w3.is_address(address):
            # Try to pad with zeros if too short, or truncate if too long
            # Ethereum addresses are exactly 42 chars (0x + 40 hex)
            hex_part = address[2:]
            if len(hex_part) < 40:
                # Pad with leading zeros
                hex_part = hex_part.zfill(40)
                address = "0x" + hex_part
            elif len(hex_part) > 40:
                # Truncate (shouldn't happen for valid addresses)
                hex_part = hex_part[:40]
                address = "0x" + hex_part

            # Validate again after correction
            if not self.w3.is_address(address):
                raise ValueError(f"Invalid Ethereum address format: {address}")

        return address

    def get_balance(self, address: str) -> Dict[str, Any]:
        """
        Get ETH balance for an address.

        Args:
            address: Ethereum address (0x...)

        Returns:
            Dict with balance in wei and ether

        Raises:
            ValueError: If address is invalid
            ConnectionError: If RPC is unreachable
        """
        # Normalize and validate address
        normalized_address = self._normalize_address(address)

        # Check connection
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to Ethereum node at {self.provider_url}")

        try:
            # Convert to checksum address from normalized lowercase
            checksum_address = Web3.to_checksum_address(normalized_address)

            # Get balance in wei
            balance_wei = self.w3.eth.get_balance(checksum_address)

            # Convert to ether
            balance_eth = Web3.from_wei(balance_wei, 'ether')

            return {
                "address": address,
                "balance_wei": balance_wei,
                "balance_eth": float(balance_eth),
                "currency": "ETH",
                "network": "ethereum",
                "provider": self.provider_url
            }

        except Exception as e:
            raise RuntimeError(f"Failed to fetch balance: {str(e)}")

    def is_multisig(self, address: str) -> Dict[str, Any]:
        """
        Check if an address is a multi-sig wallet.

        Args:
            address: Ethereum address to check

        Returns:
            Dict with is_multisig flag and details
        """
        # Normalize and validate address
        normalized_address = self._normalize_address(address)

        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to Ethereum node at {self.provider_url}")

        try:
            checksum_address = Web3.to_checksum_address(normalized_address)

            # Get code at address
            code = self.w3.eth.get_code(checksum_address)

            # If no code, it's an EOA (not a contract, so not multi-sig)
            if code == b'' or code == b'0x':
                return {
                    "address": address,
                    "is_multisig": False,
                    "is_contract": False,
                    "reason": "Externally Owned Account (EOA)"
                }

            # Check for multi-sig patterns in bytecode
            code_hex = code.hex().lower()

            # Common multi-sig function signatures
            multisig_indicators = [
                "submitTransaction",
                "confirmTransaction",
                "executeTransaction",
                "addOwner",
                "removeOwner",
                "replaceOwner",
                "changeRequirement",
                "0x173825d9",
                "0xc01a8c84",
                "0xee22610b",
            ]

            is_multisig = any(indicator.lower() in code_hex for indicator in multisig_indicators)

            return {
                "address": address,
                "is_multisig": is_multisig,
                "is_contract": True,
                "bytecode_size": len(code),
                "reason": "Multi-sig contract detected" if is_multisig else "Smart contract (not multi-sig)"
            }

        except Exception as e:
            raise RuntimeError(f"Failed to check multi-sig status: {str(e)}")

    def validate_address(self, address: str) -> bool:
        """
        Validate Ethereum address format.

        Args:
            address: Address to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            self._normalize_address(address)
            return True
        except (ValueError, TypeError):
            return False


class MultiSigHelper:
    """
    Helper class for multi-sig operations.
    Wrapper around EthereumAdapter for Lattice Protocol compatibility.
    """

    def __init__(self, provider_url: str = None):
        self.adapter = EthereumAdapter(provider_url)

    def is_multisig(self, address: str) -> Dict[str, Any]:
        """Check if address is multi-sig."""
        return self.adapter.is_multisig(address)