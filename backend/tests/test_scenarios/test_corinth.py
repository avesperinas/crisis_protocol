import pytest

from src.scenarios import get_scenario
from src.schemas.scenario import Scenario


def test_corinth_loads_and_validates() -> None:
    scenario = get_scenario("corinth_338")
    assert isinstance(scenario, Scenario)
    assert scenario.id == "corinth_338"
    assert scenario.type == "diplomatic"
    assert scenario.max_turns == 4


def test_corinth_has_six_factions() -> None:
    scenario = get_scenario("corinth_338")
    faction_ids = {f.id for f in scenario.factions}
    assert faction_ids == {"macedonia", "atenas", "esparta", "tebas", "corinto", "persia"}


@pytest.mark.parametrize(
    "role_id,expected",
    [
        ("macedonia", {"MIL": 18, "DIP": 12, "ECO": 12, "INT": 8}),
        ("atenas", {"MIL": 8, "DIP": 14, "ECO": 14, "INT": 12}),
        ("esparta", {"MIL": 16, "DIP": 6, "ECO": 8, "INT": 8}),
        ("tebas", {"MIL": 10, "DIP": 10, "ECO": 8, "INT": 10}),
        ("corinto", {"MIL": 6, "DIP": 12, "ECO": 16, "INT": 10}),
        ("persia", {"MIL": 4, "DIP": 12, "ECO": 18, "INT": 18}),
    ],
)
def test_corinth_starting_resources(role_id: str, expected: dict[str, int]) -> None:
    scenario = get_scenario("corinth_338")
    faction = next(f for f in scenario.factions if f.id == role_id)
    res = faction.starting_resources
    assert {"MIL": res.MIL, "DIP": res.DIP, "ECO": res.ECO, "INT": res.INT} == expected


def test_corinth_token_budgets_in_range() -> None:
    scenario = get_scenario("corinth_338")
    for f in scenario.factions:
        assert 3 <= f.token_budget_per_turn <= 6, f"{f.id} has out-of-range budget"


def test_corinth_every_faction_has_complete_objectives() -> None:
    scenario = get_scenario("corinth_338")
    for f in scenario.factions:
        assert f.public_objective.text
        assert f.public_objective.evaluation_criteria
        assert f.hidden_objective.text
        assert f.hidden_objective.evaluation_criteria
        assert f.evaluation_rubric
        assert f.description


def test_corinth_has_crisis_cards_and_events() -> None:
    scenario = get_scenario("corinth_338")
    assert len(scenario.crisis_cards) >= 3
    assert len(scenario.event_pool) >= 6
    crisis_ids = {c.id for c in scenario.crisis_cards}
    event_ids = {e.id for e in scenario.event_pool}
    assert len(crisis_ids) == len(scenario.crisis_cards), "duplicate crisis card ids"
    assert len(event_ids) == len(scenario.event_pool), "duplicate event ids"


def test_unknown_scenario_raises() -> None:
    with pytest.raises(KeyError):
        get_scenario("nonexistent")
