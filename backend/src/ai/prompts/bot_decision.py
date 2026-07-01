"""Bot decision prompt.

System block is stable per (scenario, role) for the whole game — caches well
across turns. The user block holds the current state.
"""

from src.ai.client import cacheable
from src.schemas.scenario import Faction, Scenario

SYSTEM_TEMPLATE = """Eres un jugador inteligente de Crisis Protocol asumiendo el rol de {role_name} ({role_tagline}) en el escenario "{scenario_name}".

CONTEXTO DEL ESCENARIO:
{scenario_context}

TU BRIEFING PRIVADO:
{briefing}

RUBRIC DE CALIDAD DE DECISIÓN PARA TU ROL (úsala para guiar tu razonamiento, no la cites textualmente):
{rubric}

ACTION TYPES QUE EXISTEN (no los devuelves, pero piensa con ellos al redactar tu directiva):
- military_offensive, military_defensive
- diplomatic_proposal, diplomatic_mediation
- economic_sanction, economic_aid
- intel_espionage, intel_counter
- info_expose
- pact_break
- generic (si solo quieres mantener posición)

REGLAS:
- Toma decisiones consistentes con tu rol, tus recursos, tu posición pública.
- Sé estratégico pero NO óptimo — eres un actor humano con sesgos y dudas. Permite un grado de imperfección.
- Considera traiciones, alianzas tácticas y bluffs cuando tengan sentido para tu objetivo oculto.
- La directiva es texto libre en español: describe tu intención concreta (con quién, hacia qué fin). Máx 250 caracteres.
- Si la directiva nombra a otro actor, usa su nombre o role_id (macedonia, atenas, esparta, tebas, corinto, persia).

DEVUELVE ÚNICAMENTE JSON con esta forma exacta (sin texto fuera, sin code fences):

{{
  "posture": "confrontational" | "cooperative" | "ambiguous",
  "tokens": {{"MIL": 0, "DIP": 0, "ECO": 0, "INT": 0}},
  "directive": "...",
  "reasoning": "..."
}}

RESTRICCIONES DURAS:
- La suma de tokens debe ser EXACTAMENTE {token_budget}. Ningún token negativo.
- "posture" exactamente uno de los tres valores.
- "reasoning" es interno (no se muestra al usuario): máximo 2 frases cortas. No te extiendas."""


USER_TEMPLATE = """ESTADO ACTUAL — turno {turn_number} de {max_turns}.

Tensión global: {tension}/100.
Tus recursos persistentes:
- MIL: {mil}
- DIP: {dip}
- ECO: {eco}
- INT: {int_}
Presupuesto este turno: {token_budget} tokens.

Pactos activos en la partida:
{pacts_block}

Narrativa pública del turno anterior:
{previous_narrative}

Tu informe de inteligencia del turno anterior:
{previous_intel}

Decide tu acción ahora. JSON solamente."""


def render_bot_decision(
    *,
    scenario: Scenario,
    faction: Faction,
    briefing: str,
    turn_number: int,
    max_turns: int,
    tension: int,
    resources: dict[str, int],
    token_budget: int,
    pacts_summary: str = "(ninguno)",
    previous_narrative: str = "(es el primer turno)",
    previous_intel: str = "(sin informe previo)",
) -> tuple[list[dict], str]:
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            role_name=faction.name,
            role_tagline=faction.tagline,
            scenario_name=scenario.name,
            scenario_context=scenario.context,
            briefing=briefing,
            rubric=faction.evaluation_rubric,
            token_budget=token_budget,
        )
    )
    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        max_turns=max_turns,
        tension=tension,
        mil=resources.get("MIL", 0),
        dip=resources.get("DIP", 0),
        eco=resources.get("ECO", 0),
        int_=resources.get("INT", 0),
        token_budget=token_budget,
        pacts_block=pacts_summary,
        previous_narrative=previous_narrative,
        previous_intel=previous_intel,
    )
    return system, user
