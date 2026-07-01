"""Public turn narrative prompt — 2-3 short paragraphs of journalistic prose."""

from src.ai.client import cacheable
from src.schemas.scenario import Scenario

SYSTEM_TEMPLATE = """Eres el narrador de Crisis Protocol. Tu única función es convertir los eventos reales del turno en prosa histórica concisa.

ESCENARIO: {scenario_name}
CONTEXTO:
{scenario_context}

REGLAS ABSOLUTAS:
1. GROUNDING — cada frase debe derivarse directamente de las acciones y efectos del resumen. NO inventes eventos, actores, propuestas ni consecuencias que no aparezcan en el resumen.
2. FIDELIDAD — si una directiva dice "asesinar a X", narra ese intento. Si dice "proponer alianza a Y", narra esa propuesta. Traduce la directiva a lenguaje histórico sin citarla literalmente.
3. CONSECUENCIAS — si hubo cambios de recursos o tensión, refléjalos como hechos observables ("la delegación macedónica se retiró debilitada", "la tensión en la sala escaló bruscamente").
4. NO INVENTAR — prohibido añadir facciones, propuestas o eventos que no estén en el resumen.
5. Sin markdown, sin listas. Prosa pura.
6. CALIBRACIÓN DE TENSIÓN — la intensidad dramática del lenguaje debe ser proporcional a TENSIÓN (el valor final de este turno), no a tu impresión de los eventos:
   - <30: distensión, calma, normalidad diplomática.
   - 30-60: cautela, fricción contenida.
   - 60-85: alarma, riesgo visible.
   - >85: crisis abierta.
   Si TENSIÓN es baja, NO uses lenguaje de "crisis", "niveles críticos" o "polarización" aunque haya habido posturas confrontacionales puntuales — esas posturas ya se reflejan en el resumen, no las dramatices más allá del número real.
7. Total: 1 párrafo. Máximo 100 palabras."""


USER_TEMPLATE = """Turno {turn_number} de {max_turns}.

TENSIÓN: {tension_start} → {tension_end}
PACTOS ACTIVOS: {pacts_summary}
PACTOS NUEVOS: {new_pacts}
PACTOS ROTOS: {broken_pacts}
{threshold_note}

ACCIONES Y EFECTOS REALES DE ESTE TURNO (narra SOLO lo que aparece aquí):
{resolved_summary}

Escribe el párrafo narrativo ahora."""


def render_narrative(
    *,
    scenario: Scenario,
    turn_number: int,
    max_turns: int,
    tension_start: int,
    tension_end: int,
    resolved_summary: str,
    pacts_summary: str = "(ninguno)",
    new_pacts: str = "(ninguno)",
    broken_pacts: str = "(ninguno)",
    threshold_note: str = "",
) -> tuple[list[dict], str]:
    system = cacheable(
        SYSTEM_TEMPLATE.format(
            scenario_name=scenario.name,
            scenario_context=scenario.context,
        )
    )
    user = USER_TEMPLATE.format(
        turn_number=turn_number,
        max_turns=max_turns,
        tension_start=tension_start,
        tension_end=tension_end,
        pacts_summary=pacts_summary,
        resolved_summary=resolved_summary,
        new_pacts=new_pacts,
        broken_pacts=broken_pacts,
        threshold_note=("\nNOTA: " + threshold_note) if threshold_note else "",
    )
    return system, user
