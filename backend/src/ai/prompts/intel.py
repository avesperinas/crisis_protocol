"""Private intel report prompt — one per player per turn.

The accuracy of the report scales with the player's current INT pool:
- INT >= 12: detailed and accurate
- INT 6..11: 1 accurate fact + 1-2 rumors
- INT < 6: vague, mostly speculation
"""

from src.ai.client import cacheable
from src.schemas.scenario import Scenario

SYSTEM_TEMPLATE = """Eres el servicio de inteligencia privado de una facción en Crisis Protocol. Generas cables internos ultra-breves.

ESCENARIO: {scenario_name}
CONTEXTO:
{scenario_context}

REGLAS:
- Primera persona, tono de cable diplomático interno.
- Sin markdown, sin bullets — prosa.
- Total: 3-4 frases. Máximo 60 palabras.

CALIBRACIÓN SEGÚN INT:
- INT >= 12: 1-2 datos concretos y fiables sobre otros jugadores.
- INT 6..11: 1 dato concreto + 1 rumor sin confirmar.
- INT < 6: todo especulativo, sin nombres concretos."""


USER_TEMPLATE = """Genera el informe para esta facción tras el turno {turn_number}.

JUGADOR: {role_name} (INT actual: {int_level})

ESTADO PÚBLICO DEL TURNO RECIÉN RESUELTO:
{public_summary}

LO QUE TÚ HICISTE:
{own_action}

INFORMACIÓN PRIVADA DISPONIBLE PARA TI (úsala según tu nivel de INT):
{private_observations}

Escribe el cable ahora."""


def render_intel(
    *,
    scenario: Scenario,
    turn_number: int,
    role_name: str,
    int_level: int,
    public_summary: str,
    own_action: str,
    private_observations: str = "(sin datos privados nuevos)",
) -> tuple[list[dict], str]:
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            scenario_name=scenario.name,
            scenario_context=scenario.context,
        )
    )
    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        role_name=role_name,
        int_level=int_level,
        public_summary=public_summary,
        own_action=own_action,
        private_observations=private_observations,
    )
    return system, user
