# Crisis Protocol v2 — "La palabra tiene peso"

> Documento de diseño. Analiza la mecánica actual, diagnostica por qué la
> diplomacia se siente desconectada y propone una evolución en cinco pilares,
> implementable en cinco fases independientes.

## 1. Cómo funciona hoy la mecánica

El bucle por turno:

1. Cada jugador elige **postura** (confrontacional / cooperativa / ambigua),
   reparte su presupuesto de **tokens** (MIL / DIP / ECO / INT) y escribe una
   **directiva** de texto libre (≤ 300 caracteres).
2. Cuando todos los humanos envían, los **bots** deciden (Haiku) con: briefing,
   narrativa del turno anterior, su último intel y un resumen de pactos.
3. Una llamada de **evaluación** (Haiku) clasifica cada directiva: tipo de
   acción, objetivo (`target_id`), coherencia tokens↔directiva, calidad de
   decisión y multiplicador efectivo (0.3–1.2).
4. El **motor determinista** (`engine/resolver.py`) resuelve: efectos base,
   interacciones por pares (ataque vs defensa, espionaje vs contraespionaje,
   sanción vs pacto comercial, mediación), modificadores de pactos, flujos
   comerciales y tensión global (0–100 con umbrales).
5. Sonnet genera una **narrativa pública** (~100 palabras) y un **cable de
   inteligencia** privado (~60 palabras) por jugador.
6. Al final de partida se puntúa: objetivos (50%), eficiencia (20%), capital
   diplomático (10%), calidad de decisión (20%).

En paralelo existen dos sistemas "diplomáticos": **mensajería** (pública y
privada) y **pactos** (alianza, no agresión, comercio, intel).

## 2. Diagnóstico: sistemas yuxtapuestos, no integrados

1. **Los mensajes son decorativos.** No entran en *ninguna* llamada de IA: ni
   evaluación, ni narrativa, ni decisión de bots, ni intel. Escribir "te
   apoyaré si no atacas Tebas" no tiene efecto mecánico ni narrativo. Los bots
   nunca leen ni responden mensajes (`message_service.py`): chatear con una
   facción bot es hablar con una pared.
2. **La evaluación no tiene memoria.** `turn_service.py` llama a
   `evaluate_turn` sin `active_pacts` ni `previous_events` (quedan en
   "(none)") aunque el prompt los soporta. Claude juzga cada directiva en el
   vacío: seguir una estrategia de varios turnos o cumplir lo pactado no
   puntúa distinto que improvisar.
3. **La narrativa tampoco recuerda.** Solo recibe el resumen del turno actual;
   no hay continuidad de arcos ni referencia a negociaciones.
4. **El intel no revela nada real.** `private_observations` siempre llega como
   "(no new private data)": gastar en INT/espionaje solo compra prosa más
   segura, nunca información verdadera (directivas ajenas, pactos secretos,
   pistas de objetivos ocultos).
5. **Los pactos son unidireccionales y de una sola pieza.** Solo humano→bot;
   el bot decide en el acto sin ver la conversación previa; los bots nunca
   proponen; no hay pactos humano↔humano; nada verifica el *cumplimiento* de
   lo firmado.
6. **Las decisiones pasadas no dejan huella** salvo en recursos y tensión: no
   hay reputación, rencores ni confianza. Traicionar en el turno 2 no cambia
   cómo te tratan en el turno 5.

## 3. Propuesta: cinco pilares

Principio de diseño: **todo lo que un jugador dice, firma o hace queda
registrado en una memoria de partida, y esa memoria alimenta cada decisión de
la IA y cada modificador del motor.**

### Pilar 1 — Crónica de partida (habilita todo lo demás)

Un registro por partida construido determinísticamente a partir de datos ya
persistidos (turnos, acciones, pactos, narrativas): por cada turno pasado, la
tensión, las acciones declaradas de cada facción, los pactos firmados/rotos
públicos y la narrativa. Se inyecta en los prompts de evaluación, narrativa y
bots (y en el futuro, intel). Coste marginal bajo: mismas llamadas, más
contexto.

### Pilar 2 — Bots como actores diplomáticos de verdad

- **Responden mensajes privados**: respuesta de Claude en personaje (briefing,
  crónica, historial del hilo) cuando un humano escribe a un bot.
- **Inician diplomacia**: al abrirse cada turno, un bot puede enviar 0–1
  mensajes o proponer un pacto (queda pendiente hasta que el humano decide).
- **Deciden pactos con contexto**: `decide_pact_response` recibe el historial
  de mensajes con el proponente y su reputación.

### Pilar 3 — Reputación y cumplimiento de promesas

**Credibilidad** (0–100) por jugador, visible en la UI. La evaluación recibe
mensajes y pactos del turno y añade a su JSON un campo `promises`
(cumplida/rota por jugador). El motor lo traduce en: credibilidad ↑/↓,
multiplicador sobre acciones diplomáticas, input a la aceptación de pactos por
bots y al componente "capital diplomático" del scoring. Prometer tiene valor
porque romper la promesa tiene precio.

