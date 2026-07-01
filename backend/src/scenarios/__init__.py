from src.schemas.scenario import Scenario
from src.scenarios.arctic import ARCTIC_SCENARIO
from src.scenarios.corinth import CORINTH_SCENARIO
from src.scenarios.localize import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    normalize_language,
    resolve_localized,
)
from src.scenarios.oil_crisis import OIL_CRISIS_SCENARIO

_RAW_SCENARIOS: dict[str, dict] = {
    CORINTH_SCENARIO["id"]: CORINTH_SCENARIO,
    OIL_CRISIS_SCENARIO["id"]: OIL_CRISIS_SCENARIO,
    ARCTIC_SCENARIO["id"]: ARCTIC_SCENARIO,
}

# Resolve + validate every scenario in every supported language on import. A
# misconfigured scenario (bad structure, missing translation) should crash the
# app at startup, never silently produce broken games at runtime.
_SCENARIOS: dict[str, dict[str, Scenario]] = {
    language: {
        scenario_id: Scenario.model_validate(resolve_localized(data, language))
        for scenario_id, data in _RAW_SCENARIOS.items()
    }
    for language in SUPPORTED_LANGUAGES
}


def get_scenario(scenario_id: str, language: str = DEFAULT_LANGUAGE) -> Scenario:
    by_id = _SCENARIOS[normalize_language(language)]
    if scenario_id not in by_id:
        raise KeyError(f"Unknown scenario: {scenario_id!r}")
    return by_id[scenario_id]


def list_scenarios(language: str = DEFAULT_LANGUAGE) -> list[Scenario]:
    return list(_SCENARIOS[normalize_language(language)].values())


__all__ = [
    "SUPPORTED_LANGUAGES",
    "Scenario",
    "get_scenario",
    "list_scenarios",
    "normalize_language",
]
