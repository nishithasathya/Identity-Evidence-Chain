"""Face verification and webpage profile resolution."""

from __future__ import annotations

import os
import tempfile
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from deepface import DeepFace


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 20


def compare_faces(
    reference_image: str,
    candidate_image: str,
) -> dict:
    """Compare two images using FaceNet."""

    result = DeepFace.verify(
        img1_path=reference_image,
        img2_path=candidate_image,
        model_name="Facenet",
        detector_backend="mtcnn",
        enforce_detection=True,
    )

    return {
        "verified": bool(result["verified"]),
        "distance": float(result["distance"]),
        "threshold": float(result["threshold"]),
    }


def download_image(url: str) -> str:
    """Download a web image to a temporary local file."""

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers=HEADERS,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "content-type",
        "",
    ).lower()

    if "image" not in content_type:
        raise ValueError(
            f"URL did not return an image: {content_type}"
        )

    suffix = ".jpg"

    if "png" in content_type:
        suffix = ".png"
    elif "webp" in content_type:
        suffix = ".webp"

    fd, path = tempfile.mkstemp(
        suffix=suffix
    )

    os.close(fd)

    with open(path, "wb") as file:
        file.write(response.content)

    return path


def _same_domain(
    base_url: str,
    candidate_url: str,
) -> bool:
    """Check whether two URLs belong to the same domain."""

    base_host = (
        urlparse(base_url).hostname
        or ""
    ).lower()

    candidate_host = (
        urlparse(candidate_url).hostname
        or ""
    ).lower()

    base_host = base_host.removeprefix(
        "www."
    )

    candidate_host = candidate_host.removeprefix(
        "www."
    )

    return (
        base_host == candidate_host
    )


def _image_url_from_tag(
    img,
    page_url: str,
) -> str | None:
    """Extract the best available image URL."""

    attributes = [
        "src",
        "data-src",
        "data-lazy-src",
        "data-original",
        "data-image",
    ]

    for attribute in attributes:
        value = img.get(attribute)

        if value:
            return urljoin(
                page_url,
                value,
            )

    srcset = img.get("srcset")

    if srcset:
        first = srcset.split(",")[0].strip()

        if first:
            image_url = first.split(" ")[0]

            return urljoin(
                page_url,
                image_url,
            )

    return None


def resolve_profile_page(
    page_url: str,
    reference_image: str,
) -> dict | None:
    """
    Inspect a result page and identify a more-specific
    linked page whose image matches the reference face.

    This is deliberately generic: it does not assume the
    website is a university, staff directory, or social site.
    """

    try:
        response = requests.get(
            page_url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS,
        )

        response.raise_for_status()

    except Exception as exc:
        print(
            f"Could not open result page: {exc}"
        )

        return None

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    candidates = []

    for img in soup.find_all("img"):
        image_url = _image_url_from_tag(
            img,
            page_url,
        )

        if not image_url:
            continue

        # Find the nearest clickable ancestor.
        link = img.find_parent("a")

        if not link:
            parent = img.parent

            if parent:
                link = parent.find("a")

        if not link:
            continue

        href = link.get("href")

        if not href:
            continue

        profile_url = urljoin(
            page_url,
            href,
        )

        parsed = urlparse(
            profile_url
        )

        if parsed.scheme not in (
            "http",
            "https",
        ):
            continue

        if not _same_domain(
            page_url,
            profile_url,
        ):
            continue

        # Ignore links that clearly aren't useful
        # profile/content destinations.
        if profile_url == page_url:
            continue

        alt = (
            img.get("alt")
            or ""
        ).strip()

        title = (
            link.get("title")
            or ""
        ).strip()

        candidates.append(
            {
                "image_url": image_url,
                "profile_url": profile_url,
                "alt": alt,
                "title": title,
            }
        )

    # Remove duplicate image/profile pairs.
    unique = []
    seen = set()

    for candidate in candidates:
        key = (
            candidate["image_url"],
            candidate["profile_url"],
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(candidate)

    candidates = unique

    print(
        f"Found {len(candidates)} linked images "
        f"on result page."
    )

    matches = []

    for candidate in candidates:
        image_path = None

        try:
            image_path = download_image(
                candidate["image_url"]
            )

            result = compare_faces(
                reference_image,
                image_path,
            )

            if result["verified"]:
                matches.append(
                    {
                        **candidate,
                        "face_distance": result[
                            "distance"
                        ],
                        "face_threshold": result[
                            "threshold"
                        ],
                    }
                )

                print(
                    "  Matching linked image found:"
                )
                print(
                    f"    {candidate['profile_url']}"
                )

        except Exception:
            # A webpage can contain many images that aren't
            # faces or aren't downloadable. Skip those.
            pass

        finally:
            if (
                image_path
                and os.path.exists(image_path)
            ):
                os.remove(image_path)

    if not matches:
        return None

    # Lowest FaceNet distance = strongest verified match.
    return min(
        matches,
        key=lambda item: item["face_distance"],
    )
