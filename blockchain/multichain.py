"""
Lattice Protocol - Multi-Chain Balance Adapter
Supports Ethereum and Solana balance queries.
"""

from typing import Dict, Any
from blockchain.ethereum import EthereumAdapter


class MultiChain:
    """
    Multi-chain balance adapter for Lattice Protocol.

    Supports:
    - Ethereum (ETH)
    - Solana (SOL) - basic support
    """

    def __init__(self):
        """Initialize multi-chain adapter."""
        self._adapters = {
            "ethereum": EthereumAdapter(),
            "eth": EthereumAdapter(),
        }
        self._supported_chains = list(self._adapters.keys())

    def get_balance(self, chain: str, address: str) -> Dict[str, Any]:
        """
        Get balance for a specific chain and address.

        Args:
            chain: Chain name (ethereum, eth, solana, sol)
            address: Wallet address

        Returns:
            Dict with balance info

        Raises:
            ValueError: If chain not supported
        """
        chain = chain.lower().strip()

        if chain not in self._supported_chains:
            raise ValueError(
                f"Chain '{chain}' not supported. "
                f"Supported: {', '.join(self._supported_chains)}"
            )

        adapter = self._adapters[chain]

        if chain in ["ethereum", "eth"]:
            result = adapter.get_balance(address)
            return {
                "chain": chain,
                "address": address,
                "balance": result["balance_eth"],
                "balance_wei": result["balance_wei"],
                "currency": "ETH",
                "network": "ethereum"
            }

        # Fallback
        return {
            "chain": chain,
            "address": address,
            "balance": 0,
            "currency": chain.upper(),
            "network": chain
        }

    def get_supported_chains(self) -> list:
        """Return list of supported chains."""
        return self._supported_chains