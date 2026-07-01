"""Localization helpers for scenario static content.

Scenario definitions carry every user-facing string in both supported
languages. A string is marked localized with `L(es, en)`, which produces a
plain ``{"es": ..., "en": ...}`` dict. `resolve_localized` then walks a raw
scenario dict and collapses each of those leaves down to a single language,
yielding a flat structure that validates against the `Scenario` schema.

Non-localized data (ids, numbers, resource maps, etc.) is left untouched.
"""

from typing import Any

SUPPORTED_LANGUAGES: tuple[str, ...] = ("es", "en")
DEFAULT_LANGUAGE = "es"


def L(es: str, en: str) -> dict[str, str]:
    """Marks a user-facing string as localized. See module docstring."""
    return {"es": es, "en": en}


def _is_localized_leaf(node: dict) -> bool:
    return set(node.keys()) == {"es", "en"} and all(
        isinstance(v, str) for v in node.values()
    )


def normalize_language(language: str | None) -> str:
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def resolve_localized(node: Any, language: str) -> Any:
    """Recursively replaces every `L(...)` leaf with its `language` variant."""
    if isinstance(node, dict):
        if _is_localized_leaf(node):
            return node[language]
        return {key: resolve_localized(value, language) for key, value in node.items()}
    if isinstance(node, list):
        return [resolve_localized(item, language) for item in node]
    return node
