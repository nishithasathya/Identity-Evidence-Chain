import json
import hashlib


def canonicalize_evidence(evidence):
    """
    Convert evidence into a deterministic JSON string.
    """

    return json.dumps(
        evidence,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    )


def hash_evidence(evidence):
    """
    Generate a SHA-256 fingerprint of the evidence.
    """

    canonical_data = canonicalize_evidence(evidence)

    evidence_hash = hashlib.sha256(
        canonical_data.encode("utf-8")
    ).digest()

    return evidence_hash


if __name__ == "__main__":

    # Temporary test evidence
    evidence = {
        "matched_url": "https://example.com/post/123",
        "platform": "Instagram",
        "image_url": "https://example.com/image.jpg",
        "caption": "Example post",
        "author": "example_user",
        "timestamp": "2026-09-06T10:00:00",
        "confidence": 0.95
    }

    canonical = canonicalize_evidence(evidence)
    evidence_hash = hash_evidence(evidence)

    print("CANONICAL EVIDENCE:")
    print(canonical)

    print("\nSHA-256:")
    print(evidence_hash.hex())