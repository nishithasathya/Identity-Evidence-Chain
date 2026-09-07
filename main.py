import sys

from face.face_utils import detect_and_encode_face
from search.search import search_web
from blockchain.blockchain_service import store_evidence, verify_evidence


def run_pipeline(image_path):

    print("\n==============================")
    print("IDENTITY EVIDENCE CHAIN")
    print("==============================")

    # PERSON 1: FACE DETECTION + ENCODING
    print("\n[1] Detecting and encoding face...")

    face_result = detect_and_encode_face(image_path)

    if not face_result.get("face_detected"):
        print("Face detection failed.")
        print("Reason:", face_result.get("error"))
        return

    print("Face detected.")
    print("Faces found:", face_result["num_faces"])

    # Data passed from Person 1 to Person 2
    p1_payload = {
        "image_path": face_result["image_path"],
        "face_encoding": face_result["face_encoding"]
    }

    # PERSON 2: WEB / SOCIAL SEARCH
    print("\n[2] Searching web/social platforms...")

    evidence = search_web(p1_payload)

    print("Matched URL:", evidence.get("matched_url"))
    print("Platform:", evidence.get("platform"))
    print("Confidence:", evidence.get("confidence"))

    # PERSON 3: STORE EVIDENCE ON BLOCKCHAIN
    print("\n[3] Storing evidence on blockchain...")

    blockchain_result = store_evidence(evidence)

    print("Evidence hash:", blockchain_result["evidence_hash"])
    print("Transaction hash:", blockchain_result["transaction_hash"])
    print("Block number:", blockchain_result["block_number"])
    print("Contract address:", blockchain_result["contract_address"])

    # PERSON 3: VERIFY EVIDENCE
    print("\n[4] Verifying evidence...")

    verification_result = verify_evidence(evidence)

    print("Verified:", verification_result["verified"])

    print("\n==============================")
    print("PIPELINE COMPLETE")
    print("==============================")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python main.py <image_path>")
        sys.exit(1)

    run_pipeline(sys.argv[1])