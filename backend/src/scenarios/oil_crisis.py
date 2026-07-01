"""Static data for the Oil Crisis scenario (October 1973).

User-facing strings are wrapped in `L(es, en)` and resolved to a single
language at load time. Logic-only fields (ids, resources, rule modifiers,
trigger conditions) stay as plain values.
"""

from src.scenarios.localize import L

OIL_CRISIS_SCENARIO: dict = {
    "id": "oil_crisis_1973",
    "name": L("La Crisis del Petróleo", "The Oil Crisis"),
    "year": "1973",
    "type": "economic",
    "max_turns": 5,
    "min_players": 4,
    "max_players": 6,
    "context": L(
        "Octubre de 1973. La guerra del Yom Kippur acaba de estallar. Los miembros "
        "árabes de la OPEP anuncian un embargo sobre los países que apoyan a Israel. "
        "El precio del crudo se cuadruplica en semanas. Las economías industrializadas "
        "entran en pánico. Pero el embargo no es un bloque monolítico, y Occidente "
        "tampoco lo es. Cada actor tiene su propio cálculo, su propia vulnerabilidad "
        "y su propio margen de maniobra secreto.",
        "October 1973. The Yom Kippur War has just broken out. The Arab members of "
        "OPEC announce an embargo against the countries that support Israel. The price "
        "of crude quadruples in weeks. The industrialized economies panic. But the "
        "embargo is not a monolithic bloc, and neither is the West. Each actor has its "
        "own calculus, its own vulnerability and its own secret room to maneuver.",
    ),
    "example_directive": L(
        "Ofrecer un alivio parcial del embargo a Japón a cambio de un compromiso "
        "de no vender nuevo armamento a Israel.",
        "Offer Japan partial relief from the embargo in exchange for a commitment not "
        "to sell new weapons to Israel.",
    ),
    "pact_type_labels": {
        "alliance": {
            "label": L("Alianza estratégica", "Strategic alliance"),
            "help": L(
                "+15% efectividad en acciones contra targets comunes.",
                "+15% effectiveness on actions against shared targets.",
            ),
        },
        "non_aggression": {
            "label": L("Acuerdo de no escalada", "De-escalation accord"),
            "help": L("-30% daño en agresiones mutuas.", "-30% damage on mutual aggression."),
        },
        "trade": {
            "label": L("Acuerdo de suministro", "Supply agreement"),
            "help": L(
                "Intercambio de recursos cada turno (1 ECO ↔ 1 DIP).",
                "Resource exchange each turn (1 ECO ↔ 1 DIP).",
            ),
        },
        "intel_share": {
            "label": L("Cooperación de inteligencia", "Intelligence cooperation"),
            "help": L("Informes con más detalle.", "More detailed reports."),
        },
    },
    "factions": [
        {
            "id": "arabia_saudi",
            "name": L("Arabia Saudí", "Saudi Arabia"),
            "tagline": L("El Arquitecto del Embargo", "The Architect of the Embargo"),
            "description": L(
                "Líder político de la OPEP árabe y principal proveedor de petróleo "
                "de Occidente. Posee las mayores reservas del mundo, capacidad "
                "financiera creciente, y una relación de seguridad con EEUU que le "
                "otorga un canal privilegiado — que también es su principal "
                "vulnerabilidad política interna.",
                "Political leader of Arab OPEC and the West's main oil supplier. It "
                "holds the world's largest reserves, growing financial capacity, and a "
                "security relationship with the USA that gives it a privileged channel — "
                "which is also its main internal political vulnerability.",
            ),
            "starting_resources": {"MIL": 6, "DIP": 14, "ECO": 18, "INT": 12},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Presionar a Occidente para que retire su apoyo a Israel.",
                    "Pressure the West into withdrawing its support for Israel.",
                ),
                "evaluation_criteria": L(
                    "Al final de la partida, Arabia Saudí tiene al menos un pacto "
                    "de no agresión o alianza activo con EEUU, y la tensión global "
                    "se ha reducido al menos 10 puntos respecto al pico máximo.",
                    "By the end of the game, Saudi Arabia holds at least one active "
                    "non-aggression or alliance pact with the USA, and global tension "
                    "has fallen at least 10 points from its peak.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Conseguir un compromiso formal de seguridad estadounidense para "
                    "el Golfo a cambio de levantar el embargo — renegociando la "
                    "relación desde una posición de fuerza, no de rendición.",
                    "Secure a formal U.S. security commitment for the Gulf in exchange "
                    "for lifting the embargo — renegotiating the relationship from a "
                    "position of strength, not surrender.",
                ),
                "evaluation_criteria": L(
                    "Existe un pacto de alianza activo entre Arabia Saudí y EEUU al "
                    "final de la partida, y Arabia Saudí conserva ≥80% de su recurso "
                    "ECO inicial.",
                    "An active alliance pact exists between Saudi Arabia and the USA at "
                    "the end of the game, and Saudi Arabia retains ≥80% of its starting "
                    "ECO resource.",
                ),
            },
            "available_actions_focus": [
                "economic_pressure",
                "diplomatic_bargaining",
                "covert_channels",
            ],
            "evaluation_rubric": L(
                "¿Usa el embargo como palanca sin romper el canal con EEUU? ¿Gestiona "
                "las divergencias internas de la OPEP (especialmente con Irán) sin "
                "que la coalición se fracture? ¿Sabe cuándo levantar el embargo "
                "obteniendo compromisos reales, en lugar de seguir aplicándolo hasta "
                "que Occidente busque sustitutos permanentes?",
                "Does it use the embargo as leverage without breaking the channel with "
                "the USA? Does it manage OPEC's internal divergences (especially with "
                "Iran) without the coalition fracturing? Does it know when to lift the "
                "embargo in return for real commitments, rather than pressing it until "
                "the West seeks permanent substitutes?",
            ),
        },
        {
            "id": "eeuu",
            "name": L("Estados Unidos", "United States"),
            "tagline": L("El Dependiente Poderoso", "The Powerful Dependent"),
            "description": L(
                "Primera potencia mundial, pero con una vulnerabilidad estructural "
                "al petróleo árabe. Dispone de poder militar incontestado, dominio "
                "del dólar, capacidad tecnológica y palanca sobre Israel. Su reto: "
                "gestionar la crisis sin sacrificar ni a Israel ni a sus aliados "
                "europeos y japoneses.",
                "The foremost world power, but with a structural vulnerability to Arab "
                "oil. It commands uncontested military power, dollar dominance, "
                "technological capacity and leverage over Israel. Its challenge: to "
                "manage the crisis without sacrificing either Israel or its European "
                "and Japanese allies.",
            ),
            "starting_resources": {"MIL": 16, "DIP": 12, "ECO": 16, "INT": 10},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Asegurar el suministro de petróleo sin sacrificar a Israel ni "
                    "fracturar la alianza occidental.",
                    "Secure the oil supply without sacrificing Israel or fracturing the "
                    "Western alliance.",
                ),
                "evaluation_criteria": L(
                    "Al final de la partida, EEUU tiene pactos activos con al menos "
                    "2 aliados occidentales (Europa o Japón) y no tiene ningún pacto "
                    "roto con ellos.",
                    "By the end of the game, the USA holds active pacts with at least 2 "
                    "Western allies (Europe or Japan) and has no broken pact with them.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Usar la crisis para separar a Egipto de la órbita soviética, "
                    "sembrando las bases de un futuro acuerdo de paz árabe-israelí "
                    "que excluya a la URSS.",
                    "Use the crisis to pull Egypt out of the Soviet orbit, laying the "
                    "groundwork for a future Arab-Israeli peace deal that excludes the "
                    "USSR.",
                ),
                "evaluation_criteria": L(
                    "La tensión global se ha reducido ≥15 puntos respecto al inicio "
                    "de la partida, y la URSS no tiene ningún pacto de alianza activo "
                    "con ninguna facción árabe al final.",
                    "Global tension has fallen ≥15 points from the start of the game, "
                    "and the USSR holds no active alliance pact with any Arab faction at "
                    "the end.",
                ),
            },
            "available_actions_focus": [
                "diplomatic_pressure",
                "economic_leverage",
                "intelligence_operations",
            ],
            "evaluation_rubric": L(
                "¿Mantiene a sus aliados europeos y japoneses dentro del bloque sin "
                "sacrificar la relación con Arabia Saudí? ¿Presiona a Israel "
                "suficiente para dar salida diplomática al embargo sin erosionar el "
                "apoyo doméstico? ¿Trabaja para aislar a la URSS sin provocar una "
                "escalada directa?",
                "Does it keep its European and Japanese allies inside the bloc without "
                "sacrificing the relationship with Saudi Arabia? Does it press Israel "
                "enough to give the embargo a diplomatic exit without eroding domestic "
                "support? Does it work to isolate the USSR without provoking a direct "
                "escalation?",
            ),
        },
        {
            "id": "iran",
            "name": L("Irán", "Iran"),
            "tagline": L("El Oportunista", "The Opportunist"),
            "description": L(
                "Miembro de la OPEP pero no árabe, por lo que no participa del "
                "embargo político. Vende a todos, mantiene relaciones con ambos "
                "bloques y se beneficia del precio alto sin pagar los costes "
                "diplomáticos del embargo. Su producción en máximos y sus ingresos "
                "en expansión le dan una posición única.",
                "An OPEC member but not Arab, so it does not join the political "
                "embargo. It sells to everyone, keeps relations with both blocs and "
                "profits from high prices without paying the embargo's diplomatic "
                "costs. Its production at record highs and expanding revenues give it a "
                "unique position.",
            ),
            "starting_resources": {"MIL": 10, "DIP": 10, "ECO": 16, "INT": 12},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": L(
                    "Maximizar los ingresos por petróleo aprovechando que vende a todos.",
                    "Maximize oil revenues by taking advantage of selling to everyone.",
                ),
                "evaluation_criteria": L(
                    "El recurso ECO de Irán ha aumentado ≥3 puntos respecto al "
                    "inicial al final de la partida.",
                    "Iran's ECO resource has increased ≥3 points over its starting value "
                    "by the end of the game.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Lograr que el precio alto del petróleo se convierta en el nuevo "
                    "suelo permanente del mercado — no solo una arma temporal del "
                    "embargo árabe.",
                    "Get the high oil price to become the market's new permanent floor — "
                    "not just a temporary weapon of the Arab embargo.",
                ),
                "evaluation_criteria": L(
                    "Al final de la partida, la tensión global sigue ≥60 (lo que "
                    "indica que el precio del petróleo no ha vuelto a los niveles "
                    "pre-crisis) y Irán tiene al menos un pacto comercial activo con "
                    "una facción occidental.",
                    "At the end of the game, global tension is still ≥60 (indicating the "
                    "oil price has not returned to pre-crisis levels) and Iran holds at "
                    "least one active trade pact with a Western faction.",
                ),
            },
            "available_actions_focus": [
                "commercial_exploitation",
                "diplomatic_hedging",
                "price_manipulation",
            ],
            "evaluation_rubric": L(
                "¿Extrae beneficios máximos de la crisis sin pagar sus costes "
                "políticos? ¿Gestiona la tensión con Arabia Saudí — que quiere el "
                "precio alto como arma, no como nueva normalidad — sin romper la "
                "cohesión de la OPEP? ¿Usa la posición de no-embargador para hacer "
                "acuerdos con compradores desesperados que Arabia Saudí no puede hacer?",
                "Does it extract maximum benefit from the crisis without paying its "
                "political costs? Does it manage tension with Saudi Arabia — which wants "
                "high prices as a weapon, not a new normal — without breaking OPEC "
                "cohesion? Does it use its non-embargoer position to strike deals with "
                "desperate buyers that Saudi Arabia cannot?",
            ),
        },
        {
            "id": "europa",
            "name": L("Europa (CEE)", "Europe (EEC)"),
            "tagline": L("La Más Vulnerable", "The Most Vulnerable"),
            "description": L(
                "El bloque europeo: mercado industrial de primer orden, capacidad "
                "financiera considerable, y flexibilidad diplomática respecto al "
                "conflicto árabe-israelí — aunque profundamente dividido entre "
                "Francia (dispuesta a distanciarse de EEUU) y Alemania (que no puede "
                "permitírselo por el paraguas de seguridad americano).",
                "The European bloc: a first-rate industrial market, considerable "
                "financial capacity, and diplomatic flexibility on the Arab-Israeli "
                "conflict — though deeply divided between France (willing to distance "
                "itself from the USA) and Germany (which cannot afford to, given the "
                "American security umbrella).",
            ),
            "starting_resources": {"MIL": 6, "DIP": 14, "ECO": 14, "INT": 10},
            "token_budget_per_turn": 5,
            "public_objective": {
                "text": L(
                    "Asegurar el suministro energético con el menor coste político posible.",
                    "Secure the energy supply at the lowest possible political cost.",
                ),
                "evaluation_criteria": L(
                    "Europa tiene al menos un pacto comercial activo con un productor "
                    "de petróleo (Arabia Saudí o Irán) al final de la partida.",
                    "Europe holds at least one active trade pact with an oil producer "
                    "(Saudi Arabia or Iran) at the end of the game.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Alcanzar acuerdos bilaterales con estados árabes que operen al "
                    "margen de la mediación estadounidense, recuperando autonomía "
                    "estratégica sin romper la alianza atlántica.",
                    "Reach bilateral deals with Arab states that operate outside U.S. "
                    "mediation, recovering strategic autonomy without breaking the "
                    "Atlantic alliance.",
                ),
                "evaluation_criteria": L(
                    "Europa tiene un pacto activo (de cualquier tipo) con Arabia Saudí "
                    "o Irán, y no ha roto ningún pacto con EEUU a lo largo de la "
                    "partida.",
                    "Europe holds an active pact (of any type) with Saudi Arabia or "
                    "Iran, and has not broken any pact with the USA over the course of "
                    "the game.",
                ),
            },
            "available_actions_focus": [
                "bilateral_diplomacy",
                "economic_bargaining",
                "strategic_autonomy",
            ],
            "evaluation_rubric": L(
                "¿Consigue acuerdos bilaterales con productores sin que EEUU lo "
                "perciba como fractura del bloque occidental? ¿Gestiona las "
                "divisiones internas — Francia vs. Alemania — sin que paralicen su "
                "capacidad de acción? ¿Sabe cuándo la solidaridad con EEUU le "
                "cuesta más de lo que le da?",
                "Does it reach bilateral deals with producers without the USA "
                "perceiving it as a fracture of the Western bloc? Does it manage its "
                "internal divisions — France vs. Germany — without them paralyzing its "
                "capacity to act? Does it know when solidarity with the USA costs it "
                "more than it gives?",
            ),
        },
        {
            "id": "japon",
            "name": L("Japón", "Japan"),
            "tagline": L("El Sin Opciones", "The One Without Options"),
            "description": L(
                "Tercera economía mundial, 100% dependiente del petróleo importado. "
                "Sin recursos militares proyectables y bajo el paraguas de seguridad "
                "estadounidense. Posee sin embargo capacidad industrial y tecnológica "
                "extraordinaria y recursos financieros considerables, que son su "
                "única palanca real.",
                "The world's third-largest economy, 100% dependent on imported oil. "
                "Without projectable military resources and under the American security "
                "umbrella. It has, however, extraordinary industrial and technological "
                "capacity and considerable financial resources, which are its only real "
                "leverage.",
            ),
            "starting_resources": {"MIL": 4, "DIP": 12, "ECO": 16, "INT": 10},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": L(
                    "Garantizar el suministro energético a cualquier coste diplomático.",
                    "Guarantee the energy supply at any diplomatic cost.",
                ),
                "evaluation_criteria": L(
                    "Japón tiene al menos un pacto activo (trade o alianza) con un "
                    "productor de petróleo al final de la partida.",
                    "Japan holds at least one active pact (trade or alliance) with an "
                    "oil producer at the end of the game.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Cerrar un acuerdo bilateral secreto de suministro garantizado con "
                    "Irán o Arabia Saudí a cambio de transferencia tecnológica — sin "
                    "que EEUU lo descubra hasta que el acuerdo sea un hecho consumado.",
                    "Close a secret bilateral guaranteed-supply deal with Iran or Saudi "
                    "Arabia in exchange for technology transfer — without the USA "
                    "finding out until the deal is a fait accompli.",
                ),
                "evaluation_criteria": L(
                    "Existe un pacto secreto (trade o intel_share) entre Japón y un "
                    "productor de petróleo al final de la partida, y EEUU no tiene "
                    "un pacto de alianza activo con ese mismo productor.",
                    "A secret pact (trade or intel_share) exists between Japan and an "
                    "oil producer at the end of the game, and the USA holds no active "
                    "alliance pact with that same producer.",
                ),
            },
            "available_actions_focus": [
                "economic_diplomacy",
                "covert_supply_deals",
                "technological_leverage",
            ],
            "evaluation_rubric": L(
                "¿Consigue el acuerdo bilateral de suministro sin antagonizar a EEUU "
                "hasta el punto de perder el paraguas de seguridad? ¿Usa su capacidad "
                "tecnológica y financiera como palanca real, no solo como señal? "
                "¿Sabe distinguir cuándo seguir la línea americana y cuándo desviarse "
                "discretamente de ella?",
                "Does it secure the bilateral supply deal without antagonizing the USA "
                "to the point of losing the security umbrella? Does it use its "
                "technological and financial capacity as real leverage, not just a "
                "signal? Does it know when to follow the American line and when to "
                "quietly deviate from it?",
            ),
        },
        {
            "id": "urss",
            "name": L("URSS", "USSR"),
            "tagline": L("El Beneficiario Silencioso", "The Silent Beneficiary"),
            "description": L(
                "Segunda superpotencia mundial. Productor de petróleo que vende a "
                "Europa, principal proveedor de armas a los estados árabes en guerra, "
                "con veto en el Consejo de Seguridad y presencia creciente en "
                "Oriente Medio. La crisis beneficia sus intereses geopolíticos, pero "
                "su gestión requiere delicadeza.",
                "The world's second superpower. An oil producer that sells to Europe, "
                "the main arms supplier to the Arab states at war, with a Security "
                "Council veto and a growing presence in the Middle East. The crisis "
                "serves its geopolitical interests, but managing it requires finesse.",
            ),
            "starting_resources": {"MIL": 14, "DIP": 10, "ECO": 12, "INT": 14},
            "token_budget_per_turn": 4,
            "public_objective": {
                "text": L(
                    "Explotar la debilidad occidental y ampliar influencia en el Medio Oriente.",
                    "Exploit Western weakness and expand influence in the Middle East.",
                ),
                "evaluation_criteria": L(
                    "La URSS tiene al menos un pacto activo con un estado árabe "
                    "(Arabia Saudí) o con una potencia occidental (Europa) al final "
                    "de la partida.",
                    "The USSR holds at least one active pact with an Arab state (Saudi "
                    "Arabia) or a Western power (Europe) at the end of the game.",
                ),
            },
            "hidden_objective": {
                "text": L(
                    "Evitar una paz árabe-israelí mediada por EEUU que reduzca la "
                    "influencia soviética en la región, manteniendo la crisis activa "
                    "sin que derive en un conflicto directo entre superpotencias.",
                    "Prevent a U.S.-brokered Arab-Israeli peace that would reduce Soviet "
                    "influence in the region, keeping the crisis alive without it "
                    "sliding into a direct superpower conflict.",
                ),
                "evaluation_criteria": L(
                    "La tensión global está ≥55 al final de la partida, y EEUU no "
                    "tiene un pacto de alianza activo con Arabia Saudí.",
                    "Global tension is ≥55 at the end of the game, and the USA holds no "
                    "active alliance pact with Saudi Arabia.",
                ),
            },
            "available_actions_focus": [
                "proxy_support",
                "energy_diplomacy",
                "intelligence_disruption",
            ],
            "evaluation_rubric": L(
                "¿Mantiene la crisis lo suficientemente activa para debilitar a "
                "Occidente sin provocar una confrontación directa con EEUU? ¿Explota "
                "la venta de petróleo a Europa como cuña dentro de la alianza "
                "atlántica? ¿Evita que EEUU consiga el acuerdo Arabia Saudí-Israel "
                "que excluiría a la URSS del Oriente Medio?",
                "Does it keep the crisis active enough to weaken the West without "
                "provoking a direct confrontation with the USA? Does it exploit its oil "
                "sales to Europe as a wedge inside the Atlantic alliance? Does it "
                "prevent the USA from landing the Saudi-Israeli deal that would exclude "
                "the USSR from the Middle East?",
            ),
        },
    ],
    "crisis_cards": [
        {
            "id": "opec_fracture",
            "name": L("Fractura en la OPEP", "OPEC fracture"),
            "description": L(
                "Un miembro árabe considera romper el embargo. Todos los actores "
                "pueden intentar influir en su decisión durante un turno.",
                "An Arab member considers breaking the embargo. All actors may try to "
                "influence its decision for one turn.",
            ),
            "rule_modifier": "opec_fracture_vote",
        },
        {
            "id": "black_market",
            "name": L("Mercado negro activo", "Active black market"),
            "description": L(
                "Los acuerdos económicos bilaterales tienen coste de reputación "
                "si se hacen públicos. Los pactos trade secretos cuestan +2 DIP "
                "si son revelados.",
                "Bilateral economic deals carry a reputation cost if made public. "
                "Secret trade pacts cost +2 DIP if revealed.",
            ),
            "rule_modifier": "bilateral_reputation_cost",
        },
        {
            "id": "dollar_pressure",
            "name": L("Presión sobre el dólar", "Pressure on the dollar"),
            "description": L(
                "EEUU impone restricciones financieras al comercio del petróleo "
                "fuera del dólar. Los pactos ECO de otros actores tienen coste "
                "+1 INT adicional.",
                "The USA imposes financial restrictions on oil trade outside the "
                "dollar. Other actors' ECO pacts cost +1 additional INT.",
            ),
            "rule_modifier": "dollar_trade_restriction",
        },
        {
            "id": "accelerated_recession",
            "name": L("Recesión acelerada", "Accelerated recession"),
            "description": L(
                "Los recursos ECO de todas las facciones importadoras de petróleo "
                "(Europa, Japón, EEUU) se reducen 2 puntos al inicio del turno 3.",
                "The ECO resources of all oil-importing factions (Europe, Japan, USA) "
                "drop by 2 points at the start of turn 3.",
            ),
            "rule_modifier": "importer_eco_penalty_turn3",
        },
        {
            "id": "un_mediation",
            "name": L("Mediación de la ONU", "UN mediation"),
            "description": L(
                "La ONU propone un alto el fuego que reduce la tensión global -10. "
                "Cualquier facción puede vetarlo gastando 2 DIP.",
                "The UN proposes a ceasefire that reduces global tension by -10. Any "
                "faction can veto it by spending 2 DIP.",
            ),
            "rule_modifier": "un_ceasefire_proposal",
        },
    ],
    "event_pool": [
        {
            "id": "oil_price_spike",
            "name": L("Shock de precio", "Price shock"),
            "trigger_condition": "tension > 65 in previous turn",
            "effect": "All non-producer factions lose 2 ECO from their persistent pool.",
            "narrative_template": L(
                "El precio del barril supera otro récord histórico. Las colas ante "
                "las gasolineras en {factions} se extienden kilómetros. Los gobiernos "
                "se tambalean ante la presión social.",
                "The price of a barrel breaks another record. The lines at the gas "
                "stations in {factions} stretch for miles. Governments wobble under "
                "social pressure.",
            ),
        },
        {
            "id": "opec_unity",
            "name": L("Unidad de la OPEP", "OPEC unity"),
            "trigger_condition": "turn_number == 2",
            "effect": "Arabia Saudí gains +2 DIP for this turn only.",
            "narrative_template": L(
                "Los ministros de la OPEP ruedan a Viena y reafirman el embargo con "
                "unanimidad sorprendente. Arabia Saudí sale reforzada en su liderazgo "
                "político de la coalición árabe.",
                "OPEC ministers converge on Vienna and reaffirm the embargo with "
                "surprising unanimity. Saudi Arabia emerges strengthened in its "
                "political leadership of the Arab coalition.",
            ),
        },
        {
            "id": "secret_deal_leaked",
            "name": L("Acuerdo bilateral filtrado", "Bilateral deal leaked"),
            "trigger_condition": "any secret pact exists",
            "effect": "A randomly chosen secret pact becomes public.",
            "narrative_template": L(
                "Fuentes anónimas filtran a la prensa un acuerdo bilateral que se "
                "creía confidencial. La reacción diplomática en {factions} es de "
                "protesta formal con cálculos muy distintos detrás.",
                "Anonymous sources leak to the press a bilateral deal believed to be "
                "confidential. The diplomatic reaction in {factions} is one of formal "
                "protest with very different calculations behind it.",
            ),
        },
        {
            "id": "strategic_reserves",
            "name": L("Reservas estratégicas", "Strategic reserves"),
            "trigger_condition": "tension > 70 in previous turn",
            "effect": (
                "A randomly chosen importing faction activates strategic reserves: "
                "+2 ECO this turn only, but tension -3."
            ),
            "narrative_template": L(
                "En un movimiento que da señal de vulnerabilidad, {faction} activa "
                "sus reservas estratégicas para amortiguar el golpe. La decisión "
                "alivia temporalmente la presión interna pero revela la profundidad "
                "del problema.",
                "In a move that signals vulnerability, {faction} taps its strategic "
                "reserves to cushion the blow. The decision temporarily eases internal "
                "pressure but reveals the depth of the problem.",
            ),
        },
        {
            "id": "iran_negotiates",
            "name": L("Irán abre canal", "Iran opens a channel"),
            "trigger_condition": "turn_number >= 3 and tension > 60",
            "effect": "Irán can propose a trade pact without spending DIP this turn.",
            "narrative_template": L(
                "Emisarios iraníes se reúnen discretamente con representantes de "
                "{faction} en un hotel de Ginebra. Irán no participa del embargo "
                "árabe y tiene petróleo que ofrecer — a su precio.",
                "Iranian envoys meet discreetly with representatives of {faction} in a "
                "Geneva hotel. Iran takes no part in the Arab embargo and has oil to "
                "offer — at its price.",
            ),
        },
        {
            "id": "superpower_confrontation",
            "name": L("Alerta nuclear", "Nuclear alert"),
            "trigger_condition": "tension >= 85",
            "effect": (
                "Both EEUU and URSS must spend 2 MIL or tension increases +5 more. "
                "All other factions lose 1 token budget this turn."
            ),
            "narrative_template": L(
                "La escalada en el frente de Oriente Medio dispara señales de alerta "
                "en Washington y Moscú. Los canales directos entre superpotencias se "
                "activan. Las cancillerías del mundo contienen la respiración.",
                "The escalation on the Middle Eastern front triggers alert signals in "
                "Washington and Moscow. The direct superpower channels go live. The "
                "world's chancelleries hold their breath.",
            ),
        },
        {
            "id": "domestic_pressure",
            "name": L("Presión electoral", "Electoral pressure"),
            "trigger_condition": "turn_number == 4",
            "effect": "Each faction with tension > 60 loses 1 DIP (internal pressure).",
            "narrative_template": L(
                "La crisis golpea las encuestas de todos los gobiernos involucrados. "
                "Los líderes de {factions} afrontan preguntas parlamentarias incómodas "
                "sobre su gestión. El margen de maniobra se estrecha.",
                "The crisis hammers the polls of every government involved. The leaders "
                "of {factions} face uncomfortable parliamentary questions about their "
                "handling of it. Room to maneuver narrows.",
            ),
        },
        {
            "id": "technology_transfer",
            "name": L("Oferta tecnológica", "Technology offer"),
            "trigger_condition": "any faction allocated ECO >= 3 in previous turn",
            "effect": (
                "The faction with the highest ECO can offer a technology deal: "
                "target faction gains +2 INT in exchange for a trade pact."
            ),
            "narrative_template": L(
                "Delegados de {faction} llegan cargados de catálogos técnicos y "
                "propuestas de cooperación industrial. El petróleo tiene sustitutos, "
                "pero la tecnología tiene condiciones.",
                "Delegates from {faction} arrive laden with technical catalogs and "
                "proposals for industrial cooperation. Oil has substitutes, but "
                "technology comes with conditions.",
            ),
        },
    ],
}
