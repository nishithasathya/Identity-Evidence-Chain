from web3 import Web3
import json

from evidence import hash_evidence


# --------------------------------
# Connect to Ganache
# --------------------------------

RPC_URL = "http://127.0.0.1:7545"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise Exception("Could not connect to Ganache")

print("Connected to Ganache")
print("Latest block:", w3.eth.block_number)


# --------------------------------
# Load deployed contract
# --------------------------------

with open("blockchain/deployment.json", "r") as file:
    deployment = json.load(file)

contract = w3.eth.contract(
    address=deployment["contract_address"],
    abi=deployment["abi"]
)

print("Contract:", deployment["contract_address"])


# --------------------------------
# Evidence package
# --------------------------------

evidence = {
    "matched_url": "https://example.com/post/123",
    "platform": "Instagram",
    "image_url": "https://example.com/image.jpg",
    "caption": "Example post",
    "author": "example_user",
    "timestamp": "2026-09-06T10:00:00",
    "confidence": 0.94
}


# --------------------------------
# Generate evidence hash
# --------------------------------

evidence_hash = hash_evidence(evidence)

print("\nEvidence package:")
print(json.dumps(evidence, indent=2))

print("\nEvidence SHA-256:")
print(evidence_hash.hex())


# --------------------------------
# Store hash on blockchain
# --------------------------------

account = w3.eth.accounts[0]

print("\nUploading evidence hash...")

transaction_hash = contract.functions.storeEvidence(
    evidence_hash
).transact({
    "from": account
})

receipt = w3.eth.wait_for_transaction_receipt(
    transaction_hash
)


# --------------------------------
# Result
# --------------------------------

print("\nEvidence stored successfully!")

print("Transaction hash:")
print(receipt.transactionHash.hex())

print("\nBlock number:")
print(receipt.blockNumber)

print("\nContract address:")
print(deployment["contract_address"])


# --------------------------------
# Verify immediately
# --------------------------------

verified = contract.functions.verifyEvidence(
    evidence_hash
).call()

print("\nBlockchain verification:")
print("Verified:", verified)