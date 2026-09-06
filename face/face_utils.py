import os
import cv2
from deepface import DeepFace

def detect_and_encode_face(image_path, model_name="Facenet", detector_backend="mtcnn"):
    """
    Detects a face in the given image and returns its encoding.
    Handles: missing file, no face found, multiple faces found.
    """
    if not os.path.exists(image_path):
        return {"image_path": image_path, "face_detected": False, "error": "file_not_found"}

    try:
        results = DeepFace.represent(
            img_path=image_path,
            model_name=model_name,
            detector_backend=detector_backend,
            enforce_detection=True
        )
    except ValueError:
        return {"image_path": image_path, "face_detected": False, "error": "no_face_found", "num_faces": 0}

    if len(results) > 1:
        # Multiple faces: assume the largest one is the subject
        results = sorted(results, key=lambda r: r["facial_area"]["w"] * r["facial_area"]["h"], reverse=True)

    best = results[0]
    return {
        "image_path": image_path,
        "face_detected": True,
        "num_faces": len(results),
        "bounding_box": best["facial_area"],
        "face_encoding": best["embedding"],
        "encoding_model": model_name,
        "detector_backend": detector_backend
    }

def save_cropped_face(image_path, bounding_box, output_path="outputs/cropped_face.jpg"):
    img = cv2.imread(image_path)
    x, y, w, h = bounding_box["x"], bounding_box["y"], bounding_box["w"], bounding_box["h"]
    cropped = img[y:y+h, x:x+w]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, cropped)
    return output_path