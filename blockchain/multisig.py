from web3 import Web3

class MultiSigHelper:
    def __init__(self, rpc_url="https://cloudflare-eth.com"):
        # Is line ko change karo
        self.w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/eth"))
    
    def is_multisig(self, address: str) -> dict:
        """Check if a wallet is a Gnosis Safe (Multi-Sig)"""
        # Gnosis Safe ke liye bytecode check
        code = self.w3.eth.get_code(address).hex()
        is_safe = '0x60806040' in code  # Gnosis Safe signature
        return {"address": address, "is_multisig": is_safe}