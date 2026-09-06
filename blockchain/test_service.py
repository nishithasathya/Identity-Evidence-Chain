from blockchain_service import store_evidence, verify_evidence


evidence = {
    "matched_url": "https://example.com/post/123",
    "platform": "Instagram",
    "image_url": "https://example.com/image.jpg",
    "caption": "Example post",
    "author": "example_user",
    "timestamp": "2026-09-06T10:00:00",
    "confidence": 0.94
}


print("STORING EVIDENCE...\n")

result = store_evidence(evidence)

print("Hash:", result["evidence_hash"])
print("Transaction:", result["transaction_hash"])
print("Block:", result["block_number"])
print("Contract:", result["contract_address"])


print("\nVERIFYING EVIDENCE...\n")

verification = verify_evidence(evidence)

print("Hash:", verification["evidence_hash"])
print("Verified:", verification["verified"])