"""Bot pact response prompt: should this bot accept or reject an incoming pact proposal?"""

from src.ai.client import cacheable
from src.schemas.scenario import Faction, Scenario

SYSTEM_TEMPLATE = """Eres {role_name} ({role_tagline}) en Crisis Protocol, escenario "{scenario_name}". Acabas de recibir una propuesta de pacto y debes decidir si aceptas.

CONTEXTO DEL ESCENARIO:
{scenario_context}

TU BRIEFING:
{briefing}

RUBRIC INTERNA (informa tu decisión, no la cites):
{rubric}

TIPOS DE PACTO Y EFECTOS:
- alliance: +15% efectividad en acciones contra targets comunes
- non_aggression: -30% daño en agresiones mutuas
- trade: intercambio de recursos cada turno
- intel_share: informes de inteligencia más detallados

REGLAS:
- Acepta solo si el pacto sirve a tus objetivos. Considera que los pactos quedan registrados públicamente.
- Si tu objetivo oculto se vería comprometido o expuesto, rechaza.
- Si el proponente es rival natural y el pacto te debilita estratégicamente, rechaza.
- Si el pacto refuerza tu posición sin coste obvio, acepta.

DEVUELVE ÚNICAMENTE JSON. Sin texto fuera, sin code fences.

{{
  "accept": true,
  "reason": "..."
}}

"reason" debe ser una sola frase corta (máximo 20 palabras). No te extiendas."""

USER_TEMPLATE = """Propuesta recibida en el turno {turn_number} de {max_turns}.

Quien propone: {proposer_name} ({proposer_id})
Tipo de pacto: {pact_type}
Pacto secreto: {is_secret}
Términos: {terms}

Estado actual del juego:
- Tensión global: {tension}/100
- Tus recursos: MIL {mil} · DIP {dip} · ECO {eco} · INT {int_}
- Pactos activos: {pacts_summary}

¿Aceptas? Responde con el JSON ahora."""


def render_pact_response(
    *,
    scenario: Scenario,
    faction: Faction,
    briefing: str,
    proposer_role_id: str,
    proposer_name: str,
    pact_type: str,
    is_secret: bool,
    terms_text: str,
    turn_number: int,
    max_turns: int,
    tension: int,
    resources: dict[str, int],
    pacts_summary: str,
) -> tuple[list[dict], str]:
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            role_name=faction.name,
            role_tagline=faction.tagline,
            scenario_name=scenario.name,
            scenario_context=scenario.context,
            briefing=briefing,
            rubric=faction.evaluation_rubric,
        )
    )
    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        max_turns=max_turns,
        proposer_id=proposer_role_id,
        proposer_name=proposer_name,
        pact_type=pact_type,
        is_secret="sí" if is_secret else "no",
        terms=terms_text,
        tension=tension,
        mil=resources.get("MIL", 0),
        dip=resources.get("DIP", 0),
        eco=resources.get("ECO", 0),
        int_=resources.get("INT", 0),
        pacts_summary=pacts_summary,
    )
    return system, user
