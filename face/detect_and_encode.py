import json
import sys
from face_utils import detect_and_encode_face, save_cropped_face

def main():
    if len(sys.argv) < 2:
        print("Usage: python detect_and_encode.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    result = detect_and_encode_face(image_path)

    if result["face_detected"]:
        cropped_path = save_cropped_face(image_path, result["bounding_box"])
        result["cropped_face_path"] = cropped_path
        print(f"Face detected. Faces found: {result['num_faces']}. Encoding length: {len(result['face_encoding'])}")
        print(f"Cropped face saved to: {cropped_path}")
    else:
        print(f"No face detected. Reason: {result.get('error')}")

    with open("outputs/face_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Saved outputs/face_output.json")

if __name__ == "__main__":
    main()