"""Public web evidence search and face-based candidate verification."""

from __future__ import annotations

from typing import Any

from .face_match import (
    compare_faces,
    download_image,
    resolve_profile_page,
)
from .filters import is_allowed_url
from .serpapi_fallback import search_lens


def search_web(
    image_path: str,
    face_encoding: Any = None,
) -> dict:
    """
    Search the public web for visually similar results.

    Face verification is performed against downloaded candidate
    images. Search-result ranking is never treated as identity
    confidence.
    """

    candidates = []

    # Google Vision is optional. If it is unavailable, billing is
    # disabled, or credentials are missing, SerpApi remains usable.
    try:
        vision_candidates = _vision_candidates(
            image_path
        )

        candidates.extend(
            vision_candidates
        )

    except Exception as exc:
        print(
            f"Google Vision search unavailable: {exc}"
        )

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

    if not candidates:
        return {
            "success": False,
            "message": "No public web candidates found.",
            "candidates": [],
        }

    # Remove duplicates while preserving order.
    candidates = _deduplicate(
        candidates
    )

    # Keep public web pages, including non-social pages.
    candidates = [
        candidate
        for candidate in candidates
        if is_allowed_url(
            candidate.get("url", "")
        )
    ]

    if not candidates:
        return {
            "success": False,
            "message": "No allowed public web candidates found.",
            "candidates": [],
        }

    verified = []

    for candidate in candidates:
        image_url = candidate.get(
            "image_url"
        )

        if not image_url:
            continue

        print(
            "\nChecking candidate:"
        )
        print(
            f"  {candidate.get('url')}"
        )

        image_path_candidate = None

        try:
            image_path_candidate = download_image(
                image_url
            )

            match = compare_faces(
                image_path,
                image_path_candidate,
            )

            candidate = {
                **candidate,
                "face_verified": match[
                    "verified"
                ],
                "face_distance": match[
                    "distance"
                ],
                "face_threshold": match[
                    "threshold"
                ],
            }

            print(
                f"  Face verified: "
                f"{match['verified']}"
            )

            print(
                f"  Face distance: "
                f"{match['distance']:.4f}"
            )

            print(
                f"  Face threshold: "
                f"{match['threshold']:.4f}"
            )

            if match["verified"]:
                verified.append(
                    candidate
                )

        except Exception as exc:
            print(
                f"  Face comparison failed: {exc}"
            )

        finally:
            if (
                image_path_candidate
                and _file_exists(
                    image_path_candidate
                )
            ):
                _remove_file(
                    image_path_candidate
                )

    if not verified:
        return {
            "success": True,
            "message": (
                "Public web results were found, "
                "but no candidate image passed face verification."
            ),
            "candidates": _annotate_unverified(
                candidates
            ),
        }

    # The smallest FaceNet distance is the strongest
    # verified visual match.
    best = min(
        verified,
        key=lambda item: item.get(
            "face_distance",
            float("inf"),
        ),
    )

    # Try to turn a generic result page into a more-specific
    # page when the matching image is linked from that page.
    profile = None

    try:
        profile = resolve_profile_page(
            best["url"],
            image_path,
        )

    except Exception as exc:
        print(
            f"Profile-page resolution failed: {exc}"
        )

    result = _build_result(
        best,
        profile,
        verified,
    )

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
        "success": True,
        "matched_url": matched_url,
        "original_matched_url": original_url,
        "profile_url": (
            profile.get("profile_url")
            if profile
            else None
        ),
        "title": best.get(
            "title"
        ),
        "caption": best.get(
            "caption"
        ),
        "author": best.get(
            "author"
        ),
        "timestamp": best.get(
            "timestamp"
        ),
        "face_verified": best.get(
            "face_verified",
            False,
        ),
        "face_distance": best.get(
            "face_distance"
        ),
        "face_threshold": best.get(
            "face_threshold"
        ),
        # Kept for compatibility with the existing
        # evidence/blockchain pipeline. This is NOT
        # identity certainty.
        "confidence": _search_confidence(
            best
        ),
        "search_confidence": _search_confidence(
            best
        ),
        "verified_candidates": len(
            verified
        ),
        "source": best.get(
            "source"
        ),
        "candidate": best,
    }


def _search_confidence(
    candidate: dict,
) -> float:
    """
    Estimate search-result strength.

    This value describes the search result, NOT the probability
    that the person is the subject.
    """

    position = candidate.get(
        "position"
    )

    if isinstance(
        position,
        int,
    ):
        return round(
            max(
                0.0,
                1.0
                - (
                    position
                    / 20.0
                ),
            ),
            3,
        )

    return 0.0


def _annotate_unverified(
    candidates: list[dict],
) -> list[dict]:
    """Return candidates with explicit face-verification status."""

    annotated = []

    for candidate in candidates:
        annotated.append(
            {
                **candidate,
                "face_verified": False,
                "face_distance": None,
                "face_threshold": None,
            }
        )

    return annotated


def _deduplicate(
    candidates: list[dict],
) -> list[dict]:
    """Remove duplicate URLs."""

    output = []
    seen = set()

    for candidate in candidates:
        url = candidate.get(
            "url"
        )

        if not url or url in seen:
            continue

        seen.add(url)
        output.append(
            candidate
        )

    return output


def _vision_candidates(
    image_path: str,
) -> list[dict]:
    """
    Query Google Cloud Vision Web Detection.

    This function is intentionally isolated so the rest of the
    pipeline continues working when Vision billing is unavailable.
    """

    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    with open(
        image_path,
        "rb",
    ) as image_file:
        content = image_file.read()

    image = vision.Image(
        content=content
    )

    response = client.web_detection(
        image=image
    )

    if response.error.message:
        raise RuntimeError(
            response.error.message
        )

    detection = (
        response.web_detection
    )

    candidates = []

    for position, page in enumerate(
        detection.pages_with_matching_images
    ):
        url = page.url

        if not url:
            continue

        candidates.append(
            {
                "url": url,
                "image_url": getattr(
                    page,
                    "full_matching_images",
                    [None],
                )[0].url
                if getattr(
                    page,
                    "full_matching_images",
                    None,
                )
                else None,
                "title": None,
                "caption": None,
                "author": None,
                "timestamp": None,
                "position": position,
                "source": "google_vision",
            }
        )

    return candidates


def _file_exists(
    path: str,
) -> bool:
    import os

    return os.path.exists(
        path
    )


def _remove_file(
    path: str,
) -> None:
    import os

    try:
        os.remove(
            path
        )
    except OSError:
        pass


if __name__ == "__main__":
    print(
        "Use main.py to run the complete "
        "Identity-Evidence-Chain pipeline."
    )
