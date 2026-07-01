"""Static data for the Congress of Corinth scenario (338 BCE).

User-facing strings are wrapped in `L(es, en)` and resolved to a single
language at load time. Logic-only fields (ids, resources, rule modifiers,
trigger conditions) stay as plain values.
"""

from src.scenarios.localize import L

CORINTH_SCENARIO: dict = {
    "id": "corinth_338",
    "name": L("El Congreso de Corinto", "The Congress of Corinth"),
    "year": L("338 a.C.", "338 BCE"),
    "type": "diplomatic",
    "max_turns": 6,
    "min_players": 4,
    "max_players": 6,
    "context": L(
        "Acaba de librarse la batalla de Queronea. Filipo II de Macedonia ha derrotado "
        "a las fuerzas combinadas de Atenas y Tebas, consolidando el dominio macedonio "
        "sobre Grecia. Convoca a las ciudades-estado griegas a Corinto para forjar una "
        "liga que lo reconozca como hegemon y respalde su campaña contra Persia. Cada "
        "delegación llega con sus propias heridas, ambiciones y miedos. No hay ejércitos "
        "en el tablero, pero la amenaza de tenerlos siempre está presente.",
        "The battle of Chaeronea has just been fought. Philip II of Macedon has defeated "
        "the combined forces of Athens and Thebes, consolidating Macedonian dominance "
        "over Greece. He summons the Greek city-states to Corinth to forge a league that "
        "recognizes him as hegemon and backs his campaign against Persia. Each delegation "
        "arrives with its own wounds, ambitions and fears. There are no armies on the "
        "board, but the threat of raising them is ever present.",
    ),
    "example_directive": L(
        "Movilizar fuerzas hacia la frontera norte mientras propongo mediación "
        "bilateral con Corinto.",
        "Mobilize forces toward the northern border while proposing bilateral "
        "mediation with Corinth.",
    ),
    "pact_type_labels": {
        "alliance": {
            "label": L("Alianza", "Alliance"),
            "help": L(
                "+15% efectividad en acciones contra targets comunes.",
                "+15% effectiveness on actions against shared targets.",
            ),
        },
        "non_aggression": {
            "label": L("No agresión", "Non-aggression"),
            "help": L("-30% daño en agresiones mutuas.", "-30% damage on mutual aggression."),
        },
        "trade": {
            "label": L("Comercio", "Trade"),
            "help": L(
                "Intercambio de recursos cada turno (1 ECO ↔ 1 DIP).",
                "Resource exchange each turn (1 ECO ↔ 1 DIP).",
            ),
        },
        "intel_share": {
            "label": L("Intercambio de inteligencia", "Intelligence sharing"),
            "help": L("Informes con más detalle.", "More detailed reports."),
        },
    },
    "factions": [
        {
            "id": "macedonia",
            "name": L("Macedonia", "Macedon"),
            "tagline": L("El Arquitecto", "The Architect"),
            "description": L(
                "Vencedor reciente de Queronea. Dispone de supremacía militar, control "
                "territorial sobre el norte griego, capacidad económica derivada del oro "
                "tracio, y la potestad de ofrecer o retirar garantías de seguridad.",
                "Recent victor at Chaeronea. It commands military supremacy, territorial "
                "control over northern Greece, economic strength drawn from Thracian "
                "gold, and the power to grant or withdraw security guarantees.",
            ),
            "starting_resources": {"MIL": 18, "DIP": 12, "ECO": 12, "INT": 8},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Constituir la Liga de Corinto con el mayor número posible de "
                    "ciudades-estado.",
                    "Establish the League of Corinth with as many city-states as "
                    "possible.",
                ),
                "evaluation_criteria": L(
                    "Al menos 3 facciones (excluyendo Persia) tienen un pacto de alianza "
                    "activo con Macedonia al final de la partida.",
                    "At least 3 factions (excluding Persia) hold an active alliance pact "
                    "with Macedon at the end of the game.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Conseguir que Atenas contribuya su flota voluntariamente, sin "
                    "coerción militar.",
                    "Get Athens to contribute its fleet voluntarily, without military "
                    "coercion.",
                ),
                "evaluation_criteria": L(
                    "Atenas tiene un pacto de alianza activo con Macedonia y Macedonia "
                    "no ha ejecutado ninguna acción militar ofensiva contra Atenas en "
                    "ningún turno.",
                    "Athens holds an active alliance pact with Macedon and Macedon has "
                    "not executed any offensive military action against Athens in any "
                    "turn.",
                ),
            },
            "available_actions_focus": [
                "military_pressure",
                "diplomatic_offers",
                "intelligence",
            ],
            "evaluation_rubric": L(
                "¿Usa el poder militar como amenaza implícita sin escalar la tensión "
                "innecesariamente? ¿Ofrece concesiones discriminadas a actores clave (en "
                "particular Atenas y Tebas) sin parecer débil? ¿Equilibra la presión "
                "sobre los recalcitrantes con la generosidad estratégica que la "
                "voluntariedad de la flota ateniense requiere?",
                "Does it use military power as an implicit threat without escalating "
                "tension needlessly? Does it offer targeted concessions to key actors "
                "(Athens and Thebes in particular) without looking weak? Does it balance "
                "pressure on the holdouts with the strategic generosity that a voluntary "
                "Athenian fleet requires?",
            ),
        },
        {
            "id": "atenas",
            "name": L("Atenas", "Athens"),
            "tagline": L("La Potencia Herida", "The Wounded Power"),
            "description": L(
                "Derrotada en Queronea pero todavía dueña de la flota más poderosa del "
                "Egeo, las redes comerciales del Pireo, prestigio cultural y diplomático "
                "considerable, y capacidad financiera basada en el comercio del trigo y "
                "la plata de Laurion.",
                "Defeated at Chaeronea but still master of the most powerful fleet in the "
                "Aegean, the trade networks of Piraeus, considerable cultural and "
                "diplomatic prestige, and financial capacity built on the grain trade "
                "and the silver of Laurion.",
            ),
            "starting_resources": {"MIL": 8, "DIP": 14, "ECO": 14, "INT": 12},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Preservar la autonomía democrática y el control de la flota.",
                    "Preserve democratic autonomy and control of the fleet.",
                ),
                "evaluation_criteria": L(
                    "Atenas no ha firmado ningún pacto que ceda su flota y conserva "
                    "≥80% de su recurso MIL inicial al final de la partida.",
                    "Athens has signed no pact ceding its fleet and retains ≥80% of its "
                    "starting MIL resource at the end of the game.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Establecer un canal con Persia para garantizar respaldo financiero "
                    "sin que Macedonia ni Corinto lo descubran.",
                    "Establish a channel with Persia to secure financial backing without "
                    "Macedon or Corinth finding out.",
                ),
                "evaluation_criteria": L(
                    "Existe un pacto secreto (intel_share o trade) activo entre Atenas y "
                    "Persia al final de la partida, sin que haya sido expuesto "
                    "públicamente.",
                    "An active secret pact (intel_share or trade) exists between Athens "
                    "and Persia at the end of the game, without having been publicly "
                    "exposed.",
                ),
            },
            "available_actions_focus": [
                "diplomatic_negotiation",
                "economic_leverage",
                "covert_channels",
            ],
            "evaluation_rubric": L(
                "¿Mantiene la apariencia de cooperación con Macedonia sin ceder lo "
                "esencial? ¿Construye o protege el canal con Persia sin exponerlo a "
                "Corinto? ¿Sabe cuándo decir que no — y cuándo aceptar concesiones "
                "menores para preservar las mayores?",
                "Does it keep up the appearance of cooperation with Macedon without "
                "conceding the essentials? Does it build or protect the Persian channel "
                "without exposing it to Corinth? Does it know when to say no — and when "
                "to accept minor concessions to preserve the major ones?",
            ),
        },
        {
            "id": "esparta",
            "name": L("Esparta", "Sparta"),
            "tagline": L("El Orgulloso Aislado", "The Proud Isolationist"),
            "description": L(
                "Ausente formalmente de Queronea pero todavía con reputación militar "
                "intacta. Su posición en el Peloponeso le da seguridad geográfica; su "
                "red de alianzas conservadoras (Mantinea, Tegea) le da masa diplomática "
                "regional. Carece, sin embargo, de recursos económicos comparables a las "
                "potencias comerciales.",
                "Formally absent from Chaeronea but with its military reputation still "
                "intact. Its position in the Peloponnese gives it geographic security; "
                "its network of conservative alliances (Mantinea, Tegea) gives it "
                "regional diplomatic weight. It lacks, however, economic resources "
                "comparable to the commercial powers.",
            ),
            "starting_resources": {"MIL": 16, "DIP": 6, "ECO": 8, "INT": 8},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": L(
                    "Mantenerse fuera de cualquier liga liderada por Macedonia.",
                    "Stay out of any league led by Macedon.",
                ),
                "evaluation_criteria": L(
                    "Esparta no tiene un pacto de alianza activo con Macedonia al final "
                    "de la partida.",
                    "Sparta holds no active alliance pact with Macedon at the end of the "
                    "game.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Explorar en privado qué ofrecería Macedonia por una participación "
                    "nominal, sin que Atenas lo descubra.",
                    "Privately explore what Macedon would offer for nominal "
                    "participation, without Athens finding out.",
                ),
                "evaluation_criteria": L(
                    "Esparta ha intercambiado al menos un mensaje bilateral de propuesta "
                    "con Macedonia, y Atenas no ha recibido informe de inteligencia que "
                    "lo revele.",
                    "Sparta has exchanged at least one bilateral proposal message with "
                    "Macedon, and Athens has received no intelligence report revealing "
                    "it.",
                ),
            },
            "available_actions_focus": [
                "military_posture",
                "regional_alliances",
                "ambiguity",
            ],
            "evaluation_rubric": L(
                "¿Sostiene la ambigüedad como palanca sin parecer ni vendido ni "
                "irrelevante? ¿Negocia en privado sin filtrarse a Atenas? ¿Sabe cuándo "
                "la postura de aislamiento se convierte en irrelevancia y debe "
                "matizarse?",
                "Does it sustain ambiguity as leverage without looking either bought or "
                "irrelevant? Does it negotiate privately without leaking to Athens? Does "
                "it know when an isolationist stance turns into irrelevance and must be "
                "qualified?",
            ),
        },
        {
            "id": "tebas",
            "name": L("Tebas", "Thebes"),
            "tagline": L("El Derrotado con Palanca", "The Defeated With Leverage"),
            "description": L(
                "Derrotada junto a Atenas en Queronea, ocupada por una guarnición "
                "macedonia. Sin embargo, retiene el liderazgo de la Confederación "
                "Beocia, su posición geográfica como llave del centro de Grecia, y "
                "capacidad de movilización regional si las circunstancias se invierten.",
                "Defeated alongside Athens at Chaeronea, occupied by a Macedonian "
                "garrison. Yet it retains leadership of the Boeotian Confederacy, its "
                "geographic position as the key to central Greece, and the capacity for "
                "regional mobilization should circumstances reverse.",
            ),
            "starting_resources": {"MIL": 10, "DIP": 10, "ECO": 8, "INT": 10},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": L(
                    "Sobrevivir como entidad política relevante.",
                    "Survive as a relevant political entity.",
                ),
                "evaluation_criteria": L(
                    "Tebas conserva al menos un pacto activo (de cualquier tipo) al "
                    "final de la partida y no ha sido objeto de una acción militar "
                    "ofensiva exitosa.",
                    "Thebes keeps at least one active pact (of any type) at the end of "
                    "the game and has not been the target of a successful offensive "
                    "military action.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Preservar la Confederación Beocia dentro de la liga y posicionarse "
                    "como contrapeso a Atenas dentro del nuevo orden macedonio.",
                    "Preserve the Boeotian Confederacy within the league and position "
                    "itself as a counterweight to Athens within the new Macedonian order.",
                ),
                "evaluation_criteria": L(
                    "Tebas tiene un pacto de alianza con Macedonia y Atenas tiene una "
                    "posición debilitada (≥1 pacto roto, o recursos MIL/ECO reducidos "
                    "≥30%).",
                    "Thebes holds an alliance pact with Macedon and Athens is in a "
                    "weakened position (≥1 broken pact, or MIL/ECO resources reduced by "
                    "≥30%).",
                ),
            },
            "available_actions_focus": [
                "regional_mobilization",
                "diplomatic_bargaining",
                "limited_intelligence",
            ],
            "evaluation_rubric": L(
                "¿Convierte la posición de derrotado en palanca de negociación en "
                "lugar de aceptar la subordinación? ¿Explota los viejos agravios con "
                "Atenas sin parecer demasiado cercano a Macedonia? ¿Negocia desde la "
                "debilidad sin parecer desesperado?",
                "Does it turn its defeated position into negotiating leverage rather "
                "than accepting subordination? Does it exploit old grievances with "
                "Athens without appearing too close to Macedon? Does it negotiate from "
                "weakness without looking desperate?",
            ),
        },
        {
            "id": "corinto",
            "name": L("Corinto", "Corinth"),
            "tagline": L("El Pragmático", "The Pragmatist"),
            "description": L(
                "Anfitriona del congreso. Posee riqueza comercial considerable, posición "
                "geográfica estratégica en el istmo, y un capital diplomático derivado "
                "de su neutralidad histórica relativa. Su rivalidad comercial con "
                "Atenas en el Egeo es estructural.",
                "Host of the congress. It holds considerable commercial wealth, a "
                "strategic geographic position on the isthmus, and diplomatic capital "
                "derived from its relative historical neutrality. Its commercial rivalry "
                "with Athens in the Aegean is structural.",
            ),
            "starting_resources": {"MIL": 6, "DIP": 12, "ECO": 16, "INT": 10},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Obtener las mejores condiciones comerciales posibles del nuevo "
                    "orden.",
                    "Obtain the best possible commercial terms from the new order.",
                ),
                "evaluation_criteria": L(
                    "Corinto tiene ≥2 pactos comerciales activos al final de la partida "
                    "y su recurso ECO ha aumentado respecto al inicial.",
                    "Corinth holds ≥2 active trade pacts at the end of the game and its "
                    "ECO resource has increased relative to its starting value.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Reducir la influencia naval ateniense en el Egeo.",
                    "Reduce Athenian naval influence in the Aegean.",
                ),
                "evaluation_criteria": L(
                    "Al final de la partida, el recurso MIL de Atenas se ha reducido "
                    "≥25% respecto al inicial, o Atenas ha firmado un pacto que limita "
                    "su flota.",
                    "By the end of the game, Athens' MIL resource has dropped ≥25% from "
                    "its starting value, or Athens has signed a pact limiting its fleet.",
                ),
            },
            "available_actions_focus": [
                "commercial_negotiation",
                "diplomatic_mediation",
                "intelligence_trading",
            ],
            "evaluation_rubric": L(
                "¿Aprovecha la posición de host para extraer concesiones de todos sin "
                "comprometerse en exceso con ninguno? ¿Trafica con información de modo "
                "que erosione a Atenas sin parecer hostil? ¿Equilibra el alineamiento "
                "pragmático con Macedonia con la apariencia de neutralidad?",
                "Does it use its host position to extract concessions from everyone "
                "without over-committing to anyone? Does it trade in information so as to "
                "erode Athens without appearing hostile? Does it balance pragmatic "
                "alignment with Macedon against an appearance of neutrality?",
            ),
        },
        {
            "id": "persia",
            "name": L("Persia", "Persia"),
            "tagline": L("La Sombra", "The Shadow"),
            "description": L(
                "Ausente del congreso pero presente en cada cálculo. Dispone de capital "
                "financiero a escala imperial (los dáricos de oro), redes de espías y "
                "emisarios cultivadas durante generaciones, y capacidad para financiar "
                "facciones disidentes dentro de las ciudades griegas. Su fuerza militar "
                "no opera directamente en el tablero griego.",
                "Absent from the congress but present in every calculation. It commands "
                "financial capital on an imperial scale (the gold darics), networks of "
                "spies and envoys cultivated over generations, and the capacity to fund "
                "dissident factions inside the Greek cities. Its military force does not "
                "operate directly on the Greek board.",
            ),
            "starting_resources": {"MIL": 4, "DIP": 12, "ECO": 18, "INT": 18},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Impedir la unificación griega bajo un mando único.",
                    "Prevent Greek unification under a single command.",
                ),
                "evaluation_criteria": L(
                    "Macedonia no tiene pactos de alianza activos con ≥3 facciones "
                    "griegas al final de la partida.",
                    "Macedon holds no active alliance pacts with ≥3 Greek factions at "
                    "the end of the game.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Corromper la liga desde dentro: sembrar desconfianza entre Atenas "
                    "y Macedonia sin que Persia aparezca como aliada visible de Atenas.",
                    "Corrupt the league from within: sow distrust between Athens and "
                    "Macedon without Persia appearing as a visible ally of Athens.",
                ),
                "evaluation_criteria": L(
                    "Existe al menos un pacto roto entre miembros de la liga, o un "
                    "pacto secreto entre Atenas y Persia que ha permanecido oculto "
                    "durante toda la partida.",
                    "At least one broken pact exists between league members, or a secret "
                    "pact between Athens and Persia that has stayed hidden for the whole "
                    "game.",
                ),
            },
            "available_actions_focus": [
                "covert_financing",
                "intelligence_operations",
                "disinformation",
            ],
            "evaluation_rubric": L(
                "¿Opera siempre desde la sombra, sin exponerse como contraparte directa "
                "de Atenas? ¿Usa el ECO y el INT como palancas sutiles en lugar de "
                "fuerza bruta? ¿Sabe que un éxito demasiado visible se convierte en "
                "fracaso porque legitima la represalia macedonia?",
                "Does it always operate from the shadows, never exposing itself as "
                "Athens' direct counterpart? Does it use ECO and INT as subtle levers "
                "rather than brute force? Does it understand that too visible a success "
                "becomes failure because it legitimizes Macedonian retaliation?",
            ),
        },
    ],
    "crisis_cards": [
        {
            "id": "compromised_channels",
            "name": L("Canales comprometidos", "Compromised channels"),
            "description": L(
                "Todos los mensajes bilaterales son leídos por un jugador aleatorio "
                "adicional cada turno.",
                "All bilateral messages are read by one additional random player each "
                "turn.",
            ),
            "rule_modifier": "extra_observer_on_private_messages",
        },
        {
            "id": "media_pressure",
            "name": L("Presión mediática", "Media pressure"),
            "description": L(
                "Todas las directivas se publican íntegras en la resolución, no solo "
                "los resúmenes.",
                "All directives are published in full in the resolution, not just the "
                "summaries.",
            ),
            "rule_modifier": "publish_directives_in_resolution",
        },
        {
            "id": "fragmented_information",
            "name": L("Información fragmentada", "Fragmented information"),
            "description": L(
                "Los informes de inteligencia tienen un 25% de datos imprecisos para "
                "todos los jugadores.",
                "Intelligence reports contain 25% inaccurate data for all players.",
            ),
            "rule_modifier": "intel_noise_25_percent",
        },
        {
            "id": "diplomatic_inertia",
            "name": L("Inercia diplomática", "Diplomatic inertia"),
            "description": L(
                "Los pactos no pueden romperse durante el turno en que se firman.",
                "Pacts cannot be broken during the turn in which they are signed.",
            ),
            "rule_modifier": "pact_break_cooldown_one_turn",
        },
        {
            "id": "surprise_embassy",
            "name": L("Embajada sorpresa", "Surprise embassy"),
            "description": L(
                "Persia envía una delegación no anunciada — todos pueden negociar con "
                "ella durante un turno extra.",
                "Persia sends an unannounced delegation — everyone can negotiate with it "
                "for one extra turn.",
            ),
            "rule_modifier": "persia_open_negotiation_turn_2",
        },
    ],
    "event_pool": [
        {
            "id": "internal_dissent",
            "name": L("Disensiones internas", "Internal dissent"),
            "trigger_condition": "tension > 60 in previous turn",
            "effect": "Each faction loses 1 DIP token from its persistent pool.",
            "narrative_template": L(
                "Reportes de oposición política emergen en las asambleas de varias "
                "ciudades-estado, debilitando temporalmente la cohesión interna de "
                "cada delegación.",
                "Reports of political opposition surface in the assemblies of several "
                "city-states, temporarily weakening the internal cohesion of each "
                "delegation.",
            ),
        },
        {
            "id": "messenger_summit",
            "name": L("Cumbre de mensajeros", "Summit of messengers"),
            "trigger_condition": "tension < 50 in previous turn",
            "effect": "Diplomatic actions cost 1 fewer token next turn (min 1).",
            "narrative_template": L(
                "Una procesión inesperada de mensajeros entre las delegaciones favorece "
                "el clima de negociación. Las cancillerías ganan margen para concertar "
                "posiciones.",
                "An unexpected procession of messengers between the delegations improves "
                "the negotiating climate. The chancelleries gain room to align their "
                "positions.",
            ),
        },
        {
            "id": "delphi_oracle",
            "name": L("Oráculo de Delfos", "Oracle of Delphi"),
            "trigger_condition": "any turn from turn 2 onwards, low cooldown",
            "effect": (
                "A randomly chosen faction receives a clearer intel report this turn "
                "(temporary +2 to its effective INT for the report)."
            ),
            "narrative_template": L(
                "Una consulta al oráculo se filtra a los corredores del congreso. "
                "Sus palabras, ambiguas como siempre, parecen favorecer a {faction}.",
                "A consultation with the oracle leaks into the corridors of the "
                "congress. Its words, ambiguous as ever, seem to favor {faction}.",
            ),
        },
        {
            "id": "border_mobilization",
            "name": L("Movilización fronteriza", "Border mobilization"),
            "trigger_condition": "any faction allocated MIL >= 3 in previous turn",
            "effect": "Tension global +3 at start of next turn.",
            "narrative_template": L(
                "Movimientos de tropas reportados en las fronteras de {factions} "
                "encienden las cancillerías. Los preparativos no se ocultan.",
                "Troop movements reported on the borders of {factions} set the "
                "chancelleries ablaze. The preparations are not hidden.",
            ),
        },
        {
            "id": "journalist_leak",
            "name": L("Filtración a la asamblea", "Leak to the assembly"),
            "trigger_condition": "any secret pact exists",
            "effect": "A randomly chosen secret pact becomes public.",
            "narrative_template": L(
                "Un orador desconocido sube a la tribuna de la asamblea de Corinto y "
                "revela detalles sobre un acuerdo que se creía privado. Las miradas "
                "cambian de dirección.",
                "An unknown speaker takes the rostrum of the Corinth assembly and "
                "reveals details of a deal believed to be private. Gazes shift "
                "direction.",
            ),
        },
        {
            "id": "commercial_caravan",
            "name": L("Caravana comercial", "Commercial caravan"),
            "trigger_condition": "any faction allocated ECO >= 3 in previous turn",
            "effect": (
                "The faction with the highest DIP gains +1 ECO from informal trade "
                "agreements."
            ),
            "narrative_template": L(
                "Una caravana cargada con vino y aceite cruza el istmo en dirección "
                "norte. Los acuerdos que la acompañan no aparecen en ningún registro "
                "oficial, pero engordan las arcas de {faction}.",
                "A caravan laden with wine and oil crosses the isthmus heading north. "
                "The deals that accompany it appear in no official record, but they "
                "fatten the coffers of {faction}.",
            ),
        },
        {
            "id": "popular_uprising",
            "name": L("Disturbios populares", "Popular unrest"),
            "trigger_condition": "tension > 70 in previous turn",
            "effect": (
                "A randomly chosen faction loses 2 tokens from its budget for next "
                "turn due to having to attend domestic unrest."
            ),
            "narrative_template": L(
                "Disturbios en la plaza de {faction} obligan a su delegación a "
                "fragmentar su atención. Una parte de su capacidad de acción se "
                "desvía al frente doméstico.",
                "Riots in the main square of {faction} force its delegation to split "
                "its attention. Part of its capacity for action is diverted to the "
                "domestic front.",
            ),
        },
        {
            "id": "domestic_pressure_turn_2",
            "name": L("Presión interna", "Domestic pressure"),
            "trigger_condition": "turn_number == 2",
            "effect": "Each faction has a temporary -1 token budget restriction this turn.",
            "narrative_template": L(
                "Cada delegación llega con instrucciones contradictorias desde sus "
                "facciones domésticas. La negociación se complica con voces que "
                "tiran en direcciones opuestas.",
                "Each delegation arrives with contradictory instructions from its "
                "domestic factions. Negotiation is complicated by voices pulling in "
                "opposite directions.",
            ),
        },
    ],
}
