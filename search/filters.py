"""URL/domain normalization and social-platform filtering."""

from __future__ import annotations

from urllib.parse import urlparse

SOCIAL_DOMAINS = {
    "instagram": ("instagram.com", "www.instagram.com"),
    "twitter": ("twitter.com", "www.twitter.com", "x.com", "www.x.com"),
    "linkedin": ("linkedin.com", "www.linkedin.com"),
    "facebook": ("facebook.com", "www.facebook.com", "m.facebook.com", "fb.com", "www.fb.com"),
}


def _hostname(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
        return host.lower().removeprefix("www.")
    except ValueError:
        return ""


def platform_for_url(url: str) -> str | None:
    host = _hostname(url)
    if host in {"instagram.com"}:
        return "instagram"
    if host in {"twitter.com", "x.com"}:
        return "twitter"
    if host in {"linkedin.com"} or host.endswith(".linkedin.com"):
        return "linkedin"
    if host in {"facebook.com", "m.facebook.com", "fb.com"}:
        return "facebook"
    return None


def is_social_url(url: str) -> bool:
    return platform_for_url(url) is not None
