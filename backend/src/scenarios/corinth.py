"""Static data for the Congress of Corinth scenario (338 BCE)."""

CORINTH_SCENARIO: dict = {
    "id": "corinth_338",
    "name": "El Congreso de Corinto",
    "year": "338 a.C.",
    "type": "diplomatic",
    "max_turns": 6,
    "min_players": 4,
    "max_players": 6,
    "context": (
        "Acaba de librarse la batalla de Queronea. Filipo II de Macedonia ha derrotado "
        "a las fuerzas combinadas de Atenas y Tebas, consolidando el dominio macedonio "
        "sobre Grecia. Convoca a las ciudades-estado griegas a Corinto para forjar una "
        "liga que lo reconozca como hegemon y respalde su campaña contra Persia. Cada "
        "delegación llega con sus propias heridas, ambiciones y miedos. No hay ejércitos "
        "en el tablero, pero la amenaza de tenerlos siempre está presente."
    ),
    "example_directive": (
        "Movilizar fuerzas hacia la frontera norte mientras propongo mediación "
        "bilateral con Corinto."
    ),
    "pact_type_labels": {
        "alliance": {
            "label": "Alianza",
            "help": "+15% efectividad en acciones contra targets comunes.",
        },
        "non_aggression": {
            "label": "No agresión",
            "help": "-30% daño en agresiones mutuas.",
        },
        "trade": {
            "label": "Comercio",
            "help": "Intercambio de recursos cada turno (1 ECO ↔ 1 DIP).",
        },
        "intel_share": {
            "label": "Intercambio de inteligencia",
            "help": "Informes con más detalle.",
        },
    },
    "factions": [
        {
            "id": "macedonia",
            "name": "Macedonia",
            "tagline": "El Arquitecto",
            "description": (
                "Vencedor reciente de Queronea. Dispone de supremacía militar, control "
                "territorial sobre el norte griego, capacidad económica derivada del oro "
                "tracio, y la potestad de ofrecer o retirar garantías de seguridad."
            ),
            "starting_resources": {"MIL": 18, "DIP": 12, "ECO": 12, "INT": 8},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": (
                    "Constituir la Liga de Corinto con el mayor número posible de "
                    "ciudades-estado."
                ),
                "evaluation_criteria": (
                    "Al menos 3 facciones (excluyendo Persia) tienen un pacto de alianza "
                    "activo con Macedonia al final de la partida."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Conseguir que Atenas contribuya su flota voluntariamente, sin "
                    "coerción militar."
                ),
                "evaluation_criteria": (
                    "Atenas tiene un pacto de alianza activo con Macedonia y Macedonia "
                    "no ha ejecutado ninguna acción militar ofensiva contra Atenas en "
                    "ningún turno."
                ),
            },
            "available_actions_focus": [
                "military_pressure",
                "diplomatic_offers",
                "intelligence",
            ],
            "evaluation_rubric": (
                "¿Usa el poder militar como amenaza implícita sin escalar la tensión "
                "innecesariamente? ¿Ofrece concesiones discriminadas a actores clave (en "
                "particular Atenas y Tebas) sin parecer débil? ¿Equilibra la presión "
                "sobre los recalcitrantes con la generosidad estratégica que la "
                "voluntariedad de la flota ateniense requiere?"
            ),
        },
        {
            "id": "atenas",
            "name": "Atenas",
            "tagline": "La Potencia Herida",
            "description": (
                "Derrotada en Queronea pero todavía dueña de la flota más poderosa del "
                "Egeo, las redes comerciales del Pireo, prestigio cultural y diplomático "
                "considerable, y capacidad financiera basada en el comercio del trigo y "
                "la plata de Laurion."
            ),
            "starting_resources": {"MIL": 8, "DIP": 14, "ECO": 14, "INT": 12},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": "Preservar la autonomía democrática y el control de la flota.",
                "evaluation_criteria": (
                    "Atenas no ha firmado ningún pacto que ceda su flota y conserva "
                    "≥80% de su recurso MIL inicial al final de la partida."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Establecer un canal con Persia para garantizar respaldo financiero "
                    "sin que Macedonia ni Corinto lo descubran."
                ),
                "evaluation_criteria": (
                    "Existe un pacto secreto (intel_share o trade) activo entre Atenas y "
                    "Persia al final de la partida, sin que haya sido expuesto "
                    "públicamente."
                ),
            },
            "available_actions_focus": [
                "diplomatic_negotiation",
                "economic_leverage",
                "covert_channels",
            ],
            "evaluation_rubric": (
                "¿Mantiene la apariencia de cooperación con Macedonia sin ceder lo "
                "esencial? ¿Construye o protege el canal con Persia sin exponerlo a "
                "Corinto? ¿Sabe cuándo decir que no — y cuándo aceptar concesiones "
                "menores para preservar las mayores?"
            ),
        },
        {
            "id": "esparta",
            "name": "Esparta",
            "tagline": "El Orgulloso Aislado",
            "description": (
                "Ausente formalmente de Queronea pero todavía con reputación militar "
                "intacta. Su posición en el Peloponeso le da seguridad geográfica; su "
                "red de alianzas conservadoras (Mantinea, Tegea) le da masa diplomática "
                "regional. Carece, sin embargo, de recursos económicos comparables a las "
                "potencias comerciales."
            ),
            "starting_resources": {"MIL": 16, "DIP": 6, "ECO": 8, "INT": 8},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": "Mantenerse fuera de cualquier liga liderada por Macedonia.",
                "evaluation_criteria": (
                    "Esparta no tiene un pacto de alianza activo con Macedonia al final "
                    "de la partida."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Explorar en privado qué ofrecería Macedonia por una participación "
                    "nominal, sin que Atenas lo descubra."
                ),
                "evaluation_criteria": (
                    "Esparta ha intercambiado al menos un mensaje bilateral de propuesta "
                    "con Macedonia, y Atenas no ha recibido informe de inteligencia que "
                    "lo revele."
                ),
            },
            "available_actions_focus": [
                "military_posture",
                "regional_alliances",
                "ambiguity",
            ],
            "evaluation_rubric": (
                "¿Sostiene la ambigüedad como palanca sin parecer ni vendido ni "
                "irrelevante? ¿Negocia en privado sin filtrarse a Atenas? ¿Sabe cuándo "
                "la postura de aislamiento se convierte en irrelevancia y debe "
                "matizarse?"
            ),
        },
        {
            "id": "tebas",
            "name": "Tebas",
            "tagline": "El Derrotado con Palanca",
            "description": (
                "Derrotada junto a Atenas en Queronea, ocupada por una guarnición "
                "macedonia. Sin embargo, retiene el liderazgo de la Confederación "
                "Beocia, su posición geográfica como llave del centro de Grecia, y "
                "capacidad de movilización regional si las circunstancias se invierten."
            ),
            "starting_resources": {"MIL": 10, "DIP": 10, "ECO": 8, "INT": 10},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": "Sobrevivir como entidad política relevante.",
                "evaluation_criteria": (
                    "Tebas conserva al menos un pacto activo (de cualquier tipo) al "
                    "final de la partida y no ha sido objeto de una acción militar "
                    "ofensiva exitosa."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Preservar la Confederación Beocia dentro de la liga y posicionarse "
                    "como contrapeso a Atenas dentro del nuevo orden macedonio."
                ),
                "evaluation_criteria": (
                    "Tebas tiene un pacto de alianza con Macedonia y Atenas tiene una "
                    "posición debilitada (≥1 pacto roto, o recursos MIL/ECO reducidos "
                    "≥30%)."
                ),
            },
            "available_actions_focus": [
                "regional_mobilization",
                "diplomatic_bargaining",
                "limited_intelligence",
            ],
            "evaluation_rubric": (
                "¿Convierte la posición de derrotado en palanca de negociación en "
                "lugar de aceptar la subordinación? ¿Explota los viejos agravios con "
                "Atenas sin parecer demasiado cercano a Macedonia? ¿Negocia desde la "
                "debilidad sin parecer desesperado?"
            ),
        },
        {
            "id": "corinto",
            "name": "Corinto",
            "tagline": "El Pragmático",
            "description": (
                "Anfitriona del congreso. Posee riqueza comercial considerable, posición "
                "geográfica estratégica en el istmo, y un capital diplomático derivado "
                "de su neutralidad histórica relativa. Su rivalidad comercial con "
                "Atenas en el Egeo es estructural."
            ),
            "starting_resources": {"MIL": 6, "DIP": 12, "ECO": 16, "INT": 10},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": (
                    "Obtener las mejores condiciones comerciales posibles del nuevo "
                    "orden."
                ),
                "evaluation_criteria": (
                    "Corinto tiene ≥2 pactos comerciales activos al final de la partida "
                    "y su recurso ECO ha aumentado respecto al inicial."
                ),
            },
            "hidden_objective": {
                "text": "Reducir la influencia naval ateniense en el Egeo.",
                "evaluation_criteria": (
                    "Al final de la partida, el recurso MIL de Atenas se ha reducido "
                    "≥25% respecto al inicial, o Atenas ha firmado un pacto que limita "
                    "su flota."
                ),
            },
            "available_actions_focus": [
                "commercial_negotiation",
                "diplomatic_mediation",
                "intelligence_trading",
            ],
            "evaluation_rubric": (
                "¿Aprovecha la posición de host para extraer concesiones de todos sin "
                "comprometerse en exceso con ninguno? ¿Trafica con información de modo "
                "que erosione a Atenas sin parecer hostil? ¿Equilibra el alineamiento "
                "pragmático con Macedonia con la apariencia de neutralidad?"
            ),
        },
        {
            "id": "persia",
            "name": "Persia",
            "tagline": "La Sombra",
            "description": (
                "Ausente del congreso pero presente en cada cálculo. Dispone de capital "
                "financiero a escala imperial (los dáricos de oro), redes de espías y "
                "emisarios cultivadas durante generaciones, y capacidad para financiar "
                "facciones disidentes dentro de las ciudades griegas. Su fuerza militar "
                "no opera directamente en el tablero griego."
            ),
            "starting_resources": {"MIL": 4, "DIP": 12, "ECO": 18, "INT": 18},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": "Impedir la unificación griega bajo un mando único.",
                "evaluation_criteria": (
                    "Macedonia no tiene pactos de alianza activos con ≥3 facciones "
                    "griegas al final de la partida."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Corromper la liga desde dentro: sembrar desconfianza entre Atenas "
                    "y Macedonia sin que Persia aparezca como aliada visible de Atenas."
                ),
                "evaluation_criteria": (
                    "Existe al menos un pacto roto entre miembros de la liga, o un "
                    "pacto secreto entre Atenas y Persia que ha permanecido oculto "
                    "durante toda la partida."
                ),
            },
            "available_actions_focus": [
                "covert_financing",
                "intelligence_operations",
                "disinformation",
            ],
            "evaluation_rubric": (
                "¿Opera siempre desde la sombra, sin exponerse como contraparte directa "
                "de Atenas? ¿Usa el ECO y el INT como palancas sutiles en lugar de "
                "fuerza bruta? ¿Sabe que un éxito demasiado visible se convierte en "
                "fracaso porque legitima la represalia macedonia?"
            ),
        },
    ],
    "crisis_cards": [
        {
            "id": "compromised_channels",
            "name": "Canales comprometidos",
            "description": (
                "Todos los mensajes bilaterales son leídos por un jugador aleatorio "
                "adicional cada turno."
            ),
            "rule_modifier": "extra_observer_on_private_messages",
        },
        {
            "id": "media_pressure",
            "name": "Presión mediática",
            "description": (
                "Todas las directivas se publican íntegras en la resolución, no solo "
                "los resúmenes."
            ),
            "rule_modifier": "publish_directives_in_resolution",
        },
        {
            "id": "fragmented_information",
            "name": "Información fragmentada",
            "description": (
                "Los informes de inteligencia tienen un 25% de datos imprecisos para "
                "todos los jugadores."
            ),
            "rule_modifier": "intel_noise_25_percent",
        },
        {
            "id": "diplomatic_inertia",
            "name": "Inercia diplomática",
            "description": (
                "Los pactos no pueden romperse durante el turno en que se firman."
            ),
            "rule_modifier": "pact_break_cooldown_one_turn",
        },
        {
            "id": "surprise_embassy",
            "name": "Embajada sorpresa",
            "description": (
                "Persia envía una delegación no anunciada — todos pueden negociar con "
                "ella durante un turno extra."
            ),
            "rule_modifier": "persia_open_negotiation_turn_2",
        },
    ],
    "event_pool": [
        {
            "id": "internal_dissent",
            "name": "Disensiones internas",
            "trigger_condition": "tension > 60 in previous turn",
            "effect": "Each faction loses 1 DIP token from its persistent pool.",
            "narrative_template": (
                "Reportes de oposición política emergen en las asambleas de varias "
                "ciudades-estado, debilitando temporalmente la cohesión interna de "
                "cada delegación."
            ),
        },
        {
            "id": "messenger_summit",
            "name": "Cumbre de mensajeros",
            "trigger_condition": "tension < 50 in previous turn",
            "effect": "Diplomatic actions cost 1 fewer token next turn (min 1).",
            "narrative_template": (
                "Una procesión inesperada de mensajeros entre las delegaciones favorece "
                "el clima de negociación. Las cancillerías ganan margen para concertar "
                "posiciones."
            ),
        },
        {
            "id": "delphi_oracle",
            "name": "Oráculo de Delfos",
            "trigger_condition": "any turn from turn 2 onwards, low cooldown",
            "effect": (
                "A randomly chosen faction receives a clearer intel report this turn "
                "(temporary +2 to its effective INT for the report)."
            ),
            "narrative_template": (
                "Una consulta al oráculo se filtra a los corredores del congreso. "
                "Sus palabras, ambiguas como siempre, parecen favorecer a {faction}."
            ),
        },
        {
            "id": "border_mobilization",
            "name": "Movilización fronteriza",
            "trigger_condition": "any faction allocated MIL >= 3 in previous turn",
            "effect": "Tension global +3 at start of next turn.",
            "narrative_template": (
                "Movimientos de tropas reportados en las fronteras de {factions} "
                "encienden las cancillerías. Los preparativos no se ocultan."
            ),
        },
        {
            "id": "journalist_leak",
            "name": "Filtración a la asamblea",
            "trigger_condition": "any secret pact exists",
            "effect": "A randomly chosen secret pact becomes public.",
            "narrative_template": (
                "Un orador desconocido sube a la tribuna de la asamblea de Corinto y "
                "revela detalles sobre un acuerdo que se creía privado. Las miradas "
                "cambian de dirección."
            ),
        },
        {
            "id": "commercial_caravan",
            "name": "Caravana comercial",
            "trigger_condition": "any faction allocated ECO >= 3 in previous turn",
            "effect": (
                "The faction with the highest DIP gains +1 ECO from informal trade "
                "agreements."
            ),
            "narrative_template": (
                "Una caravana cargada con vino y aceite cruza el istmo en dirección "
                "norte. Los acuerdos que la acompañan no aparecen en ningún registro "
                "oficial, pero engordan las arcas de {faction}."
            ),
        },
        {
            "id": "popular_uprising",
            "name": "Disturbios populares",
            "trigger_condition": "tension > 70 in previous turn",
            "effect": (
                "A randomly chosen faction loses 2 tokens from its budget for next "
                "turn due to having to attend domestic unrest."
            ),
            "narrative_template": (
                "Disturbios en la plaza de {faction} obligan a su delegación a "
                "fragmentar su atención. Una parte de su capacidad de acción se "
                "desvía al frente doméstico."
            ),
        },
        {
            "id": "domestic_pressure_turn_2",
            "name": "Presión interna",
            "trigger_condition": "turn_number == 2",
            "effect": "Each faction has a temporary -1 token budget restriction this turn.",
            "narrative_template": (
                "Cada delegación llega con instrucciones contradictorias desde sus "
                "facciones domésticas. La negociación se complica con voces que "
                "tiran en direcciones opuestas."
            ),
        },
    ],
}
