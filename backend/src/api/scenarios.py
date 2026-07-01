"""Scenario lookups for the lobby."""

from fastapi import APIRouter

from src.scenarios import list_scenarios

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("")
async def list_all() -> list[dict]:
    """Returns scenario summaries — enough for the lobby's role picker."""
    return [
        {
            "id": s.id,
            "name": s.name,
            "year": s.year,
            "type": s.type,
            "max_turns": s.max_turns,
            "example_directive": s.example_directive,
            "pact_type_labels": s.pact_type_labels.model_dump(),
            "factions": [
                {
                    "id": f.id,
                    "name": f.name,
                    "tagline": f.tagline,
                    "description": f.description,
                    "starting_resources": {
                        "MIL": f.starting_resources.MIL,
                        "DIP": f.starting_resources.DIP,
                        "ECO": f.starting_resources.ECO,
                        "INT": f.starting_resources.INT,
                    },
                    "token_budget_per_turn": f.token_budget_per_turn,
                }
                for f in s.factions
            ],
        }
        for s in list_scenarios()
    ]
