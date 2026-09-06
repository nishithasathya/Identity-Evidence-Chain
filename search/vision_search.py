"""Google Cloud Vision Web Detection adapter.

Cloud Vision Web Detection returns matching pages/images and visually similar
images for a supplied image. Authentication uses Google Application Default
Credentials, including GOOGLE_APPLICATION_CREDENTIALS when set.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def detect_web(image_path: str) -> dict[str, Any]:
    from google.cloud import vision

    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    client = vision.ImageAnnotatorClient()
    content = path.read_bytes()
    image = vision.Image(content=content)
    response = client.web_detection(image=image)

    if response.error.message:
        raise RuntimeError(response.error.message)

    web = response.web_detection
    pages = []
    for page in web.pages_with_matching_images:
        pages.append(
            {
                "url": page.url,
                "image_url": page.full_matching_images[0].url
                if page.full_matching_images
                else (page.partial_matching_images[0].url if page.partial_matching_images else None),
                "match_type": "full" if page.full_matching_images else "partial",
            }
        )

    similar = [
        {"image_url": image.url, "match_type": "visually_similar"}
        for image in web.visually_similar_images
    ]

    entities = [
        {"description": entity.description, "score": float(entity.score)}
        for entity in web.web_entities
    ]

    return {
        "pages": pages,
        "similar_images": similar,
        "entities": entities,
        "best_guess_labels": [label.label for label in web.best_guess_labels],
    }
