from src.schemas.scenario import Scenario
from src.scenarios.arctic import ARCTIC_SCENARIO
from src.scenarios.corinth import CORINTH_SCENARIO
from src.scenarios.oil_crisis import OIL_CRISIS_SCENARIO

_RAW_SCENARIOS: dict[str, dict] = {
    CORINTH_SCENARIO["id"]: CORINTH_SCENARIO,
    OIL_CRISIS_SCENARIO["id"]: OIL_CRISIS_SCENARIO,
    ARCTIC_SCENARIO["id"]: ARCTIC_SCENARIO,
}

# Validate on import. Misconfigured scenarios should crash the app at startup,
# never silently produce broken games at runtime.
SCENARIOS: dict[str, Scenario] = {
    scenario_id: Scenario.model_validate(data) for scenario_id, data in _RAW_SCENARIOS.items()
}


def get_scenario(scenario_id: str) -> Scenario:
    if scenario_id not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {scenario_id!r}")
    return SCENARIOS[scenario_id]


def list_scenarios() -> list[Scenario]:
    return list(SCENARIOS.values())


__all__ = ["SCENARIOS", "Scenario", "get_scenario", "list_scenarios"]
