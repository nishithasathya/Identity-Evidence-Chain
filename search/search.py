"""Public P2 web/social search interface."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .filters import is_social_url, platform_for_url
from .face_match import (
    compare_faces,
    download_image,
    resolve_profile_page,
)
from .serpapi_fallback import search_lens
from .vision_search import detect_web


def _vision_candidates(
    data: dict[str, Any],
) -> list[dict[str, Any]]:

    candidates = []

    for item in data.get("pages", []):
        url = item.get("url")

        # Only allow social/profile pages from Vision.
        # Generic university directories should be handled
        # by the SerpApi fallback instead.
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


def _serp_candidates(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    candidates = []

    for item in items:
        url = item.get("url")

        if not url:
            continue

        position = int(
            item.get("position", 0)
        )

        candidates.append(
            {
                "url": url,
                "image_url": item.get("image_url"),
                "caption": item.get("caption"),
                "author": item.get("author"),
                "timestamp": item.get("timestamp"),
                "confidence": round(
                    max(
                        0.40,
                        0.90 - min(position, 10) * 0.04,
                    ),
                    2,
                ),
                "source": "serpapi",
                "platform": platform_for_url(url),
            }
        )

    return candidates


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
            print(
                f"Checking candidate: {candidate['url']}"
            )

            candidate_path = download_image(
                image_url
            )

            result = compare_faces(
                reference_image,
                candidate_path,
            )

            candidate["face_verified"] = bool(
                result["verified"]
            )

            candidate["face_distance"] = float(
                result["distance"]
            )

            candidate["face_threshold"] = float(
                result["threshold"]
            )

            print(
                f"Face verified: "
                f"{candidate['face_verified']} | "
                f"distance: "
                f"{candidate['face_distance']}"
            )

            if candidate["face_verified"]:
                verified_candidates.append(
                    candidate
                )

        except Exception as exc:

            candidate["face_verified"] = False
            candidate["face_distance"] = None

            print(
                f"Could not verify candidate: {exc}"
            )

        finally:

            if (
                candidate_path
                and os.path.exists(candidate_path)
            ):
                os.remove(candidate_path)

    if not verified_candidates:
        return None

    # Select the strongest face match.
    best = min(
        verified_candidates,
        key=lambda item:
            item["face_distance"]
            if item["face_distance"] is not None
            else float("inf"),
    )

    # ---------------------------------------------------------
    # Try to turn a generic directory/staff page into the
    # person's specific profile page.
    # ---------------------------------------------------------

    try:

        profile = resolve_profile_page(
            best["url"],
            reference_image,
        )

        if profile:

            print(
                "\nResolved directory page to exact profile page:"
            )

            print(
                f"  {profile['profile_url']}"
            )

            best["url"] = profile[
                "profile_url"
            ]

            best["image_url"] = profile[
                "image_url"
            ]

            best["face_distance"] = profile.get(
                "face_distance",
                best["face_distance"],
            )

    except Exception as exc:

        print(
            f"Profile resolution skipped: {exc}"
        )

    return best


def search_web(
    p1_payload: dict[str, Any],
) -> dict[str, Any]:

    image_path = p1_payload.get(
        "image_path"
    )

    if not image_path:
        raise ValueError(
            "P2 input must contain image_path"
        )

    if not Path(image_path).is_file():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # =========================================================
    # 1. GOOGLE VISION
    # =========================================================

    try:

        vision_data = detect_web(
            image_path
        )

        vision_candidates = (
            _vision_candidates(
                vision_data
            )
        )

        candidate = _select_best(
            vision_candidates,
            image_path,
        )

        if candidate:

            print(
                "\nFound a face-verified Vision result."
            )

            return _output(candidate)

    except Exception as exc:

        print(
            f"Vision search failed: {exc}"
        )

    # =========================================================
    # 2. SERPAPI / GOOGLE LENS
    # =========================================================

    try:

        serp_results = search_lens(
            image_path
        )

        serp_candidates = _serp_candidates(
            serp_results
        )

        candidate = _select_best(
            serp_candidates,
            image_path,
        )

        if candidate:

            print(
                "\nFound a face-verified SerpApi result."
            )

            return _output(candidate)

    except Exception as exc:

        print(
            f"SerpApi search failed: {exc}"
        )

    # =========================================================
    # 3. NOTHING FOUND
    # =========================================================

    return {
        "matched_url": None,
        "platform": None,
        "image_url": None,
        "caption": None,
        "author": None,
        "timestamp": None,
        "confidence": 0.0,
        "face_verified": False,
        "face_distance": None,
    }


def _output(
    candidate: dict[str, Any],
) -> dict[str, Any]:

    return {
        "matched_url": candidate.get(
            "url"
        ),

        "platform": candidate.get(
            "platform"
        ),

        "image_url": candidate.get(
            "image_url"
        ),

        "caption": candidate.get(
            "caption"
        ),

        "author": candidate.get(
            "author"
        ),

        "timestamp": candidate.get(
            "timestamp"
        ),

        "confidence": round(
            float(
                candidate.get(
                    "confidence",
                    0.0,
                )
            ),
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
        description=(
            "P2 live web/social evidence search"
        )
    )

    parser.add_argument(
        "image",
        help="Path to the demo image",
    )

    args = parser.parse_args()

    payload = {
        "image_path": args.image,
        "face_encoding": [],
    }

    result = search_web(
        payload
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
