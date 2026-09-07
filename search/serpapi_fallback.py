"""SerpApi Google Lens search for local images."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image


MAX_UPLOAD_SIZE = 500_000


def _prepare_image(path: str) -> tuple[str, bool]:
    """Prepare an image that satisfies SerpApi's upload limit."""

    source = Path(path)

    if source.stat().st_size <= MAX_UPLOAD_SIZE:
        return str(source), False

    image = Image.open(source).convert("RGB")

    fd, temp_path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)

    quality = 85

    while quality >= 30:
        image.save(
            temp_path,
            format="JPEG",
            quality=quality,
            optimize=True,
        )

        if Path(temp_path).stat().st_size <= MAX_UPLOAD_SIZE:
            break

        quality -= 10

    if Path(temp_path).stat().st_size > MAX_UPLOAD_SIZE:
        Path(temp_path).unlink(missing_ok=True)

        raise RuntimeError(
            "Could not compress image below SerpApi's 500 KB limit"
        )

    return temp_path, True


def search_lens(image_path: str) -> list[dict[str, Any]]:
    """Upload the reference image and query Google Lens."""

    import serpapi

    api_key = (
        os.getenv("SERPAPI_KEY")
        or os.getenv("API_KEY")
    )

    if not api_key:
        raise RuntimeError(
            "SERPAPI_KEY is not configured"
        )

    client = serpapi.Client(
        api_key=api_key
    )

    upload_path, temporary = _prepare_image(
        image_path
    )

    try:
        upload = client.upload_image(
            upload_path
        )

        image_id = upload.get(
            "image_id"
        )

        if not image_id:
            raise RuntimeError(
                "SerpApi image upload did not return image_id"
            )

        results = client.search(
            {
                "engine": "google_lens",
                "image_id": image_id,
            }
        )

        return _extract_candidates(
            results
        )

    finally:
        if temporary:
            Path(upload_path).unlink(
                missing_ok=True
            )


def _extract_candidates(
    results: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Convert Google Lens visual matches into
    normalized candidates.
    """

    candidates = []

    visual_matches = (
        results.get("visual_matches")
        or []
    )

    for position, item in enumerate(
        visual_matches
    ):
        page_url = (
            item.get("link")
            or item.get("source")
        )

        if not page_url:
            continue

        image_url = (
            item.get("thumbnail")
            or item.get("image")
        )

        candidates.append(
            {
                "url": page_url,
                "image_url": image_url,
                "title": item.get(
                    "title"
                ),
                "caption": (
                    item.get("snippet")
                    or item.get("title")
                ),
                "author": item.get(
                    "source"
                ),
                "timestamp": item.get(
                    "date"
                ),
                "position": position,
                "source": "serpapi",
            }
        )

    return candidates
