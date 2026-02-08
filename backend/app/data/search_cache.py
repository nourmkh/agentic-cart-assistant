from typing import Any

_last_search: dict[str, Any] | None = None


def set_last_search(payload: dict[str, Any]) -> None:
    global _last_search
    _last_search = payload


def get_last_search() -> dict[str, Any] | None:
    return _last_search
