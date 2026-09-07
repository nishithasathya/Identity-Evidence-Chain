"""Web/social evidence discovery module."""


def search_web(*args, **kwargs):
    from .search import search_web as _search_web

    return _search_web(*args, **kwargs)


__all__ = ["search_web"]
