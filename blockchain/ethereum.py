from web3 import Web3

class EthereumAdapter:
    def __init__(self, rpc_url="https://cloudflare-eth.com"):
        # Public free RPC (Read-only). Production mein Infura/Alchemy use karo.
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    def get_balance(self, address: str) -> str:
        if not self.w3.is_address(address):
            return "Invalid Address Format"
        try:
            balance_wei = self.w3.eth.get_balance(address)
            balance_eth = self.w3.from_wei(balance_wei, 'ether')
            return f"{balance_eth:.4f} ETH"
        except Exception as e:
            return f"RPC Error: {str(e)}"