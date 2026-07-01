"""Briefing prompt: per-player private intro at game start.

Stable part (scenario context) goes in `system` as a cacheable block;
the variable part (this player's role + resources + objectives) is the
user message.
"""

from src.ai.client import cacheable
from src.schemas.scenario import Faction, Scenario

SYSTEM_TEMPLATE = """Eres un diseñador de juegos que escribe el briefing privado para un jugador en una partida de Crisis Protocol.

ESCENARIO: {scenario_name} ({scenario_year})
TIPO: {scenario_type}

CONTEXTO HISTÓRICO:
{scenario_context}

REGLAS DE TONO:
- Serio, evocador, sin clichés épicos.
- Prosa narrativa, no listas con bullets dentro del texto.
- Habla en segunda persona al jugador.
- No reveles objetivos ocultos de otras facciones.
- No menciones mecánicas (tokens, multiplicadores, etc.).

ESTRUCTURA OBLIGATORIA (en este orden, con estos encabezados de markdown):
## La Situación
## Tu Posición
## Lo que Sabes
## Lo que Debes Lograr

Máximo total: 250 palabras."""


USER_TEMPLATE = """Genera el briefing del jugador con esta información:

ROL: {faction_name} — {faction_tagline}
DESCRIPCIÓN DEL ROL:
{faction_description}

RECURSOS INICIALES:
- Militar (MIL): {mil}
- Diplomático (DIP): {dip}
- Económico (ECO): {eco}
- Inteligencia (INT): {int_}

OBJETIVO PÚBLICO (visible para todos):
{public_objective}

OBJETIVO OCULTO (solo para este jugador, narrarlo sin revelarlo de forma literal):
{hidden_objective}

CONSIDERACIONES ESTRATÉGICAS DEL ROL (rubric interno; informa el tono, no se cita literalmente):
{rubric}

Escribe el briefing ahora."""


def render_briefing(scenario: Scenario, faction: Faction) -> tuple[list[dict], str]:
    """Returns (system_blocks, user_message) ready for ClaudeClient.call()."""
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            scenario_name=scenario.name,
            scenario_year=scenario.year,
            scenario_type=scenario.type,
            scenario_context=scenario.context,
        )
    )
    user = USER_TEMPLATE.format(
        faction_name=faction.name,
        faction_tagline=faction.tagline,
        faction_description=faction.description,
        mil=faction.starting_resources.MIL,
        dip=faction.starting_resources.DIP,
        eco=faction.starting_resources.ECO,
        int_=faction.starting_resources.INT,
        public_objective=faction.public_objective.text,
        hidden_objective=faction.hidden_objective.text,
        rubric=faction.evaluation_rubric,
    )
    return system, user
