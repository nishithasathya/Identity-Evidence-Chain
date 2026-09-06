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
      "confidence": float
    }

The search is live. No social URL is hardcoded.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .filters import is_social_url, platform_for_url
from .serpapi_fallback import search_lens
from .vision_search import detect_web

SOCIAL_PLATFORMS = {"instagram", "twitter", "linkedin", "facebook"}


def _vision_candidates(data: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for item in data.get("pages", []):
        url = item.get("url")
        if not url or not is_social_url(url):
            continue
        match_type = item.get("match_type")
        confidence = {"full": 0.90, "partial": 0.75}.get(match_type, 0.65)
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


def _serp_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for item in items:
        url = item.get("url")
        platform = platform_for_url(url or "")
        if not url or platform not in SOCIAL_PLATFORMS:
            continue
        position = int(item.get("position", 0))
        confidence = max(0.55, 0.82 - min(position, 10) * 0.03)
        candidates.append(
            {
                "url": url,
                "image_url": item.get("image_url"),
                "caption": item.get("caption"),
                "author": item.get("author"),
                "timestamp": item.get("timestamp"),
                "confidence": round(confidence, 2),
                "source": "serpapi",
                "platform": platform,
            }
        )
    return candidates


def _select_best(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    # Prefer confidence, then richer metadata, then a stable platform order.
    platform_bonus = {"instagram": 0.03, "twitter": 0.02, "linkedin": 0.01, "facebook": 0.0}

    def key(item: dict[str, Any]) -> tuple[float, int]:
        richness = sum(bool(item.get(k)) for k in ("image_url", "caption", "author", "timestamp"))
        score = float(item.get("confidence", 0.0)) + platform_bonus.get(item.get("platform"), 0)
        return score, richness

    return max(candidates, key=key)


def search_web(p1_payload: dict[str, Any]) -> dict[str, Any]:
    """Search the supplied image and return the P2 → P3 evidence contract."""
    image_path = p1_payload.get("image_path")
    if not image_path:
        raise ValueError("P2 input must contain image_path")
    if not Path(image_path).is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    vision_error: str | None = None
    try:
        vision_data = detect_web(image_path)
        candidate = _select_best(_vision_candidates(vision_data))
        if candidate:
            return _output(candidate)
    except Exception as exc:  # noqa: BLE001 - fallback is intentional
        vision_error = str(exc)

    try:
        candidate = _select_best(_serp_candidates(search_lens(image_path)))
    except Exception as exc:  # noqa: BLE001 - surface a useful combined error
        if vision_error:
            raise RuntimeError(f"Vision search failed: {vision_error}; SerpApi fallback failed: {exc}") from exc
        raise

    if not candidate:
        raise LookupError("No supported social-media result found from Vision or SerpApi")
    return _output(candidate)


def _output(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "matched_url": candidate["url"],
        "platform": candidate["platform"],
        "image_url": candidate.get("image_url"),
        "caption": candidate.get("caption"),
        "author": candidate.get("author"),
        "timestamp": candidate.get("timestamp"),
        "confidence": round(float(candidate.get("confidence", 0.0)), 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="P2 live web/social evidence search")
    parser.add_argument("image", help="Path to the consenting demo image")
    args = parser.parse_args()

    payload = {"image_path": args.image, "face_encoding": []}
    result = search_web(payload)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
