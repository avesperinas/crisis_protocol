"""Shared helpers for prompt rendering.

The game is localized per-game: every AI-generated, player-facing text must be
written in the game's language so the experience stays immersive. Prompt
instructions themselves are in English; the output language is enforced with an
explicit directive built here.
"""

_LANGUAGE_NAMES = {"es": "Spanish", "en": "English"}


def language_name(language: str) -> str:
    return _LANGUAGE_NAMES.get(language, "Spanish")


def output_language_instruction(language: str) -> str:
    """A directive forcing the model's player-facing output into `language`."""
    return (
        f"OUTPUT LANGUAGE: write your entire response in {language_name(language)}. "
        f"This is mandatory — the text is shown to a player and must stay immersive."
    )
