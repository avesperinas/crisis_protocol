"""Evaluation prompt: parses + scores all actions of a single turn in one call.

Output is a strict JSON object. The parser in ai/parsing.py validates and falls
back to deterministic defaults on failure.

For each action submitted this turn, Claude must produce:
- action_type: one of the engine's ActionType values (or "generic" if unclear)
- target_id: the role_id of the target, or null
- coherence_score: 0.0..1.0 (how well do tokens back the directive?)
- decision_quality: 0..10 (against the role's rubric)
- decision_quality_reasoning: short string
"""

from src.ai.client import cacheable
from src.schemas.scenario import Scenario

# Action types must match src.engine.types.ActionType values.
_ALLOWED_ACTION_TYPES = [
    "military_offensive",
    "military_defensive",
    "diplomatic_proposal",
    "diplomatic_mediation",
    "economic_sanction",
    "economic_aid",
    "intel_espionage",
    "intel_counter",
    "info_expose",
    "pact_break",
    "generic",
]


SYSTEM_TEMPLATE = """Eres el sistema de evaluación de Crisis Protocol. Analizas las acciones de un turno y produces scores y clasificaciones que el engine usa para calcular efectos reales sobre los recursos.

ESCENARIO: {scenario_name}
CONTEXTO:
{scenario_context}

RUBRICS DE CALIDAD POR FACCIÓN:
{rubrics_block}

ACTION TYPES DISPONIBLES (elige siempre el más específico posible):
{action_types}

REGLAS DE CLASIFICACIÓN (crítico — el engine aplica efectos distintos según el tipo):
- "military_offensive": directiva que busca dañar recursos MIL del target. Requiere target_id.
- "military_defensive": directiva que busca proteger los propios recursos MIL.
- "diplomatic_proposal": oferta formal a otro actor. Requiere target_id.
- "diplomatic_mediation": intervención para reducir tensión entre terceros. Requiere target_id.
- "economic_sanction": presión económica contra otro actor. Requiere target_id.
- "economic_aid": transferencia de recursos ECO a otro actor. Requiere target_id.
- "intel_espionage": recopilación de información sobre otro actor. Requiere target_id.
- "intel_counter": defensa propia contra operaciones de inteligencia enemigas.
- "info_expose": revelación pública de información dañina sobre otro actor. Requiere target_id.
- "pact_break": ruptura unilateral de un pacto existente. Requiere target_id.
- "generic": SOLO si la directiva es genuinamente vaga y no encaja en ningún tipo anterior.

REGLA CLAVE: si la directiva menciona un actor concreto (macedonia, atenas, esparta, tebas, corinto, persia) como objeto de la acción, DEBES clasificarla en un tipo no-generic y poner ese actor en target_id. Usar "generic" con un target obvio es un error.

REGLAS DE SCORING:
1. coherence_score 0.0..1.0 — ¿los tokens invertidos respaldan la directiva?
   - 1.0: tokens perfectamente alineados (ej: DIP alto para propuesta diplomática)
   - 0.7: parcialmente alineados
   - 0.4: tokens insuficientes o mal distribuidos para la ambición declarada
   - 0.0: imposible con esos recursos

2. decision_quality 0..10 contra la rubric del rol. No premies "ganar", premia "decidir bien dado lo que sabía".

3. effective_multiplier 0.3..1.2 — multiplicador final que el engine aplica a los efectos:
   - 1.2: coherencia perfecta + postura alineada + decisión excelente
   - 1.0: baseline sin bonus ni penalización
   - 0.5: coherencia baja o postura contradictoria
   - 0.3: directiva incoherente o farol obvio

IMPORTANTE — BREVEDAD: "decision_quality_reasoning" es interno (no se muestra al usuario). Máximo una frase corta por acción. Evalúas varias facciones en la misma respuesta — no te extiendas en ninguna, o te quedarás sin espacio para las últimas.

DEVUELVE SOLO JSON. Sin texto fuera del JSON. Sin markdown ni code fences:

{{
  "evaluations": [
    {{
      "player_id": "...",
      "action_type": "diplomatic_proposal",
      "target_id": "atenas",
      "coherence_score": 0.85,
      "posture_modifier": 0.10,
      "decision_quality": 7.0,
      "decision_quality_reasoning": "...",
      "effective_multiplier": 1.05
    }}
  ]
}}"""


USER_TEMPLATE = """Turno {turn_number} de {max_turns}. Tensión global al inicio: {tension_start}.

PACTOS ACTIVOS:
{pacts_block}

EVENTOS / NOTAS PREVIAS:
{previous_events}

ACCIONES DE ESTE TURNO (player_id es el role_id de cada facción):

{actions_block}

Devuelve el JSON ahora."""


def render_evaluation(
    *,
    scenario: Scenario,
    turn_number: int,
    max_turns: int,
    tension_start: int,
    actions: list[dict],
    active_pacts: list[dict] | None = None,
    previous_events: str = "(ninguno)",
) -> tuple[list[dict], str]:
    """Return (system_blocks, user_message).

    `actions` is a list of dicts shaped:
        {"player_id": "macedonia", "posture": "confrontational",
         "tokens": {"MIL": 2, "DIP": 1, "ECO": 0, "INT": 1},
         "directive": "..."}

    `active_pacts` shape: [{"a": "...", "b": "...", "type": "alliance", "is_secret": false}]
    """
    rubrics = "\n\n".join(
        f"- {f.id} ({f.name}): {f.evaluation_rubric}" for f in scenario.factions
    )
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            scenario_name=scenario.name,
            scenario_context=scenario.context,
            rubrics_block=rubrics,
            action_types=", ".join(_ALLOWED_ACTION_TYPES),
        )
    )

    if active_pacts:
        pacts_block = "\n".join(
            f"- {p['a']} <-> {p['b']}: {p['type']}" + (" (secreto)" if p.get("is_secret") else "")
            for p in active_pacts
        )
    else:
        pacts_block = "(ninguno)"

    actions_block = "\n\n".join(
        f"{i + 1}. player_id: {a['player_id']}\n"
        f"   posture: {a['posture']}\n"
        f"   tokens: MIL={a['tokens']['MIL']} DIP={a['tokens']['DIP']} "
        f"ECO={a['tokens']['ECO']} INT={a['tokens']['INT']}\n"
        f"   directive: {a['directive']!r}"
        for i, a in enumerate(actions)
    )

    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        max_turns=max_turns,
        tension_start=tension_start,
        pacts_block=pacts_block,
        previous_events=previous_events,
        actions_block=actions_block,
    )
    return system, user
