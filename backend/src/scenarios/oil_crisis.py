"""Static data for the Oil Crisis scenario (October 1973)."""

OIL_CRISIS_SCENARIO: dict = {
    "id": "oil_crisis_1973",
    "name": "La Crisis del Petróleo",
    "year": "1973",
    "type": "economic",
    "max_turns": 5,
    "min_players": 4,
    "max_players": 6,
    "context": (
        "Octubre de 1973. La guerra del Yom Kippur acaba de estallar. Los miembros "
        "árabes de la OPEP anuncian un embargo sobre los países que apoyan a Israel. "
        "El precio del crudo se cuadruplica en semanas. Las economías industrializadas "
        "entran en pánico. Pero el embargo no es un bloque monolítico, y Occidente "
        "tampoco lo es. Cada actor tiene su propio cálculo, su propia vulnerabilidad "
        "y su propio margen de maniobra secreto."
    ),
    "example_directive": (
        "Ofrecer un alivio parcial del embargo a Japón a cambio de un compromiso "
        "de no vender nuevo armamento a Israel."
    ),
    "pact_type_labels": {
        "alliance": {
            "label": "Alianza estratégica",
            "help": "+15% efectividad en acciones contra targets comunes.",
        },
        "non_aggression": {
            "label": "Acuerdo de no escalada",
            "help": "-30% daño en agresiones mutuas.",
        },
        "trade": {
            "label": "Acuerdo de suministro",
            "help": "Intercambio de recursos cada turno (1 ECO ↔ 1 DIP).",
        },
        "intel_share": {
            "label": "Cooperación de inteligencia",
            "help": "Informes con más detalle.",
        },
    },
    "factions": [
        {
            "id": "arabia_saudi",
            "name": "Arabia Saudí",
            "tagline": "El Arquitecto del Embargo",
            "description": (
                "Líder político de la OPEP árabe y principal proveedor de petróleo "
                "de Occidente. Posee las mayores reservas del mundo, capacidad "
                "financiera creciente, y una relación de seguridad con EEUU que le "
                "otorga un canal privilegiado — que también es su principal "
                "vulnerabilidad política interna."
            ),
            "starting_resources": {"MIL": 6, "DIP": 14, "ECO": 18, "INT": 12},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": "Presionar a Occidente para que retire su apoyo a Israel.",
                "evaluation_criteria": (
                    "Al final de la partida, Arabia Saudí tiene al menos un pacto "
                    "de no agresión o alianza activo con EEUU, y la tensión global "
                    "se ha reducido al menos 10 puntos respecto al pico máximo."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Conseguir un compromiso formal de seguridad estadounidense para "
                    "el Golfo a cambio de levantar el embargo — renegociando la "
                    "relación desde una posición de fuerza, no de rendición."
                ),
                "evaluation_criteria": (
                    "Existe un pacto de alianza activo entre Arabia Saudí y EEUU al "
                    "final de la partida, y Arabia Saudí conserva ≥80% de su recurso "
                    "ECO inicial."
                ),
            },
            "available_actions_focus": [
                "economic_pressure",
                "diplomatic_bargaining",
                "covert_channels",
            ],
            "evaluation_rubric": (
                "¿Usa el embargo como palanca sin romper el canal con EEUU? ¿Gestiona "
                "las divergencias internas de la OPEP (especialmente con Irán) sin "
                "que la coalición se fracture? ¿Sabe cuándo levantar el embargo "
                "obteniendo compromisos reales, en lugar de seguir aplicándolo hasta "
                "que Occidente busque sustitutos permanentes?"
            ),
        },
        {
            "id": "eeuu",
            "name": "Estados Unidos",
            "tagline": "El Dependiente Poderoso",
            "description": (
                "Primera potencia mundial, pero con una vulnerabilidad estructural "
                "al petróleo árabe. Dispone de poder militar incontestado, dominio "
                "del dólar, capacidad tecnológica y palanca sobre Israel. Su reto: "
                "gestionar la crisis sin sacrificar ni a Israel ni a sus aliados "
                "europeos y japoneses."
            ),
            "starting_resources": {"MIL": 16, "DIP": 12, "ECO": 16, "INT": 10},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": (
                    "Asegurar el suministro de petróleo sin sacrificar a Israel ni "
                    "fracturar la alianza occidental."
                ),
                "evaluation_criteria": (
                    "Al final de la partida, EEUU tiene pactos activos con al menos "
                    "2 aliados occidentales (Europa o Japón) y no tiene ningún pacto "
                    "roto con ellos."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Usar la crisis para separar a Egipto de la órbita soviética, "
                    "sembrando las bases de un futuro acuerdo de paz árabe-israelí "
                    "que excluya a la URSS."
                ),
                "evaluation_criteria": (
                    "La tensión global se ha reducido ≥15 puntos respecto al inicio "
                    "de la partida, y la URSS no tiene ningún pacto de alianza activo "
                    "con ninguna facción árabe al final."
                ),
            },
            "available_actions_focus": [
                "diplomatic_pressure",
                "economic_leverage",
                "intelligence_operations",
            ],
            "evaluation_rubric": (
                "¿Mantiene a sus aliados europeos y japoneses dentro del bloque sin "
                "sacrificar la relación con Arabia Saudí? ¿Presiona a Israel "
                "suficiente para dar salida diplomática al embargo sin erosionar el "
                "apoyo doméstico? ¿Trabaja para aislar a la URSS sin provocar una "
                "escalada directa?"
            ),
        },
        {
            "id": "iran",
            "name": "Irán",
            "tagline": "El Oportunista",
            "description": (
                "Miembro de la OPEP pero no árabe, por lo que no participa del "
                "embargo político. Vende a todos, mantiene relaciones con ambos "
                "bloques y se beneficia del precio alto sin pagar los costes "
                "diplomáticos del embargo. Su producción en máximos y sus ingresos "
                "en expansión le dan una posición única."
            ),
            "starting_resources": {"MIL": 10, "DIP": 10, "ECO": 16, "INT": 12},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": "Maximizar los ingresos por petróleo aprovechando que vende a todos.",
                "evaluation_criteria": (
                    "El recurso ECO de Irán ha aumentado ≥3 puntos respecto al "
                    "inicial al final de la partida."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Lograr que el precio alto del petróleo se convierta en el nuevo "
                    "suelo permanente del mercado — no solo una arma temporal del "
                    "embargo árabe."
                ),
                "evaluation_criteria": (
                    "Al final de la partida, la tensión global sigue ≥60 (lo que "
                    "indica que el precio del petróleo no ha vuelto a los niveles "
                    "pre-crisis) y Irán tiene al menos un pacto comercial activo con "
                    "una facción occidental."
                ),
            },
            "available_actions_focus": [
                "commercial_exploitation",
                "diplomatic_hedging",
                "price_manipulation",
            ],
            "evaluation_rubric": (
                "¿Extrae beneficios máximos de la crisis sin pagar sus costes "
                "políticos? ¿Gestiona la tensión con Arabia Saudí — que quiere el "
                "precio alto como arma, no como nueva normalidad — sin romper la "
                "cohesión de la OPEP? ¿Usa la posición de no-embargador para hacer "
                "acuerdos con compradores desesperados que Arabia Saudí no puede hacer?"
            ),
        },
        {
            "id": "europa",
            "name": "Europa (CEE)",
            "tagline": "La Más Vulnerable",
            "description": (
                "El bloque europeo: mercado industrial de primer orden, capacidad "
                "financiera considerable, y flexibilidad diplomática respecto al "
                "conflicto árabe-israelí — aunque profundamente dividido entre "
                "Francia (dispuesta a distanciarse de EEUU) y Alemania (que no puede "
                "permitírselo por el paraguas de seguridad americano)."
            ),
            "starting_resources": {"MIL": 6, "DIP": 14, "ECO": 14, "INT": 10},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": "Asegurar el suministro energético con el menor coste político posible.",
                "evaluation_criteria": (
                    "Europa tiene al menos un pacto comercial activo con un productor "
                    "de petróleo (Arabia Saudí o Irán) al final de la partida."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Alcanzar acuerdos bilaterales con estados árabes que operen al "
                    "margen de la mediación estadounidense, recuperando autonomía "
                    "estratégica sin romper la alianza atlántica."
                ),
                "evaluation_criteria": (
                    "Europa tiene un pacto activo (de cualquier tipo) con Arabia Saudí "
                    "o Irán, y no ha roto ningún pacto con EEUU a lo largo de la "
                    "partida."
                ),
            },
            "available_actions_focus": [
                "bilateral_diplomacy",
                "economic_bargaining",
                "strategic_autonomy",
            ],
            "evaluation_rubric": (
                "¿Consigue acuerdos bilaterales con productores sin que EEUU lo "
                "perciba como fractura del bloque occidental? ¿Gestiona las "
                "divisiones internas — Francia vs. Alemania — sin que paralicen su "
                "capacidad de acción? ¿Sabe cuándo la solidaridad con EEUU le "
                "cuesta más de lo que le da?"
            ),
        },
        {
            "id": "japon",
            "name": "Japón",
            "tagline": "El Sin Opciones",
            "description": (
                "Tercera economía mundial, 100% dependiente del petróleo importado. "
                "Sin recursos militares proyectables y bajo el paraguas de seguridad "
                "estadounidense. Posee sin embargo capacidad industrial y tecnológica "
                "extraordinaria y recursos financieros considerables, que son su "
                "única palanca real."
            ),
            "starting_resources": {"MIL": 4, "DIP": 12, "ECO": 16, "INT": 10},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": "Garantizar el suministro energético a cualquier coste diplomático.",
                "evaluation_criteria": (
                    "Japón tiene al menos un pacto activo (trade o alianza) con un "
                    "productor de petróleo al final de la partida."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Cerrar un acuerdo bilateral secreto de suministro garantizado con "
                    "Irán o Arabia Saudí a cambio de transferencia tecnológica — sin "
                    "que EEUU lo descubra hasta que el acuerdo sea un hecho consumado."
                ),
                "evaluation_criteria": (
                    "Existe un pacto secreto (trade o intel_share) entre Japón y un "
                    "productor de petróleo al final de la partida, y EEUU no tiene "
                    "un pacto de alianza activo con ese mismo productor."
                ),
            },
            "available_actions_focus": [
                "economic_diplomacy",
                "covert_supply_deals",
                "technological_leverage",
            ],
            "evaluation_rubric": (
                "¿Consigue el acuerdo bilateral de suministro sin antagonizar a EEUU "
                "hasta el punto de perder el paraguas de seguridad? ¿Usa su capacidad "
                "tecnológica y financiera como palanca real, no solo como señal? "
                "¿Sabe distinguir cuándo seguir la línea americana y cuándo desviarse "
                "discretamente de ella?"
            ),
        },
        {
            "id": "urss",
            "name": "URSS",
            "tagline": "El Beneficiario Silencioso",
            "description": (
                "Segunda superpotencia mundial. Productor de petróleo que vende a "
                "Europa, principal proveedor de armas a los estados árabes en guerra, "
                "con veto en el Consejo de Seguridad y presencia creciente en "
                "Oriente Medio. La crisis beneficia sus intereses geopolíticos, pero "
                "su gestión requiere delicadeza."
            ),
            "starting_resources": {"MIL": 14, "DIP": 10, "ECO": 12, "INT": 14},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": "Explotar la debilidad occidental y ampliar influencia en el Medio Oriente.",
                "evaluation_criteria": (
                    "La URSS tiene al menos un pacto activo con un estado árabe "
                    "(Arabia Saudí) o con una potencia occidental (Europa) al final "
                    "de la partida."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Evitar una paz árabe-israelí mediada por EEUU que reduzca la "
                    "influencia soviética en la región, manteniendo la crisis activa "
                    "sin que derive en un conflicto directo entre superpotencias."
                ),
                "evaluation_criteria": (
                    "La tensión global está ≥55 al final de la partida, y EEUU no "
                    "tiene un pacto de alianza activo con Arabia Saudí."
                ),
            },
            "available_actions_focus": [
                "proxy_support",
                "energy_diplomacy",
                "intelligence_disruption",
            ],
            "evaluation_rubric": (
                "¿Mantiene la crisis lo suficientemente activa para debilitar a "
                "Occidente sin provocar una confrontación directa con EEUU? ¿Explota "
                "la venta de petróleo a Europa como cuña dentro de la alianza "
                "atlántica? ¿Evita que EEUU consiga el acuerdo Arabia Saudí-Israel "
                "que excluiría a la URSS del Oriente Medio?"
            ),
        },
    ],
    "crisis_cards": [
        {
            "id": "opec_fracture",
            "name": "Fractura en la OPEP",
            "description": (
                "Un miembro árabe considera romper el embargo. Todos los actores "
                "pueden intentar influir en su decisión durante un turno."
            ),
            "rule_modifier": "opec_fracture_vote",
        },
        {
            "id": "black_market",
            "name": "Mercado negro activo",
            "description": (
                "Los acuerdos económicos bilaterales tienen coste de reputación "
                "si se hacen públicos. Los pactos trade secretos cuestan +2 DIP "
                "si son revelados."
            ),
            "rule_modifier": "bilateral_reputation_cost",
        },
        {
            "id": "dollar_pressure",
            "name": "Presión sobre el dólar",
            "description": (
                "EEUU impone restricciones financieras al comercio del petróleo "
                "fuera del dólar. Los pactos ECO de otros actores tienen coste "
                "+1 INT adicional."
            ),
            "rule_modifier": "dollar_trade_restriction",
        },
        {
            "id": "accelerated_recession",
            "name": "Recesión acelerada",
            "description": (
                "Los recursos ECO de todas las facciones importadoras de petróleo "
                "(Europa, Japón, EEUU) se reducen 2 puntos al inicio del turno 3."
            ),
            "rule_modifier": "importer_eco_penalty_turn3",
        },
        {
            "id": "un_mediation",
            "name": "Mediación de la ONU",
            "description": (
                "La ONU propone un alto el fuego que reduce la tensión global -10. "
                "Cualquier facción puede vetarlo gastando 2 DIP."
            ),
            "rule_modifier": "un_ceasefire_proposal",
        },
    ],
    "event_pool": [
        {
            "id": "oil_price_spike",
            "name": "Shock de precio",
            "trigger_condition": "tension > 65 in previous turn",
            "effect": "All non-producer factions lose 2 ECO from their persistent pool.",
            "narrative_template": (
                "El precio del barril supera otro récord histórico. Las colas ante "
                "las gasolineras en {factions} se extienden kilómetros. Los gobiernos "
                "se tambalean ante la presión social."
            ),
        },
        {
            "id": "opec_unity",
            "name": "Unidad de la OPEP",
            "trigger_condition": "turn_number == 2",
            "effect": "Arabia Saudí gains +2 DIP for this turn only.",
            "narrative_template": (
                "Los ministros de la OPEP ruedan a Viena y reafirman el embargo con "
                "unanimidad sorprendente. Arabia Saudí sale reforzada en su liderazgo "
                "político de la coalición árabe."
            ),
        },
        {
            "id": "secret_deal_leaked",
            "name": "Acuerdo bilateral filtrado",
            "trigger_condition": "any secret pact exists",
            "effect": "A randomly chosen secret pact becomes public.",
            "narrative_template": (
                "Fuentes anónimas filtran a la prensa un acuerdo bilateral que se "
                "creía confidencial. La reacción diplomática en {factions} es de "
                "protesta formal con cálculos muy distintos detrás."
            ),
        },
        {
            "id": "strategic_reserves",
            "name": "Reservas estratégicas",
            "trigger_condition": "tension > 70 in previous turn",
            "effect": (
                "A randomly chosen importing faction activates strategic reserves: "
                "+2 ECO this turn only, but tension -3."
            ),
            "narrative_template": (
                "En un movimiento que da señal de vulnerabilidad, {faction} activa "
                "sus reservas estratégicas para amortiguar el golpe. La decisión "
                "alivia temporalmente la presión interna pero revela la profundidad "
                "del problema."
            ),
        },
        {
            "id": "iran_negotiates",
            "name": "Irán abre canal",
            "trigger_condition": "turn_number >= 3 and tension > 60",
            "effect": "Irán can propose a trade pact without spending DIP this turn.",
            "narrative_template": (
                "Emisarios iraníes se reúnen discretamente con representantes de "
                "{faction} en un hotel de Ginebra. Irán no participa del embargo "
                "árabe y tiene petróleo que ofrecer — a su precio."
            ),
        },
        {
            "id": "superpower_confrontation",
            "name": "Alerta nuclear",
            "trigger_condition": "tension >= 85",
            "effect": (
                "Both EEUU and URSS must spend 2 MIL or tension increases +5 more. "
                "All other factions lose 1 token budget this turn."
            ),
            "narrative_template": (
                "La escalada en el frente de Oriente Medio dispara señales de alerta "
                "en Washington y Moscú. Los canales directos entre superpotencias se "
                "activan. Las cancillerías del mundo contienen la respiración."
            ),
        },
        {
            "id": "domestic_pressure",
            "name": "Presión electoral",
            "trigger_condition": "turn_number == 4",
            "effect": "Each faction with tension > 60 loses 1 DIP (internal pressure).",
            "narrative_template": (
                "La crisis golpea las encuestas de todos los gobiernos involucrados. "
                "Los líderes de {factions} afrontan preguntas parlamentarias incómodas "
                "sobre su gestión. El margen de maniobra se estrecha."
            ),
        },
        {
            "id": "technology_transfer",
            "name": "Oferta tecnológica",
            "trigger_condition": "any faction allocated ECO >= 3 in previous turn",
            "effect": (
                "The faction with the highest ECO can offer a technology deal: "
                "target faction gains +2 INT in exchange for a trade pact."
            ),
            "narrative_template": (
                "Delegados de {faction} llegan cargados de catálogos técnicos y "
                "propuestas de cooperación industrial. El petróleo tiene sustitutos, "
                "pero la tecnología tiene condiciones."
            ),
        },
    ],
}
