from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.db import Base
from src.models import Game, GameStatus, Player
from src.scenarios import get_scenario


async def test_init_db_creates_all_tables(engine: AsyncEngine) -> None:
    expected = {"games", "players", "turns", "actions", "pacts", "messages"}
    assert expected.issubset(set(Base.metadata.tables.keys()))


async def test_create_game_with_four_players(session: AsyncSession) -> None:
    scenario = get_scenario("corinth_338")
    selected_role_ids = ["macedonia", "atenas", "tebas", "corinto"]

    game = Game(scenario_id=scenario.id, max_turns=scenario.max_turns)
    session.add(game)
    await session.flush()

    factions_by_id = {f.id: f for f in scenario.factions}
    for role_id in selected_role_ids:
        faction = factions_by_id[role_id]
        res = faction.starting_resources
        player = Player(
            game_id=game.id,
            role_id=role_id,
            is_ai=True,
            resources={"MIL": res.MIL, "DIP": res.DIP, "ECO": res.ECO, "INT": res.INT},
        )
        session.add(player)
    await session.commit()

    result = await session.execute(select(Player).where(Player.game_id == game.id))
    players = list(result.scalars())
    assert len(players) == 4
    assert {p.role_id for p in players} == set(selected_role_ids)

    atenas = next(p for p in players if p.role_id == "atenas")
    assert atenas.resources == {"MIL": 8, "DIP": 14, "ECO": 14, "INT": 12}
    assert atenas.is_ai is True
    assert atenas.public_objective_status == "pending"
    assert atenas.hidden_objective_status == "pending"


async def test_game_defaults(session: AsyncSession) -> None:
    game = Game(scenario_id="corinth_338", max_turns=4)
    session.add(game)
    await session.commit()
    await session.refresh(game)

    assert game.status == GameStatus.LOBBY.value
    assert game.current_turn == 0
    assert game.tension == 50
    assert game.id  # uuid default applied
    assert game.created_at is not None
