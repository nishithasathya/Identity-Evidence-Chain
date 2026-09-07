"""Public P2 web/social search interface.

Input:
    {"image_path": str, "face_encoding": [...]}

Output:
    {
      "matched_url": str,
      "platform": str,
      "image_url": str | None,
      "caption": str | None,
      "author": str | None,
      "timestamp": str | None,
      "confidence": float,
      "face_verified": bool,
      "face_distance": float | None
    }

The search is live. No social URL is hardcoded.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .filters import is_social_url, platform_for_url
from .face_match import compare_faces, download_image
from .serpapi_fallback import search_lens


    candidates = []

    for item in data.get("pages", []):
        url = item.get("url")

        if not url or not is_social_url(url):
            continue

        match_type = item.get("match_type")

        confidence = {
            "full": 0.90,
            "partial": 0.75,
        }.get(match_type, 0.65)

        candidates.append(
            {
                "url": url,
                "image_url": item.get("image_url"),
                "caption": None,
                "author": None,
                "timestamp": None,
                "confidence": confidence,
                "source": "vision",
                "platform": platform_for_url(url),
            }
        )

    return candidates

        candidates.extend(
            vision_candidates
        )

def _serp_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []

    for item in items:
        url = item.get("url")

        if not url:
            continue

        position = int(item.get("position", 0))

        candidates.append(
            {
                "url": url,
                "image_url": item.get("image_url"),
                "caption": item.get("caption"),
                "author": item.get("author"),
                "timestamp": item.get("timestamp"),
                "confidence": round(
                    max(0.40, 0.90 - min(position, 10) * 0.04),
                    2,
                ),
                "source": "serpapi",
                "platform": platform_for_url(url),
            }
        )

    return candidates

    # SerpApi provides the main Google Lens fallback.
    if not candidates:
        try:
            candidates = search_lens(
                image_path
            )

        except Exception as exc:
            print(
                f"SerpApi search failed: {exc}"
            )

def _select_best(
    candidates: list[dict[str, Any]],
    reference_image: str,
) -> dict[str, Any] | None:

    if not candidates:
        return None

    verified_candidates = []

    for candidate in candidates:
        image_url = candidate.get("image_url")

        if not image_url:
            continue

        candidate_path = None

        try:
            print(f"Checking candidate: {candidate['url']}")

            candidate_path = download_image(image_url)

            face_result = compare_faces(
                reference_image,
                candidate_path,
            )

            candidate["face_verified"] = face_result["verified"]
            candidate["face_distance"] = face_result["distance"]
            candidate["face_threshold"] = face_result["threshold"]

            print(
                f"Face verified: {candidate['face_verified']} | "
                f"distance: {candidate['face_distance']}"
            )

            if face_result["verified"]:
                verified_candidates.append(candidate)

        except Exception as exc:
            candidate["face_verified"] = False
            candidate["face_distance"] = None
            print(f"Could not verify candidate: {exc}")

        finally:
            if candidate_path and os.path.exists(candidate_path):
                os.remove(candidate_path)

    if not verified_candidates:
        return None

    # FaceNet distance:
    # lower distance = more similar face.
    return min(
        verified_candidates,
        key=lambda item: item["face_distance"]
        if item["face_distance"] is not None
        else float("inf"),
    )

    if not candidates:
        return {
            "success": False,
            "message": "No allowed public web candidates found.",
            "candidates": [],
        }

def search_web(p1_payload: dict[str, Any]) -> dict[str, Any]:
    """Search the supplied image and return verified web evidence."""

    image_path = p1_payload.get("image_path")

    if not image_path:
        raise ValueError("P2 input must contain image_path")

    if not Path(image_path).is_file():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    vision_error: str | None = None

    # ---------------------------------------------------------
    # 1. Try Google Cloud Vision
    # ---------------------------------------------------------

    try:
        vision_data = detect_web(image_path)

        candidate = _select_best(
            _vision_candidates(vision_data),
            image_path,
        )

        if candidate:
            return _output(candidate)

    except Exception as exc:
        vision_error = str(exc)

    # ---------------------------------------------------------
    # 2. Fall back to SerpApi / Google Lens
    # ---------------------------------------------------------

    try:
        serp_results = search_lens(image_path)

        candidate = _select_best(
            _serp_candidates(serp_results),
            image_path,
        )

    except Exception as exc:

        if vision_error:
            raise RuntimeError(
                f"Vision search failed: {vision_error}; "
                f"SerpApi fallback failed: {exc}"
            ) from exc

        raise

    # ---------------------------------------------------------
    # 3. No face-verified result
    # ---------------------------------------------------------

    if not candidate:
        raise LookupError(
            "No face-verified result found from Vision or SerpApi"
        )

    return _output(candidate)

    return result


def _build_result(
    best: dict,
    profile: dict | None,
    verified: list[dict],
) -> dict:
    """Build a stable result object for downstream evidence storage."""

    original_url = best.get(
        "url"
    )

    matched_url = original_url

    if profile:
        matched_url = profile.get(
            "profile_url",
            original_url,
        )

    return {
        "matched_url": candidate["url"],
        "platform": candidate.get("platform"),
        "image_url": candidate.get("image_url"),
        "caption": candidate.get("caption"),
        "author": candidate.get("author"),
        "timestamp": candidate.get("timestamp"),
        "confidence": round(
            float(candidate.get("confidence", 0.0)),
            2,
        ),
        "face_verified": candidate.get(
            "face_verified",
            False,
        ),
        "face_distance": candidate.get(
            "face_distance"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="P2 live web/social evidence search"
    )

    parser.add_argument(
        "image",
        help="Path to the consenting demo image",
    )

    args = parser.parse_args()

    payload = {
        "image_path": args.image,
        "face_encoding": [],
    }

    result = search_web(payload)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    print(
        "Use main.py to run the complete "
        "Identity-Evidence-Chain pipeline."
    )
