"""SerpApi Google Lens fallback for local images."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any


def _prepare_image(path: str) -> tuple[str, bool]:
    """Return a path suitable for SerpApi image upload and whether it is temporary."""
    source = Path(path)
    if source.stat().st_size <= 500_000:
        return str(source), False

    from PIL import Image

    image = Image.open(source).convert("RGB")
    fd, temp_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    quality = 85
    image.save(temp_path, format="JPEG", quality=quality, optimize=True)
    while Path(temp_path).stat().st_size > 500_000 and quality > 35:
        quality -= 10
        image.save(temp_path, format="JPEG", quality=quality, optimize=True)
    return temp_path, True


def search_lens(image_path: str) -> list[dict[str, Any]]:
    import serpapi

    api_key = os.getenv("SERPAPI_KEY") or os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY is not configured")

    client = serpapi.Client(api_key=api_key)
    upload_path, temporary = _prepare_image(image_path)
    try:
        upload = client.upload_image(upload_path)
        image_id = upload.get("image_id")
        if not image_id:
            raise RuntimeError("SerpApi image upload did not return image_id")

        results = client.search({"engine": "google_lens", "image_id": image_id})
        return _extract_candidates(results)
    finally:
        if temporary:
            try:
                Path(upload_path).unlink(missing_ok=True)
            except OSError:
                pass


def _extract_candidates(results: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    # Google Lens can expose visual_matches and knowledge_graph/related content;
    # visual_matches are the most useful source for reverse-image evidence.
    for index, item in enumerate(results.get("visual_matches", []) or []):
        url = item.get("link") or item.get("source")
        if not url:
            continue
        candidates.append(
            {
                "url": url,
                "image_url": item.get("thumbnail") or item.get("image"),
                "title": item.get("title"),
                "author": item.get("source"),
                "timestamp": item.get("date"),
                "caption": item.get("snippet") or item.get("title"),
                "source": "serpapi",
                "position": index,
            }
        )

    return candidates
