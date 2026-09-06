from web3 import Web3
import json

from evidence import hash_evidence


RPC_URL = "http://127.0.0.1:7545"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise Exception("Could not connect to Ganache")


# Load deployed contract
with open("blockchain/deployment.json", "r") as file:
    deployment = json.load(file)

contract = w3.eth.contract(
    address=deployment["contract_address"],
    abi=deployment["abi"]
)


# --------------------------------
# ORIGINAL EVIDENCE
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


# Generate current hash
current_hash = hash_evidence(evidence)

print("CURRENT EVIDENCE HASH:")
print(current_hash.hex())


# Check blockchain
verified = contract.functions.verifyEvidence(
    current_hash
).call()

print("\nBLOCKCHAIN VERIFICATION:")
print("Verified:", verified)


if verified:
    print("\n✓ EVIDENCE VERIFIED")
else:
    print("\n✗ EVIDENCE NOT VERIFIED")


# --------------------------------
# TAMPER TEST
# --------------------------------

print("\n------------------------------")
print("TAMPER TEST")
print("------------------------------")

tampered_evidence = evidence.copy()

# Deliberately change one piece of evidence
tampered_evidence["caption"] = "CHANGED CAPTION"

tampered_hash = hash_evidence(tampered_evidence)

print("\nOriginal hash:")
print(current_hash.hex())

print("\nTampered hash:")
print(tampered_hash.hex())

tampered_verified = contract.functions.verifyEvidence(
    tampered_hash
).call()

print("\nTampered verification:")
print("Verified:", tampered_verified)


if current_hash != tampered_hash and not tampered_verified:
    print("\n✓ TAMPER DETECTED")
else:
    print("\n✗ TAMPER TEST FAILED")