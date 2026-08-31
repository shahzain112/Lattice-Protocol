from solana.rpc.api import Client
from solders.pubkey import Pubkey  # <-- Yeh import zaroori hai
from web3 import Web3

class MultiChain:
    def __init__(self):
        self.eth = Web3(Web3.HTTPProvider("https://cloudflare-eth.com"))
        self.polygon = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
        # Solana ke liye reliable RPC
        self.sol = Client("https://api.mainnet-beta.solana.com")
    
    def get_balance(self, chain: str, address: str):
        if chain == "ethereum":
            return f"{self.eth.from_wei(self.eth.eth.get_balance(address), 'ether')} ETH"
        elif chain == "polygon":
            return f"{self.polygon.from_wei(self.polygon.eth.get_balance(address), 'ether')} MATIC"
        elif chain == "solana":
            try:
                # 🔥 FIX: String ko Pubkey object mein convert karo
                pubkey = Pubkey.from_string(address)
                bal = self.sol.get_balance(pubkey)['result']['value']
                return f"{bal / 1e9} SOL"
            except Exception as e:
                return f"Solana error: {str(e)}"
        else:
            return "Unsupported chain"