"""Static data for the Arctic Crisis scenario (2031).

User-facing strings are wrapped in `L(es, en)` and resolved to a single
language at load time. Logic-only fields (ids, resources, rule modifiers,
trigger conditions) stay as plain values.
"""

from src.scenarios.localize import L

ARCTIC_SCENARIO: dict = {
    "id": "arctic_2031",
    "name": L("Crisis del Ártico", "Arctic Crisis"),
    "year": "2031",
    "type": "hybrid",
    "max_turns": 6,
    "min_players": 4,
    "max_players": 6,
    "context": L(
        "2031. El deshielo ártico ha superado todos los modelos. La Ruta del Mar del "
        "Norte es navegable nueve meses al año. Los fondos marinos contienen reservas "
        "de minerales críticos estimadas en billones de dólares. Rusia lleva años "
        "ampliando su presencia militar. China, sin territorio ártico, se declara "
        "'estado ártico próximo'. Un incidente entre un buque chino y la guardia "
        "costera canadiense ha colapsado el Consejo Ártico. Las potencias se reúnen "
        "para acordar un nuevo marco de gobernanza antes de que los hechos sobre el "
        "terreno lo hagan irreversible.",
        "2031. Arctic melt has outrun every model. The Northern Sea Route is navigable "
        "nine months a year. The seabed holds critical-mineral reserves estimated in "
        "the trillions of dollars. Russia has spent years expanding its military "
        "presence. China, with no Arctic territory, declares itself a 'near-Arctic "
        "state'. An incident between a Chinese vessel and the Canadian coast guard has "
        "collapsed the Arctic Council. The powers convene to agree on a new governance "
        "framework before facts on the ground make it irreversible.",
    ),
    "example_directive": L(
        "Reforzar la presencia militar en la plataforma continental mientras "
        "propongo a China un acuerdo bilateral de explotación mineral.",
        "Reinforce the military presence on the continental shelf while proposing a "
        "bilateral mineral-extraction deal to China.",
    ),
    "pact_type_labels": {
        "alliance": {
            "label": L("Pacto de cooperación ártica", "Arctic cooperation pact"),
            "help": L(
                "+15% efectividad en acciones contra targets comunes.",
                "+15% effectiveness on actions against shared targets.",
            ),
        },
        "non_aggression": {
            "label": L(
                "Acuerdo de no agresión territorial", "Territorial non-aggression accord"
            ),
            "help": L("-30% daño en agresiones mutuas.", "-30% damage on mutual aggression."),
        },
        "trade": {
            "label": L("Acuerdo de explotación conjunta", "Joint extraction agreement"),
            "help": L(
                "Intercambio de recursos cada turno (1 ECO ↔ 1 DIP).",
                "Resource exchange each turn (1 ECO ↔ 1 DIP).",
            ),
        },
        "intel_share": {
            "label": L("Intercambio de inteligencia ártica", "Arctic intelligence sharing"),
            "help": L("Informes con más detalle.", "More detailed reports."),
        },
    },
    "factions": [
        {
            "id": "rusia",
            "name": L("Rusia", "Russia"),
            "tagline": L("El Ocupante de Facto", "The De Facto Occupant"),
            "description": L(
                "Presencia militar dominante en el Ártico, infraestructura consolidada "
                "durante décadas, control efectivo de la mayor parte de la Ruta del "
                "Mar del Norte. Dispone de bases militares, rompehielos nucleares y "
                "reclamaciones territoriales sobre la plataforma continental que el "
                "resto rechaza pero no puede ignorar.",
                "Dominant military presence in the Arctic, infrastructure consolidated "
                "over decades, effective control of most of the Northern Sea Route. It "
                "fields military bases, nuclear icebreakers and territorial claims over "
                "the continental shelf that the others reject but cannot ignore.",
            ),
            "starting_resources": {"MIL": 18, "DIP": 8, "ECO": 12, "INT": 12},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Conseguir el reconocimiento legal de su plataforma continental "
                    "extendida y el control formal de la Ruta del Mar del Norte.",
                    "Secure legal recognition of its extended continental shelf and "
                    "formal control of the Northern Sea Route.",
                ),
                "evaluation_criteria": L(
                    "Al final de la partida, Rusia tiene al menos un pacto de alianza "
                    "o no agresión activo con China, y ningún otro actor tiene un "
                    "pacto de alianza activo con Canadá o EEUU que mencione la Ruta "
                    "del Mar del Norte.",
                    "By the end of the game, Russia holds at least one active alliance "
                    "or non-aggression pact with China, and no other actor holds an "
                    "active alliance pact with Canada or the USA referencing the "
                    "Northern Sea Route.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Cerrar un acuerdo bilateral de extracción de minerales con China "
                    "antes de que se firme el tratado multilateral — fijando las "
                    "condiciones antes de que China gane posición autónoma en el Ártico.",
                    "Close a bilateral mineral-extraction deal with China before the "
                    "multilateral treaty is signed — setting the terms before China "
                    "gains an autonomous foothold in the Arctic.",
                ),
                "evaluation_criteria": L(
                    "Existe un pacto activo (trade o alianza) entre Rusia y China al "
                    "final de la partida, firmado antes del turno 4, y China no tiene "
                    "ningún pacto con EEUU ni Canadá.",
                    "An active pact (trade or alliance) exists between Russia and China "
                    "at the end of the game, signed before turn 4, and China holds no "
                    "pact with the USA or Canada.",
                ),
            },
            "available_actions_focus": [
                "military_presence",
                "bilateral_extraction",
                "information_control",
            ],
            "evaluation_rubric": L(
                "¿Usa la presencia militar como hecho consumado sin provocar una "
                "respuesta OTAN que consolide el bloque contrario? ¿Cierra el "
                "acuerdo con China antes de que China gane suficiente autonomía para "
                "negociar directamente con los occidentales? ¿Gestiona la tensión "
                "con Noruega — el mediador más peligroso — sin antagonizarla "
                "completamente?",
                "Does it use military presence as a fait accompli without provoking a "
                "NATO response that consolidates the opposing bloc? Does it close the "
                "deal with China before China gains enough autonomy to negotiate "
                "directly with the West? Does it manage tension with Norway — the most "
                "dangerous mediator — without fully antagonizing it?",
            ),
        },
        {
            "id": "eeuu",
            "name": L("Estados Unidos", "United States"),
            "tagline": L("El Rezagado Alarmado", "The Alarmed Latecomer"),
            "description": L(
                "Primera potencia militar global, pero con presencia ártica limitada "
                "respecto a Rusia. Lidera las alianzas occidentales, tiene capacidad "
                "tecnológica y financiera, y puede presionar a sus aliados — pero "
                "enfrenta un dilema estructural: para mantener a Canadá alineado, "
                "tendría que ceder en su propia doctrina de libertad de navegación.",
                "The world's foremost military power, but with a limited Arctic "
                "presence relative to Russia. It leads the Western alliances, holds "
                "technological and financial clout, and can lean on its allies — but "
                "faces a structural dilemma: to keep Canada aligned it would have to "
                "concede on its own freedom-of-navigation doctrine.",
            ),
            "starting_resources": {"MIL": 16, "DIP": 12, "ECO": 12, "INT": 10},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Garantizar la libertad de navegación y limitar la influencia rusa y china.",
                    "Guarantee freedom of navigation and limit Russian and Chinese influence.",
                ),
                "evaluation_criteria": L(
                    "Al final de la partida, EEUU tiene un pacto de alianza activo "
                    "con Canadá y China no tiene ningún pacto activo con Rusia.",
                    "By the end of the game, the USA holds an active alliance pact with "
                    "Canada and China holds no active pact with Russia.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Asegurar el alineamiento canadiense antes de la firma del "
                    "tratado, aunque eso implique concesiones privadas sobre el Paso "
                    "del Noroeste que contradicen la doctrina oficial estadounidense "
                    "de libertad de navegación.",
                    "Secure Canadian alignment before the treaty is signed, even if it "
                    "means private concessions on the Northwest Passage that contradict "
                    "official U.S. freedom-of-navigation doctrine.",
                ),
                "evaluation_criteria": L(
                    "Existe un pacto de alianza entre EEUU y Canadá al final de la "
                    "partida, y Canadá no tiene ningún pacto con China ni con Rusia.",
                    "An alliance pact exists between the USA and Canada at the end of "
                    "the game, and Canada holds no pact with China or Russia.",
                ),
            },
            "available_actions_focus": [
                "alliance_management",
                "china_containment",
                "diplomatic_pressure",
            ],
            "evaluation_rubric": L(
                "¿Consigue el alineamiento canadiense sin tener que hacer públicas "
                "las concesiones que lo hacen posible? ¿Evita que Noruega se "
                "posicione como árbitro neutral reduciendo la influencia americana? "
                "¿Mantiene a Japón y Europa dentro del bloque sin que busquen "
                "acuerdos propios con China o Rusia?",
                "Does it secure Canadian alignment without having to make public the "
                "concessions that make it possible? Does it keep Norway from casting "
                "itself as a neutral arbiter that erodes American influence? Does it "
                "keep Japan and Europe inside the bloc without them seeking their own "
                "deals with China or Russia?",
            ),
        },
        {
            "id": "canada",
            "name": L("Canadá", "Canada"),
            "tagline": L("El Soberano Disputado", "The Disputed Sovereign"),
            "description": L(
                "Estado ártico con soberanía sobre el Paso del Noroeste — que el "
                "resto del mundo no reconoce como aguas interiores. Posee reservas "
                "naturales relevantes, un argumento jurídico sólido basado en "
                "derechos indígenas, y la posición de aliado imprescindible de EEUU "
                "que le da más palanca de la que parece.",
                "An Arctic state with sovereignty over the Northwest Passage — which "
                "the rest of the world does not recognize as internal waters. It holds "
                "significant natural reserves, a solid legal argument grounded in "
                "Indigenous rights, and the position of indispensable U.S. ally that "
                "gives it more leverage than it appears.",
            ),
            "starting_resources": {"MIL": 6, "DIP": 14, "ECO": 10, "INT": 10},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": L(
                    "Conseguir el reconocimiento del Paso del Noroeste como aguas "
                    "interiores canadienses en el tratado final.",
                    "Secure recognition of the Northwest Passage as Canadian internal "
                    "waters in the final treaty.",
                ),
                "evaluation_criteria": L(
                    "Al final de la partida, Canadá tiene un pacto de alianza con "
                    "EEUU y ninguna facción tiene un pacto que explícitamente niegue "
                    "la soberanía canadiense (evaluado como: Canadá no ha roto ningún "
                    "pacto de no agresión durante la partida).",
                    "By the end of the game, Canada holds an alliance pact with the USA "
                    "and no faction holds a pact that explicitly denies Canadian "
                    "sovereignty (evaluated as: Canada has not broken any non-aggression "
                    "pact during the game).",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Extraer concesiones bilaterales de EEUU en frentes pendientes "
                    "(energía, comercio, defensa continental) a cambio de alineamiento "
                    "político en la cumbre ártica.",
                    "Extract bilateral concessions from the USA on open fronts (energy, "
                    "trade, continental defense) in exchange for political alignment at "
                    "the Arctic summit.",
                ),
                "evaluation_criteria": L(
                    "Existe un pacto de alianza activo entre Canadá y EEUU firmado "
                    "antes del turno 4, y el recurso ECO de Canadá ha aumentado "
                    "respecto al inicial.",
                    "An active alliance pact exists between Canada and the USA signed "
                    "before turn 4, and Canada's ECO resource has increased relative to "
                    "its starting value.",
                ),
            },
            "available_actions_focus": [
                "legal_leverage",
                "bilateral_bargaining",
                "indigenous_rights_shield",
            ],
            "evaluation_rubric": L(
                "¿Convierte la soberanía sobre el Paso del Noroeste en palanca "
                "concreta sin que EEUU la perciba como extorsión? ¿Usa los derechos "
                "indígenas como escudo jurídico legítimo en lugar de solo como "
                "táctica dilatoria? ¿Sabe cuándo el apoyo de EEUU tiene más valor "
                "que cualquier oferta de Rusia o China?",
                "Does it turn sovereignty over the Northwest Passage into concrete "
                "leverage without the USA perceiving it as extortion? Does it use "
                "Indigenous rights as a legitimate legal shield rather than a mere "
                "stalling tactic? Does it know when U.S. support is worth more than any "
                "offer from Russia or China?",
            ),
        },
        {
            "id": "noruega",
            "name": L("Noruega", "Norway"),
            "tagline": L("El Mediador Creíble", "The Credible Mediator"),
            "description": L(
                "Estado ártico con décadas de experiencia técnica en el Ártico, "
                "credibilidad diplomática ganada como mediador en múltiples conflictos, "
                "y el mayor fondo soberano del mundo como respaldo financiero. Su "
                "membresía en la OTAN le da protección pero también le complica la "
                "neutralidad que necesita para mediar.",
                "An Arctic state with decades of Arctic technical expertise, diplomatic "
                "credibility earned as a mediator in multiple conflicts, and the world's "
                "largest sovereign wealth fund as financial backing. Its NATO membership "
                "gives it protection but also complicates the neutrality it needs to "
                "mediate.",
            ),
            "starting_resources": {"MIL": 6, "DIP": 18, "ECO": 12, "INT": 8},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": L(
                    "Establecer un marco multilateral vinculante de gobernanza ártica "
                    "que incluya a todos los actores principales.",
                    "Establish a binding multilateral Arctic governance framework that "
                    "includes all the main actors.",
                ),
                "evaluation_criteria": L(
                    "Al final de la partida, Noruega tiene pactos activos con al menos "
                    "3 facciones diferentes, incluyendo al menos una de cada bloque "
                    "(occidental y ruso-chino).",
                    "By the end of the game, Norway holds active pacts with at least 3 "
                    "different factions, including at least one from each bloc (Western "
                    "and Russo-Chinese).",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Posicionarse como el mediador indispensable, lo que requiere "
                    "contradecir a EEUU en al menos un punto clave — aceptando el "
                    "estatus de observador de China — para ganarse la confianza del "
                    "bloque contrario.",
                    "Position itself as the indispensable mediator, which requires "
                    "contradicting the USA on at least one key point — accepting China's "
                    "observer status — to earn the trust of the opposing bloc.",
                ),
                "evaluation_criteria": L(
                    "Noruega tiene un pacto activo con China al final de la partida, "
                    "y también mantiene al menos un pacto con EEUU o Canadá.",
                    "Norway holds an active pact with China at the end of the game and "
                    "also keeps at least one pact with the USA or Canada.",
                ),
            },
            "available_actions_focus": [
                "multilateral_mediation",
                "technical_expertise",
                "diplomatic_bridging",
            ],
            "evaluation_rubric": L(
                "¿Acepta el coste de contradecir a EEUU en puntos específicos para "
                "ganar credibilidad como árbitro neutral? ¿Traduce su experiencia "
                "técnica ártica en propuestas concretas que otros no pueden rechazar "
                "sin coste reputacional? ¿Mantiene el equilibrio entre lealtad "
                "atlántica y rol de mediador sin quedar atrapada entre los dos?",
                "Does it accept the cost of contradicting the USA on specific points to "
                "gain credibility as a neutral arbiter? Does it translate its Arctic "
                "technical expertise into concrete proposals others cannot reject "
                "without reputational cost? Does it hold the balance between Atlantic "
                "loyalty and its mediator role without getting trapped between the two?",
            ),
        },
        {
            "id": "china",
            "name": L("China", "China"),
            "tagline": L("El Reclamante sin Territorio", "The Claimant Without Territory"),
            "description": L(
                "Sin territorio ártico propio, pero con inversiones en infraestructura, "
                "relaciones con actores menores, capacidad financiera masiva y la "
                "declaración unilateral de 'estado ártico próximo'. Su objetivo es "
                "la legitimidad formal antes de que el tratado multilateral la excluya "
                "definitivamente del nuevo orden ártico.",
                "No Arctic territory of its own, but with infrastructure investments, "
                "relationships with minor actors, massive financial capacity and the "
                "unilateral declaration of 'near-Arctic state'. Its goal is formal "
                "legitimacy before the multilateral treaty locks it out of the new "
                "Arctic order for good.",
            ),
            "starting_resources": {"MIL": 8, "DIP": 12, "ECO": 18, "INT": 14},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Obtener estatus formal de observador permanente en la gobernanza "
                    "ártica y acceso garantizado a rutas y recursos.",
                    "Obtain formal permanent-observer status in Arctic governance and "
                    "guaranteed access to routes and resources.",
                ),
                "evaluation_criteria": L(
                    "Al final de la partida, China tiene pactos activos con al menos "
                    "2 facciones árticas (Rusia, Canadá, Noruega o Groenlandia).",
                    "By the end of the game, China holds active pacts with at least 2 "
                    "Arctic factions (Russia, Canada, Norway or Greenland).",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Establecer una instalación de investigación permanente en "
                    "territorio disputado antes de la firma del tratado — un hecho "
                    "consumado que le dé presencia física en el Ártico que el "
                    "tratado tendrá que reconocer o ignorar.",
                    "Establish a permanent research facility in disputed territory "
                    "before the treaty is signed — a fait accompli that gives it a "
                    "physical Arctic presence the treaty will have to recognize or "
                    "ignore.",
                ),
                "evaluation_criteria": L(
                    "China ha ejecutado al menos una acción MIL ofensiva exitosa "
                    "(no bloqueada) durante la partida, y al final tiene un pacto "
                    "activo con Rusia o Groenlandia.",
                    "China has executed at least one successful (unblocked) offensive "
                    "MIL action during the game, and at the end holds an active pact "
                    "with Russia or Greenland.",
                ),
            },
            "available_actions_focus": [
                "economic_investment",
                "fait_accompli",
                "legitimacy_building",
            ],
            "evaluation_rubric": L(
                "¿Establece hechos sobre el terreno sin provocar una respuesta "
                "coordinada del bloque occidental que la excluya formalmente? "
                "¿Cierra el acuerdo con Rusia antes de que Rusia perciba el "
                "riesgo de crear un competidor ártico? ¿Usa su capacidad financiera "
                "para construir dependencias con actores menores (Groenlandia, "
                "Noruega) que le den votos en el proceso multilateral?",
                "Does it establish facts on the ground without provoking a coordinated "
                "Western response that formally excludes it? Does it close the deal "
                "with Russia before Russia perceives the risk of creating an Arctic "
                "competitor? Does it use its financial capacity to build dependencies "
                "with minor actors (Greenland, Norway) that give it votes in the "
                "multilateral process?",
            ),
        },
        {
            "id": "groenlandia",
            "name": L("Groenlandia", "Greenland"),
            "tagline": L("El Comodín", "The Wild Card"),
            "description": L(
                "Territorio autónomo danés con reservas de minerales críticos de "
                "primera magnitud, posición geográfica estratégica y un movimiento "
                "de independencia en auge. Cada potencia quiere su alineamiento. "
                "Su mayor palanca es precisamente la neutralidad que todos intentan "
                "comprar.",
                "A Danish autonomous territory with first-rate critical-mineral "
                "reserves, a strategic geographic position and a rising independence "
                "movement. Every power wants its alignment. Its greatest leverage is "
                "precisely the neutrality everyone is trying to buy.",
            ),
            "starting_resources": {"MIL": 4, "DIP": 10, "ECO": 14, "INT": 8},
            "token_budget_per_turn": 3,
            "public_objective": {
                "text": L(
                    "Maximizar los beneficios económicos de su posición estratégica.",
                    "Maximize the economic benefits of its strategic position.",
                ),
                "evaluation_criteria": L(
                    "El recurso ECO de Groenlandia ha aumentado ≥4 puntos respecto "
                    "al inicial al final de la partida.",
                    "Greenland's ECO resource has increased by ≥4 points over its "
                    "starting value by the end of the game.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Conseguir compromisos de inversión vinculantes de al menos dos "
                    "potencias de bloques distintos antes de declarar su posición "
                    "en el tratado — maximizando la competencia entre pretendientes "
                    "sin quemar a ninguno.",
                    "Secure binding investment commitments from at least two powers of "
                    "different blocs before declaring its position on the treaty — "
                    "maximizing competition among suitors without burning any of them.",
                ),
                "evaluation_criteria": L(
                    "Groenlandia tiene pactos activos con al menos 2 facciones de "
                    "bloques distintos (uno occidental: EEUU, Canadá o Noruega; "
                    "y uno oriental: Rusia o China) al final de la partida.",
                    "Greenland holds active pacts with at least 2 factions from "
                    "different blocs (one Western: USA, Canada or Norway; and one "
                    "Eastern: Russia or China) at the end of the game.",
                ),
            },
            "available_actions_focus": [
                "strategic_ambiguity",
                "investment_competition",
                "independence_leverage",
            ],
            "evaluation_rubric": L(
                "¿Mantiene la ambigüedad estratégica lo suficiente como para que "
                "los pretendientes sigan compitiendo, sin que ninguno la perciba "
                "como definitivamente perdida? ¿Extrae compromisos reales de "
                "inversión antes de comprometerse con alguien? ¿Entiende cuándo "
                "la neutralidad se ha convertido en irrelevancia y es el momento "
                "de declarar una posición?",
                "Does it keep strategic ambiguity alive enough that suitors keep "
                "competing, without any of them seeing it as definitively lost? Does it "
                "extract real investment commitments before committing to anyone? Does "
                "it understand when neutrality has turned into irrelevance and it is "
                "time to declare a position?",
            ),
        },
    ],
    "crisis_cards": [
        {
            "id": "arctic_storm",
            "name": L("Tormenta ártica", "Arctic storm"),
            "description": L(
                "Turno 2: todas las acciones militares y logísticas tienen coste "
                "incrementado en 1 MIL adicional este turno.",
                "Turn 2: all military and logistical actions cost 1 additional MIL "
                "this turn.",
            ),
            "rule_modifier": "military_cost_increase_turn2",
        },
        {
            "id": "seismic_data_leak",
            "name": L("Filtración de datos sísmicos", "Seismic data leak"),
            "description": L(
                "Se hacen públicas reservas de minerales mayores de lo esperado en "
                "zona disputada. Tensión global +8 de forma inmediata.",
                "Larger-than-expected mineral reserves in a disputed zone become "
                "public. Global tension +8 immediately.",
            ),
            "rule_modifier": "tension_spike_8",
        },
        {
            "id": "energy_grid_failure",
            "name": L("Crisis energética global", "Global energy crisis"),
            "description": L(
                "Un fallo en infraestructura crítica europea eleva la urgencia: "
                "todas las facciones dependientes de energía pierden 1 ECO este turno.",
                "A failure in critical European infrastructure raises the urgency: all "
                "energy-dependent factions lose 1 ECO this turn.",
            ),
            "rule_modifier": "energy_importer_eco_penalty",
        },
        {
            "id": "indigenous_veto",
            "name": L("Veto indígena", "Indigenous veto"),
            "description": L(
                "Comunidades indígenas árticas impugnan un acuerdo. Canadá puede "
                "bloquear cualquier pacto que le involucre sin coste DIP este turno.",
                "Arctic Indigenous communities challenge a deal. Canada can block any "
                "pact involving it at no DIP cost this turn.",
            ),
            "rule_modifier": "canada_pact_veto_turn",
        },
        {
            "id": "military_incident",
            "name": L("Incidente naval", "Naval incident"),
            "description": L(
                "Tensión militar súbita: todas las facciones con MIL < 8 pierden "
                "1 token de presupuesto este turno por medidas de seguridad de "
                "emergencia.",
                "Sudden military tension: all factions with MIL < 8 lose 1 budget "
                "token this turn to emergency security measures.",
            ),
            "rule_modifier": "low_mil_budget_penalty",
        },
    ],
    "event_pool": [
        {
            "id": "navigation_incident",
            "name": L("Incidente de navegación", "Navigation incident"),
            "trigger_condition": "any faction allocated MIL >= 3 in previous turn",
            "effect": "Tension global +5. The faction with highest MIL must justify.",
            "narrative_template": L(
                "Un buque de {faction} cruza una zona de exclusión declarada por "
                "otro actor. Las comunicaciones de emergencia se multiplican. "
                "Los portavoces preparan declaraciones que no dicen nada.",
                "A {faction} vessel crosses an exclusion zone declared by another "
                "actor. Emergency communications multiply. Spokespeople prepare "
                "statements that say nothing.",
            ),
        },
        {
            "id": "mineral_discovery",
            "name": L("Descubrimiento de yacimiento", "Deposit discovery"),
            "trigger_condition": "turn_number >= 2",
            "effect": (
                "A randomly chosen faction with territorial claims gains +2 ECO. "
                "Tension +3 globally."
            ),
            "narrative_template": L(
                "Imágenes satelitales revelan un yacimiento de tierras raras en "
                "la plataforma reclamada por {faction}. El anuncio genera reacciones "
                "inmediatas en todas las cancillerías involucradas.",
                "Satellite imagery reveals a rare-earth deposit on the shelf claimed "
                "by {faction}. The announcement triggers immediate reactions in every "
                "chancellery involved.",
            ),
        },
        {
            "id": "climate_pressure",
            "name": L("Presión climática", "Climate pressure"),
            "trigger_condition": "tension < 50 in previous turn",
            "effect": (
                "All factions gain +1 DIP for 'climate diplomacy' framing this turn."
            ),
            "narrative_template": L(
                "Las imágenes del deshielo ártico dominan los medios globales. "
                "La presión de la opinión pública obliga a todas las delegaciones "
                "a adoptar un lenguaje más cooperativo — al menos en público.",
                "Images of Arctic melt dominate global media. Public-opinion pressure "
                "forces every delegation to adopt more cooperative language — at least "
                "in public.",
            ),
        },
        {
            "id": "china_infrastructure",
            "name": L("Infraestructura china anunciada", "Chinese infrastructure announced"),
            "trigger_condition": "turn_number == 3",
            "effect": (
                "China gains +2 ECO. EEUU and Canada must respond or lose 1 DIP each."
            ),
            "narrative_template": L(
                "Beijing anuncia la financiación de una nueva estación de "
                "investigación en {region}. El proyecto incluye un muelle de doble "
                "uso. Las reacciones se producen en cuestión de horas.",
                "Beijing announces funding for a new research station in {region}. The "
                "project includes a dual-use pier. Reactions come within hours.",
            ),
        },
        {
            "id": "nato_coordination",
            "name": L("Coordinación OTAN", "NATO coordination"),
            "trigger_condition": "any OTAN faction has alliance pact with another OTAN faction",
            "effect": "EEUU, Canada, and Noruega each gain +1 MIL temporarily.",
            "narrative_template": L(
                "Una reunión de urgencia en el cuartel general de la OTAN produce "
                "una declaración conjunta sobre la soberanía ártica. Los efectivos "
                "de los aliados en la región aumentan discretamente.",
                "An emergency meeting at NATO headquarters produces a joint statement "
                "on Arctic sovereignty. Allied forces in the region quietly increase.",
            ),
        },
        {
            "id": "russian_veto_threat",
            "name": L("Amenaza de veto ruso", "Russian veto threat"),
            "trigger_condition": "tension > 65 in previous turn",
            "effect": "Rusia can cancel one multilateral pact proposed this turn without DIP cost.",
            "narrative_template": L(
                "Moscú hace circular entre delegaciones una nota verbal: ciertos "
                "arreglos multilaterales serán considerados contrarios a los intereses "
                "de seguridad rusa. La nota es suficientemente vaga para generar "
                "incertidumbre y suficientemente concreta para ser una amenaza.",
                "Moscow circulates a verbal note among delegations: certain multilateral "
                "arrangements will be considered contrary to Russian security interests. "
                "The note is vague enough to breed uncertainty and specific enough to be "
                "a threat.",
            ),
        },
        {
            "id": "greenland_election",
            "name": L("Elecciones en Groenlandia", "Greenland elections"),
            "trigger_condition": "turn_number == 4",
            "effect": (
                "Groenlandia gains +2 DIP. Other factions must re-evaluate any pacts "
                "with Greenland (they remain active but must be reconfirmed next turn)."
            ),
            "narrative_template": L(
                "Las elecciones en Nuuk producen un nuevo gobierno con mandato "
                "explícito de maximizar la autonomía y los beneficios económicos. "
                "Las embajadas actualizan sus análisis sobre Groenlandia.",
                "Elections in Nuuk produce a new government with an explicit mandate to "
                "maximize autonomy and economic benefits. Embassies update their "
                "analyses of Greenland.",
            ),
        },
        {
            "id": "tech_breakthrough",
            "name": L("Ruptura tecnológica", "Technological breakthrough"),
            "trigger_condition": "any faction allocated INT >= 3 in previous turn",
            "effect": (
                "The faction with the highest INT gains a free intel report about "
                "any one other faction's current resource levels."
            ),
            "narrative_template": L(
                "Satélites de nueva generación y análisis de señales de {faction} "
                "producen un informe de inteligencia más detallado de lo esperado. "
                "La ventaja de información es temporal, pero puede ser decisiva.",
                "Next-generation satellites and signals analysis from {faction} produce "
                "an intelligence report more detailed than expected. The information "
                "advantage is temporary, but it can be decisive.",
            ),
        },
    ],
}