### Pilar 4 — Inteligencia con contenido real

Un `intel_engine` determinista decide qué se filtra según el INT del jugador y
el espionaje dirigido: INT alto o espionaje exitoso → directiva literal del
objetivo, existencia de pactos secretos o pista del objetivo oculto; INT medio
→ versión con ruido; INT bajo → nada. Claude solo redacta el cable con
`private_observations` reales.

### Pilar 5 — UX: feed diplomático unificado

Un timeline por turno que mezcla cronológicamente narrativa, mensajes,
propuestas/rupturas de pactos y eventos de reputación, con hilos por facción
que muestran el estado de la relación. En resolución, una sección
"causa y efecto" (*tu mensaje a Esparta → Esparta aceptó la no agresión → su
defensa redujo el ataque tebano*).

## 4. Fases de implementación

| Fase | Contenido | Estado |
|------|-----------|--------|
| **A — Cimientos** | Crónica determinista + pasar mensajes/pactos/crónica a evaluación, narrativa y decisiones de bots. Sin UI nueva. | **Hecha** |
| **B — Bots vivos** | Bots responden mensajes; propuestas de pacto bot→humano y humano↔humano. | **Hecha** |
| **C — Consecuencias** | Credibilidad + detección de promesas + modificadores en motor y scoring. | Pendiente |
| **D — Información** | Intel engine con filtraciones reales según INT. | Pendiente |
| **E — Fachada** | Feed diplomático unificado y panel causa-efecto. | Pendiente |

### Detalle de la Fase A

Nuevo módulo `backend/src/services/chronicle.py`:

- `build_chronicle(...)` — crónica **pública** de los turnos ya resueltos
  (tensión, acciones declaradas, pactos públicos firmados/rotos, narrativa).
  Los pactos secretos se excluyen: la crónica viaja a prompts cuyo output ven
  los jugadores.
- Formateo de los mensajes del turno en curso: bloque completo
  (público + privado, etiquetado) para la **evaluación** —que actúa como
  árbitro y lo ve todo—, y bloque solo-público para la **narrativa**.
- Eventos de pacto del turno (firmados/rotos, públicos) para la narrativa.

Cableado en `turn_service._resolve_turn_full`:

- `evaluate_turn` recibe pactos activos reales, la crónica como
  `previous_events` y los mensajes del turno (`messages_block`). El prompt de
  evaluación instruye valorar la coherencia directiva↔negociaciones.
- `generate_narrative` recibe crónica, mensajes públicos y pactos
  nuevos/rotos del turno, con regla de continuidad (puede referirse al pasado,
  sin inventar hechos nuevos).
- Los bots (`_collect_bot_decisions`) reciben la crónica y los mensajes que
  su facción puede ver (públicos + privados que la involucran), en lugar de
  solo la última narrativa.

Sin cambios de esquema de BD ni de UI. Los mensajes empiezan a importar:
los bots reaccionan a ellos en sus acciones y la evaluación premia la
coherencia con lo negociado.

### Detalle de la Fase B

Nuevo módulo `backend/src/services/diplomacy_service.py` con dos entradas,
cada una con núcleo testeable y wrapper en background (sesión propia):

- **Respuestas de bots** (`generate_bot_reply`): un mensaje privado
  humano→bot dispara una respuesta en personaje (prompt
  `bot_message_reply.py`, Haiku), con briefing, crónica, pactos visibles y el
  hilo bilateral completo. Si Claude falla, silencio (mejor que una respuesta
  enlatada). Se difunde `message_received` por WebSocket.
- **Diplomacia iniciada por bots** (`run_bot_diplomacy_for_game`): al abrirse
  cada turno (incluido el 1), cada bot decide UN movimiento opcional (prompt
  `bot_diplomacy.py`): declaración pública, mensaje privado o propuesta de
  pacto. Se ejecutan en secuencia para que un pacto firmado por un bot sea
  visible para los siguientes. Flag `BOT_DIPLOMACY_ENABLED` para desactivarlo.

Pactos v2 (`pact_service.py`):

- Cualquiera puede proponer a cualquiera. Destino bot → decisión síncrona de
  Claude, ahora con crónica e hilo de conversación con el proponente. Destino
  humano → la propuesta queda **pendiente** (nuevas columnas
  `proposal_is_secret`/`proposal_terms` en `messages` + migración SQLite) y se
  resuelve vía `POST /pacts/proposals/{message_id}/respond`.
- Guard de duplicados: pacto activo o propuesta pendiente entre las mismas
  dos partes bloquea nuevas propuestas.

Frontend: botones aceptar/rechazar sobre propuestas pendientes en el panel de
mensajes, toast de "propuesta pendiente", `respondToProposal` en el cliente
API y difusión WS que refresca el estado al llegar mensajes de bots.
