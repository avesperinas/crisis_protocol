"""Static data for the Arctic Crisis scenario (2031)."""

ARCTIC_SCENARIO: dict = {
    "id": "arctic_2031",
    "name": "Crisis del Ártico",
    "year": "2031",
    "type": "hybrid",
    "max_turns": 6,
    "min_players": 4,
    "max_players": 6,
    "context": (
        "2031. El deshielo ártico ha superado todos los modelos. La Ruta del Mar del "
        "Norte es navegable nueve meses al año. Los fondos marinos contienen reservas "
        "de minerales críticos estimadas en billones de dólares. Rusia lleva años "
        "ampliando su presencia militar. China, sin territorio ártico, se declara "
        "'estado ártico próximo'. Un incidente entre un buque chino y la guardia "
        "costera canadiense ha colapsado el Consejo Ártico. Las potencias se reúnen "
        "para acordar un nuevo marco de gobernanza antes de que los hechos sobre el "
        "terreno lo hagan irreversible."
    ),
    "example_directive": (
        "Reforzar la presencia militar en la plataforma continental mientras "
        "propongo a China un acuerdo bilateral de explotación mineral."
    ),
    "pact_type_labels": {
        "alliance": {
            "label": "Pacto de cooperación ártica",
            "help": "+15% efectividad en acciones contra targets comunes.",
        },
        "non_aggression": {
            "label": "Acuerdo de no agresión territorial",
            "help": "-30% daño en agresiones mutuas.",
        },
        "trade": {
            "label": "Acuerdo de explotación conjunta",
            "help": "Intercambio de recursos cada turno (1 ECO ↔ 1 DIP).",
        },
        "intel_share": {
            "label": "Intercambio de inteligencia ártica",
            "help": "Informes con más detalle.",
        },
    },
    "factions": [
        {
            "id": "rusia",
            "name": "Rusia",
            "tagline": "El Ocupante de Facto",
            "description": (
                "Presencia militar dominante en el Ártico, infraestructura consolidada "
                "durante décadas, control efectivo de la mayor parte de la Ruta del "
                "Mar del Norte. Dispone de bases militares, rompehielos nucleares y "
                "reclamaciones territoriales sobre la plataforma continental que el "
                "resto rechaza pero no puede ignorar."
            ),
            "starting_resources": {"MIL": 18, "DIP": 8, "ECO": 12, "INT": 12},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": (
                    "Conseguir el reconocimiento legal de su plataforma continental "
                    "extendida y el control formal de la Ruta del Mar del Norte."
                ),
                "evaluation_criteria": (
                    "Al final de la partida, Rusia tiene al menos un pacto de alianza "
                    "o no agresión activo con China, y ningún otro actor tiene un "
                    "pacto de alianza activo con Canadá o EEUU que mencione la Ruta "
                    "del Mar del Norte."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Cerrar un acuerdo bilateral de extracción de minerales con China "
                    "antes de que se firme el tratado multilateral — fijando las "
                    "condiciones antes de que China gane posición autónoma en el Ártico."
                ),
                "evaluation_criteria": (
                    "Existe un pacto activo (trade o alianza) entre Rusia y China al "
                    "final de la partida, firmado antes del turno 4, y China no tiene "
                    "ningún pacto con EEUU ni Canadá."
                ),
            },
            "available_actions_focus": [
                "military_presence",
                "bilateral_extraction",
                "information_control",
            ],
            "evaluation_rubric": (
                "¿Usa la presencia militar como hecho consumado sin provocar una "
                "respuesta OTAN que consolide el bloque contrario? ¿Cierra el "
                "acuerdo con China antes de que China gane suficiente autonomía para "
                "negociar directamente con los occidentales? ¿Gestiona la tensión "
                "con Noruega — el mediador más peligroso — sin antagonizarla "
                "completamente?"
            ),
        },
        {
            "id": "eeuu",
            "name": "Estados Unidos",
            "tagline": "El Rezagado Alarmado",
            "description": (
                "Primera potencia militar global, pero con presencia ártica limitada "
                "respecto a Rusia. Lidera las alianzas occidentales, tiene capacidad "
                "tecnológica y financiera, y puede presionar a sus aliados — pero "
                "enfrenta un dilema estructural: para mantener a Canadá alineado, "
                "tendría que ceder en su propia doctrina de libertad de navegación."
            ),
            "starting_resources": {"MIL": 16, "DIP": 12, "ECO": 12, "INT": 10},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": "Garantizar la libertad de navegación y limitar la influencia rusa y china.",
                "evaluation_criteria": (
                    "Al final de la partida, EEUU tiene un pacto de alianza activo "
                    "con Canadá y China no tiene ningún pacto activo con Rusia."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Asegurar el alineamiento canadiense antes de la firma del "
                    "tratado, aunque eso implique concesiones privadas sobre el Paso "
                    "del Noroeste que contradicen la doctrina oficial estadounidense "
                    "de libertad de navegación."
                ),
                "evaluation_criteria": (
                    "Existe un pacto de alianza entre EEUU y Canadá al final de la "
                    "partida, y Canadá no tiene ningún pacto con China ni con Rusia."
                ),
            },
            "available_actions_focus": [
                "alliance_management",
                "china_containment",
                "diplomatic_pressure",
            ],
            "evaluation_rubric": (
                "¿Consigue el alineamiento canadiense sin tener que hacer públicas "
                "las concesiones que lo hacen posible? ¿Evita que Noruega se "
                "posicione como árbitro neutral reduciendo la influencia americana? "
                "¿Mantiene a Japón y Europa dentro del bloque sin que busquen "
                "acuerdos propios con China o Rusia?"
            ),
        },
        {
            "id": "canada",
            "name": "Canadá",
            "tagline": "El Soberano Disputado",
            "description": (
                "Estado ártico con soberanía sobre el Paso del Noroeste — que el "
                "resto del mundo no reconoce como aguas interiores. Posee reservas "
                "naturales relevantes, un argumento jurídico sólido basado en "
                "derechos indígenas, y la posición de aliado imprescindible de EEUU "
                "que le da más palanca de la que parece."
            ),
            "starting_resources": {"MIL": 6, "DIP": 14, "ECO": 10, "INT": 10},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": (
                    "Conseguir el reconocimiento del Paso del Noroeste como aguas "
                    "interiores canadienses en el tratado final."
                ),
                "evaluation_criteria": (
                    "Al final de la partida, Canadá tiene un pacto de alianza con "
                    "EEUU y ninguna facción tiene un pacto que explícitamente niegue "
                    "la soberanía canadiense (evaluado como: Canadá no ha roto ningún "
                    "pacto de no agresión durante la partida)."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Extraer concesiones bilaterales de EEUU en frentes pendientes "
                    "(energía, comercio, defensa continental) a cambio de alineamiento "
                    "político en la cumbre ártica."
                ),
                "evaluation_criteria": (
                    "Existe un pacto de alianza activo entre Canadá y EEUU firmado "
                    "antes del turno 4, y el recurso ECO de Canadá ha aumentado "
                    "respecto al inicial."
                ),
            },
            "available_actions_focus": [
                "legal_leverage",
                "bilateral_bargaining",
                "indigenous_rights_shield",
            ],
            "evaluation_rubric": (
                "¿Convierte la soberanía sobre el Paso del Noroeste en palanca "
                "concreta sin que EEUU la perciba como extorsión? ¿Usa los derechos "
                "indígenas como escudo jurídico legítimo en lugar de solo como "
                "táctica dilatoria? ¿Sabe cuándo el apoyo de EEUU tiene más valor "
                "que cualquier oferta de Rusia o China?"
            ),
        },
        {
            "id": "noruega",
            "name": "Noruega",
            "tagline": "El Mediador Creíble",
            "description": (
                "Estado ártico con décadas de experiencia técnica en el Ártico, "
                "credibilidad diplomática ganada como mediador en múltiples conflictos, "
                "y el mayor fondo soberano del mundo como respaldo financiero. Su "
                "membresía en la OTAN le da protección pero también le complica la "
                "neutralidad que necesita para mediar."
            ),
            "starting_resources": {"MIL": 6, "DIP": 18, "ECO": 12, "INT": 8},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": (
                    "Establecer un marco multilateral vinculante de gobernanza ártica "
                    "que incluya a todos los actores principales."
                ),
                "evaluation_criteria": (
                    "Al final de la partida, Noruega tiene pactos activos con al menos "
                    "3 facciones diferentes, incluyendo al menos una de cada bloque "
                    "(occidental y ruso-chino)."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Posicionarse como el mediador indispensable, lo que requiere "
                    "contradecir a EEUU en al menos un punto clave — aceptando el "
                    "estatus de observador de China — para ganarse la confianza del "
                    "bloque contrario."
                ),
                "evaluation_criteria": (
                    "Noruega tiene un pacto activo con China al final de la partida, "
                    "y también mantiene al menos un pacto con EEUU o Canadá."
                ),
            },
            "available_actions_focus": [
                "multilateral_mediation",
                "technical_expertise",
                "diplomatic_bridging",
            ],
            "evaluation_rubric": (
                "¿Acepta el coste de contradecir a EEUU en puntos específicos para "
                "ganar credibilidad como árbitro neutral? ¿Traduce su experiencia "
                "técnica ártica en propuestas concretas que otros no pueden rechazar "
                "sin coste reputacional? ¿Mantiene el equilibrio entre lealtad "
                "atlántica y rol de mediador sin quedar atrapada entre los dos?"
            ),
        },
        {
            "id": "china",
            "name": "China",
            "tagline": "El Reclamante sin Territorio",
            "description": (
                "Sin territorio ártico propio, pero con inversiones en infraestructura, "
                "relaciones con actores menores, capacidad financiera masiva y la "
                "declaración unilateral de 'estado ártico próximo'. Su objetivo es "
                "la legitimidad formal antes de que el tratado multilateral la excluya "
                "definitivamente del nuevo orden ártico."
            ),
            "starting_resources": {"MIL": 8, "DIP": 12, "ECO": 18, "INT": 14},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": (
                    "Obtener estatus formal de observador permanente en la gobernanza "
                    "ártica y acceso garantizado a rutas y recursos."
                ),
                "evaluation_criteria": (
                    "Al final de la partida, China tiene pactos activos con al menos "
                    "2 facciones árticas (Rusia, Canadá, Noruega o Groenlandia)."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Establecer una instalación de investigación permanente en "
                    "territorio disputado antes de la firma del tratado — un hecho "
                    "consumado que le dé presencia física en el Ártico que el "
                    "tratado tendrá que reconocer o ignorar."
                ),
                "evaluation_criteria": (
                    "China ha ejecutado al menos una acción MIL ofensiva exitosa "
                    "(no bloqueada) durante la partida, y al final tiene un pacto "
                    "activo con Rusia o Groenlandia."
                ),
            },
            "available_actions_focus": [
                "economic_investment",
                "fait_accompli",
                "legitimacy_building",
            ],
            "evaluation_rubric": (
                "¿Establece hechos sobre el terreno sin provocar una respuesta "
                "coordinada del bloque occidental que la excluya formalmente? "
                "¿Cierra el acuerdo con Rusia antes de que Rusia perciba el "
                "riesgo de crear un competidor ártico? ¿Usa su capacidad financiera "
                "para construir dependencias con actores menores (Groenlandia, "
                "Noruega) que le den votos en el proceso multilateral?"
            ),
        },
        {
            "id": "groenlandia",
            "name": "Groenlandia",
            "tagline": "El Comodín",
            "description": (
                "Territorio autónomo danés con reservas de minerales críticos de "
                "primera magnitud, posición geográfica estratégica y un movimiento "
                "de independencia en auge. Cada potencia quiere su alineamiento. "
                "Su mayor palanca es precisamente la neutralidad que todos intentan "
                "comprar."
            ),
            "starting_resources": {"MIL": 4, "DIP": 10, "ECO": 14, "INT": 8},
            "token_budget_per_turn": 3,
            "public_objective": {
                "text": "Maximizar los beneficios económicos de su posición estratégica.",
                "evaluation_criteria": (
                    "El recurso ECO de Groenlandia ha aumentado ≥4 puntos respecto "
                    "al inicial al final de la partida."
                ),
            },
            "hidden_objective": {
                "text": (
                    "Conseguir compromisos de inversión vinculantes de al menos dos "
                    "potencias de bloques distintos antes de declarar su posición "
                    "en el tratado — maximizando la competencia entre pretendientes "
                    "sin quemar a ninguno."
                ),
                "evaluation_criteria": (
                    "Groenlandia tiene pactos activos con al menos 2 facciones de "
                    "bloques distintos (uno occidental: EEUU, Canadá o Noruega; "
                    "y uno oriental: Rusia o China) al final de la partida."
                ),
            },
            "available_actions_focus": [
                "strategic_ambiguity",
                "investment_competition",
                "independence_leverage",
            ],
            "evaluation_rubric": (
                "¿Mantiene la ambigüedad estratégica lo suficiente como para que "
                "los pretendientes sigan compitiendo, sin que ninguno la perciba "
                "como definitivamente perdida? ¿Extrae compromisos reales de "
                "inversión antes de comprometerse con alguien? ¿Entiende cuándo "
                "la neutralidad se ha convertido en irrelevancia y es el momento "
                "de declarar una posición?"
            ),
        },
    ],
    "crisis_cards": [
        {
            "id": "arctic_storm",
            "name": "Tormenta ártica",
            "description": (
                "Turno 2: todas las acciones militares y logísticas tienen coste "
                "incrementado en 1 MIL adicional este turno."
            ),
            "rule_modifier": "military_cost_increase_turn2",
        },
        {
            "id": "seismic_data_leak",
            "name": "Filtración de datos sísmicos",
            "description": (
                "Se hacen públicas reservas de minerales mayores de lo esperado en "
                "zona disputada. Tensión global +8 de forma inmediata."
            ),
            "rule_modifier": "tension_spike_8",
        },
        {
            "id": "energy_grid_failure",
            "name": "Crisis energética global",
            "description": (
                "Un fallo en infraestructura crítica europea eleva la urgencia: "
                "todas las facciones dependientes de energía pierden 1 ECO este turno."
            ),
            "rule_modifier": "energy_importer_eco_penalty",
        },
        {
            "id": "indigenous_veto",
            "name": "Veto indígena",
            "description": (
                "Comunidades indígenas árticas impugnan un acuerdo. Canadá puede "
                "bloquear cualquier pacto que le involucre sin coste DIP este turno."
            ),
            "rule_modifier": "canada_pact_veto_turn",
        },
        {
            "id": "military_incident",
            "name": "Incidente naval",
            "description": (
                "Tensión militar súbita: todas las facciones con MIL < 8 pierden "
                "1 token de presupuesto este turno por medidas de seguridad de "
                "emergencia."
            ),
            "rule_modifier": "low_mil_budget_penalty",
        },
    ],
    "event_pool": [
        {
            "id": "navigation_incident",
            "name": "Incidente de navegación",
            "trigger_condition": "any faction allocated MIL >= 3 in previous turn",
            "effect": "Tension global +5. The faction with highest MIL must justify.",
            "narrative_template": (
                "Un buque de {faction} cruza una zona de exclusión declarada por "
                "otro actor. Las comunicaciones de emergencia se multiplican. "
                "Los portavoces preparan declaraciones que no dicen nada."
            ),
        },
        {
            "id": "mineral_discovery",
            "name": "Descubrimiento de yacimiento",
            "trigger_condition": "turn_number >= 2",
            "effect": (
                "A randomly chosen faction with territorial claims gains +2 ECO. "
                "Tension +3 globally."
            ),
            "narrative_template": (
                "Imágenes satelitales revelan un yacimiento de tierras raras en "
                "la plataforma reclamada por {faction}. El anuncio genera reacciones "
                "inmediatas en todas las cancillerías involucradas."
            ),
        },
        {
            "id": "climate_pressure",
            "name": "Presión climática",
            "trigger_condition": "tension < 50 in previous turn",
            "effect": (
                "All factions gain +1 DIP for 'climate diplomacy' framing this turn."
            ),
            "narrative_template": (
                "Las imágenes del deshielo ártico dominan los medios globales. "
                "La presión de la opinión pública obliga a todas las delegaciones "
                "a adoptar un lenguaje más cooperativo — al menos en público."
            ),
        },
        {
            "id": "china_infrastructure",
            "name": "Infraestructura china anunciada",
            "trigger_condition": "turn_number == 3",
            "effect": (
                "China gains +2 ECO. EEUU and Canada must respond or lose 1 DIP each."
            ),
            "narrative_template": (
                "Beijing anuncia la financiación de una nueva estación de "
                "investigación en {region}. El proyecto incluye un muelle de doble "
                "uso. Las reacciones se producen en cuestión de horas."
            ),
        },
        {
            "id": "nato_coordination",
            "name": "Coordinación OTAN",
            "trigger_condition": "any OTAN faction has alliance pact with another OTAN faction",
            "effect": "EEUU, Canada, and Noruega each gain +1 MIL temporarily.",
            "narrative_template": (
                "Una reunión de urgencia en el cuartel general de la OTAN produce "
                "una declaración conjunta sobre la soberanía ártica. Los efectivos "
                "de los aliados en la región aumentan discretamente."
            ),
        },
        {
            "id": "russian_veto_threat",
            "name": "Amenaza de veto ruso",
            "trigger_condition": "tension > 65 in previous turn",
            "effect": "Rusia can cancel one multilateral pact proposed this turn without DIP cost.",
            "narrative_template": (
                "Moscú hace circular entre delegaciones una nota verbal: ciertos "
                "arreglos multilaterales serán considerados contrarios a los intereses "
                "de seguridad rusa. La nota es suficientemente vaga para generar "
                "incertidumbre y suficientemente concreta para ser una amenaza."
            ),
        },
        {
            "id": "greenland_election",
            "name": "Elecciones en Groenlandia",
            "trigger_condition": "turn_number == 4",
            "effect": (
                "Groenlandia gains +2 DIP. Other factions must re-evaluate any pacts "
                "with Greenland (they remain active but must be reconfirmed next turn)."
            ),
            "narrative_template": (
                "Las elecciones en Nuuk producen un nuevo gobierno con mandato "
                "explícito de maximizar la autonomía y los beneficios económicos. "
                "Las embajadas actualizan sus análisis sobre Groenlandia."
            ),
        },
        {
            "id": "tech_breakthrough",
            "name": "Ruptura tecnológica",
            "trigger_condition": "any faction allocated INT >= 3 in previous turn",
            "effect": (
                "The faction with the highest INT gains a free intel report about "
                "any one other faction's current resource levels."
            ),
            "narrative_template": (
                "Satélites de nueva generación y análisis de señales de {faction} "
                "producen un informe de inteligencia más detallado de lo esperado. "
                "La ventaja de información es temporal, pero puede ser decisiva."
            ),
        },
    ],
}
