"""Face verification and generic webpage/profile resolution."""

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

    base_host = base_host.removeprefix("www.")
    candidate_host = candidate_host.removeprefix("www.")

    return base_host == candidate_host


def _image_url_from_tag(
    img,
    page_url: str,
) -> str | None:
    """Extract the best available image URL from an image tag."""

    attributes = [
        "src",
        "data-src",
        "data-lazy-src",
        "data-original",
        "data-image",
        "data-original-src",
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
        entries = [
            item.strip()
            for item in srcset.split(",")
            if item.strip()
        ]

        if entries:
            image_url = entries[-1].split(" ")[0]

            return urljoin(
                page_url,
                image_url,
            )

    return None


def _meta_image_urls(
    soup: BeautifulSoup,
    page_url: str,
) -> list[str]:
    """Extract OpenGraph/Twitter preview images."""

    urls = []

    for attribute, value in [
        ("property", "og:image"),
        ("property", "og:image:url"),
        ("name", "twitter:image"),
        ("name", "twitter:image:src"),
    ]:
        tag = soup.find(
            "meta",
            attrs={attribute: value},
        )

        if not tag:
            continue

        content = tag.get("content")

        if not content:
            continue

        urls.append(
            urljoin(
                page_url,
                content,
            )
        )

    return urls


def _collect_page_images(
    soup: BeautifulSoup,
    page_url: str,
) -> list[str]:
    """Collect all useful image URLs from a webpage."""

    urls = []

    urls.extend(
        _meta_image_urls(
            soup,
            page_url,
        )
    )

    for img in soup.find_all("img"):
        image_url = _image_url_from_tag(
            img,
            page_url,
        )

        if image_url:
            urls.append(image_url)

    unique = []
    seen = set()

    for url in urls:
        if url in seen:
            continue

        seen.add(url)
        unique.append(url)

    return unique


def _link_score(
    href: str,
    text: str,
    title: str,
) -> int:
    """
    Rank links that look like individual profile pages.

    This is intentionally generic and does not depend on
    a specific university or social-media website.
    """

    value = (
        f"{href} {text} {title}"
    ).lower()

    score = 0

    profile_terms = [
        "/in/",
        "/profile/",
        "/people/",
        "/person/",
        "/faculty/",
        "/staff/",
        "/member/",
        "/members/",
        "/author/",
        "/authors/",
        "/team/",
        "/employee/",
        "/employees/",
        "profile",
        "faculty",
        "staff",
        "people",
        "member",
        "author",
        "employee",
    ]

    for term in profile_terms:
        if term in value:
            score += 3

    bad_terms = [
        "/search",
        "/login",
        "/signup",
        "/register",
        "/privacy",
        "/terms",
        "/about",
        "/contact",
        "/category/",
        "/tag/",
        "/events/",
        "/news/",
    ]

    for term in bad_terms:
        if term in value:
            score -= 4

    if text.strip():
        score += 1

    if title.strip():
        score += 1

    return score


def _candidate_links_near_image(
    img,
    page_url: str,
) -> list[dict]:
    """
    Find links associated with an image.

    Many websites do not put the image directly inside
    the <a> tag. We therefore inspect several ancestors.
    """

    links = []

    current = img

    for _ in range(7):
        if current is None:
            break

        for link in current.find_all(
            "a",
            href=True,
        ):
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

            if profile_url == page_url:
                continue

            text = link.get_text(
                " ",
                strip=True,
            )

            title = (
                link.get("title")
                or ""
            ).strip()

            links.append(
                {
                    "profile_url": profile_url,
                    "text": text,
                    "title": title,
                    "score": _link_score(
                        profile_url,
                        text,
                        title,
                    ),
                }
            )

        current = current.parent

    return links


def _verify_image(
    reference_image: str,
    image_url: str,
) -> dict | None:
    """Download and face-verify one image."""

    image_path = None

    try:
        image_path = download_image(
            image_url
        )

        result = compare_faces(
            reference_image,
            image_path,
        )

        if not result["verified"]:
            return None

        return {
            "face_distance": result[
                "distance"
            ],
            "face_threshold": result[
                "threshold"
            ],
        }

    except Exception:
        return None

    finally:
        if (
            image_path
            and os.path.exists(image_path)
        ):
            os.remove(image_path)


def resolve_profile_page(
    page_url: str,
    reference_image: str,
) -> dict | None:
    """
    Resolve a general search-result page to the most
    specific page associated with the matching face.

    Handles:
    - direct profile pages
    - directory pages
    - staff/faculty pages
    - LinkedIn/social pages
    - news/article pages
    - personal websites
    - lazy-loaded images
    - OpenGraph/Twitter images
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

    # --------------------------------------------------
    # 1. Check the page's own preview/profile images.
    # --------------------------------------------------

    page_images = _collect_page_images(
        soup,
        page_url,
    )

    print(
        f"Checking {len(page_images)} images on result page."
    )

    page_matches = []

    for image_url in page_images:
        result = _verify_image(
            reference_image,
            image_url,
        )

        if result:
            page_matches.append(
                {
                    "profile_url": page_url,
                    "image_url": image_url,
                    **result,
                }
            )

            print(
                "  Matching image found on page:"
            )
            print(
                f"    {page_url}"
            )

    # If the actual result page is itself a matching
    # profile page, prefer it immediately.
    if page_matches:
        return min(
            page_matches,
            key=lambda item: item[
                "face_distance"
            ],
        )

    # --------------------------------------------------
    # 2. Check images and links throughout the page.
    # --------------------------------------------------

    candidates = []

    for img in soup.find_all("img"):
        image_url = _image_url_from_tag(
            img,
            page_url,
        )

        if not image_url:
            continue

        links = _candidate_links_near_image(
            img,
            page_url,
        )

        for link in links:
            candidates.append(
                {
                    "image_url": image_url,
                    "profile_url": link[
                        "profile_url"
                    ],
                    "score": link[
                        "score"
                    ],
                }
            )

    # Remove duplicate image/profile combinations.
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
        f"Found {len(candidates)} linked image candidates."
    )

    matches = []

    for candidate in candidates:
        result = _verify_image(
            reference_image,
            candidate["image_url"],
        )

        if not result:
            continue

        matches.append(
            {
                **candidate,
                **result,
            }
        )

        print(
            "  Matching linked image found:"
        )
        print(
            f"    {candidate['profile_url']}"
        )

    if not matches:
        return None

    # Face similarity is the primary criterion.
    # Link structure is only used as a small tie-breaker.
    return min(
        matches,
        key=lambda item: (
            item["face_distance"],
            -item["score"],
        ),
    )
