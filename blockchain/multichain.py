from web3 import Web3
from solana.rpc.api import Client

class MultiChain:
    def __init__(self):
        self.eth = Web3(Web3.HTTPProvider("https://cloudflare-eth.com"))
        self.polygon = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
        self.sol = Client("https://api.mainnet-beta.solana.com")
    
    def get_balance(self, chain: str, address: str):
        if chain == "ethereum":
            return f"{self.eth.from_wei(self.eth.eth.get_balance(address), 'ether')} ETH"
        elif chain == "polygon":
            return f"{self.polygon.from_wei(self.polygon.eth.get_balance(address), 'ether')} MATIC"
        elif chain == "solana":
            bal = self.sol.get_balance(address)['result']['value']
            return f"{bal / 1e9} SOL"
        else:
            return "Unsupported chain"