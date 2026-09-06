from web3 import Web3
import json

# Connect to Ganache
RPC_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise Exception("Could not connect to Ganache")

print("Connected to Ganache")
print("Chain ID:", w3.eth.chain_id)
print("Current block:", w3.eth.block_number)

# Get first Ganache account
account = w3.eth.accounts[0]
print("Deploying from:", account)

# Load compiled contract
with open("blockchain/compiled_contract.json", "r") as file:
    contract_data = json.load(file)

abi = contract_data["abi"]
bytecode = contract_data["evm"]["bytecode"]["object"]

# Create contract
EvidenceRegistry = w3.eth.contract(
    abi=abi,
    bytecode=bytecode
)

# Deploy
print("Deploying contract...")

transaction_hash = EvidenceRegistry.constructor().transact({
    "from": account
})

# Wait for deployment
transaction_receipt = w3.eth.wait_for_transaction_receipt(
    transaction_hash
)

contract_address = transaction_receipt.contractAddress

print("\nContract deployed successfully!")
print("Contract address:", contract_address)
print("Transaction hash:", transaction_receipt.transactionHash.hex())
print("Block number:", transaction_receipt.blockNumber)

# Save deployment information
deployment_info = {
    "contract_address": contract_address,
    "transaction_hash": transaction_receipt.transactionHash.hex(),
    "block_number": transaction_receipt.blockNumber,
    "abi": abi
}

with open("blockchain/deployment.json", "w") as file:
    json.dump(deployment_info, file, indent=2)

print("\nDeployment information saved to deployment.json")