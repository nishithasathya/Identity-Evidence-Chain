from __future__ import annotations

import os
from typing import Any, Dict, List

from .filters import is_social_url, platform_for_url
from .face_match import compare_faces, download_image
from .serpapi_fallback import search_lens
from .vision_search import detect_web


def _vision_candidates(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert Google Vision Web Detection results into candidate pages.

    Vision is restricted to social/profile-style pages so that a generic
    university staff directory does not automatically win just because
    it contains the person's photograph.
    """
    candidates: List[Dict[str, Any]] = []

    for item in data.get("pages", []):
        url = item.get("url")

        if not url or not is_social_url(url):
            continue

        candidates.append(
            {
                "url": url,
                "title": item.get("pageTitle") or "",
                "score": 0.90,
                "source": "vision",
                "image_url": item.get("imageUrl"),
            }
        )

    return candidates


def _serp_candidates(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert SerpApi / Google Lens results into candidate pages.

    Unlike Vision candidates, SerpApi candidates are NOT restricted to
    social media. This allows exact university profile pages to be found.
    """
    candidates: List[Dict[str, Any]] = []

    if not data:
        return candidates

    items = data.get("visual_matches") or data.get("organic_results") or []

    for item in items:
        url = item.get("link") or item.get("url")

        if not url:
            continue

        title = (
            item.get("title")
            or item.get("name")
            or item.get("source")
            or ""
        )

        image_url = (
            item.get("thumbnail")
            or item.get("image")
            or item.get("image_url")
        )

        candidates.append(
            {
                "url": url,
                "title": title,
                "score": 0.80,
                "source": "serpapi",
                "image_url": image_url,
            }
        )

    return candidates


def _select_best(
    query_image: str,
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any] | None:
    """
    Face-verify candidate images and return the closest verified match.
    """
    if not candidates:
        return None

    best = None
    best_distance = float("inf")

    for candidate in candidates:
        image_url = candidate.get("image_url")

        if not image_url:
            continue

        try:
            local_image = download_image(image_url)

            result = compare_faces(query_image, local_image)

            if not result:
                continue

            verified = result.get("verified", False)
            distance = result.get("distance")

            if not verified or distance is None:
                continue

            if distance < best_distance:
                best_distance = distance

                best = {
                    **candidate,
                    "face_verified": True,
                    "face_distance": distance,
                }

        except Exception as exc:
            print(
                f"Face verification failed for "
                f"{candidate.get('url')}: {exc}"
            )

    return best


def search_web(image_path: str) -> Dict[str, Any]:
    """
    Run the complete P2 web/social evidence search.

    Order:
      1. Google Vision Web Detection
      2. Keep only social/profile candidates from Vision
      3. If needed, use SerpApi / Google Lens
      4. Face-verify candidate images
      5. Return the best matching page
    """

    vision_candidates: List[Dict[str, Any]] = []

    # ---------------------------------------------------------
    # 1. Google Vision
    # ---------------------------------------------------------
    try:
        vision_data = detect_web(image_path)
        vision_candidates = _vision_candidates(vision_data)

    except Exception as exc:
        print(f"Vision search failed: {exc}")

    # ---------------------------------------------------------
    # 2. Face-verify Vision candidates
    # ---------------------------------------------------------
    best = _select_best(image_path, vision_candidates)

    if best:
        return {
            "url": best["url"],
            "title": best.get("title", ""),
            "source": best.get("source", "vision"),
            "confidence": best.get("score", 0.0),
            "face_verified": True,
            "face_distance": best.get("face_distance"),
        }

    # ---------------------------------------------------------
    # 3. SerpApi / Google Lens fallback
    # ---------------------------------------------------------
    serp_candidates: List[Dict[str, Any]] = []

    try:
        serp_data = search_lens(image_path)
        serp_candidates = _serp_candidates(serp_data)

    except Exception as exc:
        print(f"SerpApi search failed: {exc}")

    # ---------------------------------------------------------
    # 4. Face-verify general web results
    # ---------------------------------------------------------
    best = _select_best(image_path, serp_candidates)

    if best:
        return {
            "url": best["url"],
            "title": best.get("title", ""),
            "source": best.get("source", "serpapi"),
            "confidence": best.get("score", 0.0),
            "face_verified": True,
            "face_distance": best.get("face_distance"),
        }

    # ---------------------------------------------------------
    # 5. No verified result
    # ---------------------------------------------------------
    return {
        "url": None,
        "title": None,
        "source": None,
        "confidence": 0.0,
        "face_verified": False,
        "face_distance": None,
    }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m search.search <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        sys.exit(1)

    result = search_web(image_path)

    print(json.dumps(result, indent=2))
