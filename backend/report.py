"""
Genera un informe HTML completo de una partida a partir de la base de datos SQLite.

Uso:
    uv run python report.py                        # última partida
    uv run python report.py <game_id_o_prefijo>   # partida específica
    uv run python report.py --list                 # listar partidas disponibles
"""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "crisis_protocol.db"
OUT_PATH = Path(__file__).parent / "informe_partida.html"

POSTURE_ES = {
    "cooperative": "Cooperativa",
    "ambiguous": "Ambigua",
    "confrontational": "Confrontacional",
}
POSTURE_COLOR = {
    "cooperative": "#16a34a",
    "ambiguous": "#b45309",
    "confrontational": "#dc2626",
}
PACT_ES = {
    "alliance": "Alianza",
    "non_aggression": "No agresión",
    "intel_share": "Intercambio de inteligencia",
    "trade": "Acuerdo comercial",
}
FACTION_COLORS = {
    "macedonia": "#1d4ed8",
    "atenas": "#7c3aed",
    "esparta": "#b45309",
    "tebas": "#dc2626",
    "corinto": "#0891b2",
    "persia": "#15803d",
}


# ──────────────────────────────────────────────
# Carga de datos
# ──────────────────────────────────────────────

def load(game_id: str) -> dict:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    game = dict(db.execute("SELECT * FROM games WHERE id=?", (game_id,)).fetchone())

    players_raw = db.execute(
        "SELECT * FROM players WHERE game_id=? ORDER BY role_id", (game_id,)
    ).fetchall()
    players = {}
    for p in players_raw:
        d = dict(p)
        d["resources"] = json.loads(d["resources"]) if d["resources"] else {}
        players[d["role_id"]] = d

    turns_raw = db.execute(
        "SELECT * FROM turns WHERE game_id=? ORDER BY turn_number", (game_id,)
    ).fetchall()

    turns = []
    for t in turns_raw:
        td = dict(t)

        actions_raw = db.execute(
            """
            SELECT a.*, p.role_id, p.is_ai
            FROM actions a
            JOIN players p ON a.player_id = p.id
            WHERE a.turn_id = ?
            ORDER BY p.role_id
            """,
            (t["id"],),
        ).fetchall()

        actions = []
        for a in actions_raw:
            ad = dict(a)
            ad["effects"] = json.loads(ad["effects"]) if ad["effects"] else {}
            actions.append(ad)

        messages_raw = db.execute(
            """
            SELECT m.*, pf.role_id as from_role,
                   pt.role_id as to_role
            FROM messages m
            JOIN players pf ON m.from_player_id = pf.id
            LEFT JOIN players pt ON m.to_player_id = pt.id
            WHERE m.turn_id = ?
            ORDER BY m.created_at
            """,
            (t["id"],),
        ).fetchall()
        messages = [dict(m) for m in messages_raw]

        td["actions"] = actions
        td["messages"] = messages
        turns.append(td)

    pacts_raw = db.execute(
        """
        SELECT pac.*,
               pa.role_id as role_a,
               pb.role_id as role_b
        FROM pacts pac
        JOIN players pa ON pac.player_a_id = pa.id
        JOIN players pb ON pac.player_b_id = pb.id
        WHERE pac.game_id = ?
        ORDER BY pac.created_turn
        """,
        (game_id,),
    ).fetchall()
    pacts = [dict(p) for p in pacts_raw]

    return {"game": game, "players": players, "turns": turns, "pacts": pacts}


# ──────────────────────────────────────────────
# Helpers de renderizado
# ──────────────────────────────────────────────

def faction_badge(role_id: str, name: str | None = None) -> str:
    color = FACTION_COLORS.get(role_id, "#374151")
    label = (name or role_id).capitalize()
    return (
        f'<span class="badge" style="background:{color};color:#fff">{label}</span>'
    )


def tension_bar(value: int, max_val: int = 100) -> str:
    pct = min(100, max(0, value))
    if pct < 40:
        color = "#16a34a"
    elif pct < 65:
        color = "#b45309"
    else:
        color = "#dc2626"
    return (
        f'<div class="tbar-wrap">'
        f'<div class="tbar-fill" style="width:{pct}%;background:{color}"></div>'
        f'</div>'
        f'<span class="tbar-val">{value}</span>'
    )


def quality_stars(score: float | None) -> str:
    if score is None:
        return ""
    filled = round(score / 2)
    stars = "★" * filled + "☆" * (5 - filled)
    return f'<span class="stars" title="{score}/10">{stars}</span>'


def resource_pills(res: dict) -> str:
    parts = []
    for k, v in res.items():
        parts.append(f'<span class="res-pill res-{k.lower()}">{k} {v}</span>')
    return " ".join(parts)


def token_pills(a: dict) -> str:
    pills = []
    for k in ("MIL", "DIP", "ECO", "INT"):
        v = a[f"tokens_{k.lower()}"]
        if v:
            pills.append(f'<span class="res-pill res-{k.lower()}">{k} +{v}</span>')
    if not pills:
        return '<span class="muted">Sin asignación</span>'
    return " ".join(pills)


# ──────────────────────────────────────────────
# Secciones HTML
# ──────────────────────────────────────────────

def render_header(data: dict) -> str:
    g = data["game"]
    scenario_name = "El Congreso de Corinto" if g["scenario_id"] == "corinth_338" else g["scenario_id"]
    status_label = "Finalizada" if g["status"] == "finished" else "En curso"
    status_color = "#16a34a" if g["status"] == "finished" else "#b45309"
    created = g["created_at"][:16].replace("T", " ")

    players = data["players"]
    human_roles = [r for r, p in players.items() if not p["is_ai"]]
    human_str = ", ".join(human_roles) if human_roles else "Ninguno (todos bots)"

    turns = data["turns"]
    finished = [t for t in turns if t["status"] == "finished"]
    t_start = turns[0]["tension_at_start"] if turns else "—"
    t_end = finished[-1]["tension_at_end"] if finished else "—"

    return f"""
<section class="card header-card">
  <div class="header-top">
    <div>
      <h1>{scenario_name}</h1>
      <p class="subtitle">Informe de partida · {created}</p>
    </div>
    <div class="header-meta">
      <span class="status-pill" style="background:{status_color}">{status_label}</span>
      <span class="muted">Partida <code>{g["id"][:8]}</code></span>
    </div>
  </div>
  <div class="header-stats">
    <div class="stat"><span class="stat-label">Turnos jugados</span><span class="stat-value">{len(finished)} / {g["max_turns"]}</span></div>
    <div class="stat"><span class="stat-label">Jugador humano</span><span class="stat-value">{human_str}</span></div>
    <div class="stat"><span class="stat-label">Tensión inicial</span><span class="stat-value">{t_start}</span></div>
    <div class="stat"><span class="stat-label">Tensión final</span><span class="stat-value">{t_end}</span></div>
  </div>
</section>
"""


def render_players(data: dict) -> str:
    rows = []
    for role_id, p in data["players"].items():
        color = FACTION_COLORS.get(role_id, "#374151")
        tipo = "Humano" if not p["is_ai"] else "Bot IA"
        tipo_class = "human-tag" if not p["is_ai"] else "bot-tag"
        rows.append(f"""
    <div class="player-card" style="border-left:4px solid {color}">
      <div class="player-header">
        <strong>{role_id.capitalize()}</strong>
        <span class="{tipo_class}">{tipo}</span>
      </div>
      <div class="player-resources">{resource_pills(p["resources"])}</div>
    </div>""")

    return f"""
<section class="card">
  <h2>Facciones participantes</h2>
  <p class="muted">Recursos mostrados al final de la partida.</p>
  <div class="players-grid">{"".join(rows)}
  </div>
</section>
"""


def render_tension_arc(data: dict) -> str:
    turns = [t for t in data["turns"] if t["status"] == "finished"]
    if not turns:
        return ""

    points = []
    width = 600
    height = 120
    pad = 40
    inner_w = width - 2 * pad
    inner_h = height - 2 * pad

    all_vals = [t["tension_at_start"] for t in turns] + [turns[-1]["tension_at_end"]]
    min_v, max_v = 0, 100

    def to_x(i: int) -> float:
        return pad + i * inner_w / (len(all_vals) - 1)

    def to_y(v: int) -> float:
        return pad + inner_h * (1 - (v - min_v) / (max_v - min_v))

    path_pts = []
    for i, v in enumerate(all_vals):
        path_pts.append(f"{to_x(i):.1f},{to_y(v):.1f}")
    polyline = " ".join(path_pts)

    dots = ""
    labels = ""
    for i, v in enumerate(all_vals):
        x, y = to_x(i), to_y(v)
        color = "#dc2626" if v >= 65 else "#b45309" if v >= 40 else "#16a34a"
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" stroke="#fff" stroke-width="1.5"/>'
        label = f"T{i}" if i < len(turns) else f"Fin"
        labels += f'<text x="{x:.1f}" y="{height - 6}" text-anchor="middle" font-size="10" fill="#6b7280">{label}</text>'
        labels += f'<text x="{x:.1f}" y="{y - 9:.1f}" text-anchor="middle" font-size="10" fill="{color}" font-weight="600">{v}</text>'

    y_lines = ""
    for threshold, label in [(40, "Bajo"), (65, "Alto")]:
        yy = to_y(threshold)
        y_lines += f'<line x1="{pad}" y1="{yy:.1f}" x2="{width - pad}" y2="{yy:.1f}" stroke="#e5e7eb" stroke-dasharray="4,3"/>'
        y_lines += f'<text x="{pad - 4}" y="{yy + 3:.1f}" text-anchor="end" font-size="9" fill="#9ca3af">{threshold}</text>'

    return f"""
<section class="card">
  <h2>Evolución de la tensión</h2>
  <div class="tension-arc-wrap">
    <svg viewBox="0 0 {width} {height}" class="tension-svg">
      {y_lines}
      <polyline points="{polyline}" fill="none" stroke="#6366f1" stroke-width="2.5" stroke-linejoin="round"/>
      {dots}
      {labels}
    </svg>
  </div>
  <p class="muted tension-legend">
    <span style="color:#16a34a">● Verde</span> tensión baja (&lt;40) ·
    <span style="color:#b45309">● Ámbar</span> media (40–64) ·
    <span style="color:#dc2626">● Rojo</span> alta (≥65)
  </p>
</section>
"""


def render_turn(t: dict, data: dict) -> str:
    num = t["turn_number"]
    t_start = t["tension_at_start"]
    t_end = t.get("tension_at_end") or "—"
    delta = (t_end - t_start) if isinstance(t_end, int) else 0
    delta_str = f"{'▲' if delta > 0 else '▼' if delta < 0 else '='} {abs(delta)}" if delta != 0 else "= sin cambio"
    delta_color = "#dc2626" if delta > 0 else "#16a34a" if delta < 0 else "#6b7280"

    # Narrativa
    narrative_block = ""
    if t.get("narrative"):
        narrative_block = f"""
  <div class="narrative-block">
    <h4 class="section-label">Narrativa del turno</h4>
    <p class="narrative-text">{t["narrative"]}</p>
  </div>"""

    # Acciones
    action_rows = []
    for a in t["actions"]:
        role = a["role_id"]
        color = FACTION_COLORS.get(role, "#374151")
        tipo = "Humano" if not a["is_ai"] else "Bot IA"
        tipo_class = "human-tag" if not a["is_ai"] else "bot-tag"
        posture = a["posture"]
        posture_label = POSTURE_ES.get(posture, posture)
        posture_color = POSTURE_COLOR.get(posture, "#374151")

        eff = a["effects"]
        action_type = eff.get("action_type", "generic") if eff else "generic"
        action_type_label = {
            "generic": "Acción genérica",
            "diplomatic_proposal": "Propuesta diplomática",
            "diplomatic_mediation": "Mediación diplomática",
            "military_threat": "Amenaza militar",
            "economic_pressure": "Presión económica",
            "intelligence_op": "Operación de inteligencia",
            "alliance_formation": "Formación de alianza",
        }.get(action_type, action_type)

        reasoning = eff.get("reasoning", "") if eff else ""
        reasoning_block = ""
        if reasoning and reasoning != "(fallback determinista)":
            reasoning_block = f'<div class="reasoning"><span class="reasoning-label">Evaluación IA:</span> {reasoning}</div>'

        quality = a.get("decision_quality")
        mult = a.get("effective_multiplier")
        eval_line = ""
        if quality is not None:
            eval_line = f"""
        <div class="eval-line">
          {quality_stars(quality)}
          <span class="eval-detail">Calidad {quality}/10 · Multiplicador ×{mult}</span>
          <span class="action-type-pill">{action_type_label}</span>
        </div>"""

        intel = a.get("intel_report", "")
        intel_block = ""
        if intel:
            intel_block = f"""
        <details class="intel-details">
          <summary>Ver informe de inteligencia</summary>
          <div class="intel-text">{intel}</div>
        </details>"""

        action_rows.append(f"""
      <div class="action-card" style="border-left:4px solid {color}">
        <div class="action-header">
          <div class="action-who">
            <strong style="color:{color}">{role.capitalize()}</strong>
            <span class="{tipo_class}">{tipo}</span>
            <span class="posture-pill" style="color:{posture_color};border-color:{posture_color}">{posture_label}</span>
          </div>
          <div class="action-tokens">{token_pills(a)}</div>
        </div>
        <div class="directive">"{a['directive']}"</div>
        {eval_line}
        {reasoning_block}
        {intel_block}
      </div>""")

    actions_block = f"""
  <div class="actions-section">
    <h4 class="section-label">Acciones de las facciones</h4>
    {"".join(action_rows)}
  </div>"""

    # Mensajes y diplomacia
    messages = t.get("messages", [])
    msg_rows = []
    for m in messages:
        from_role = m.get("from_role", "?")
        to_role = m.get("to_role")
        from_color = FACTION_COLORS.get(from_role, "#374151")

        if m.get("is_proposal"):
            status = m.get("proposal_status", "")
            status_label = {"accepted": "✓ Aceptado", "rejected": "✗ Rechazado", "pending": "⏳ Pendiente"}.get(status, status)
            status_color = {"accepted": "#16a34a", "rejected": "#dc2626", "pending": "#b45309"}.get(status, "#374151")
            pact_type = PACT_ES.get(m.get("proposal_type", ""), m.get("proposal_type", ""))
            secret_tag = ' <span class="secret-tag">secreto</span>' if "secreto" in (m.get("content") or "") else ""
            msg_rows.append(f"""
      <div class="msg-card proposal-card">
        <div class="msg-header">
          <span style="color:{from_color}"><strong>{from_role.capitalize()}</strong></span>
          → <strong>{(to_role or "?").capitalize()}</strong>
          <span class="pact-type-pill">{pact_type}{secret_tag}</span>
          <span class="proposal-status" style="color:{status_color}">{status_label}</span>
        </div>
        <div class="msg-content">{m.get("content", "")}</div>
      </div>""")
        else:
            dest = f"→ {to_role.capitalize()}" if to_role else "→ todos"
            dest_color = FACTION_COLORS.get(to_role, "#374151") if to_role else "#374151"
            msg_rows.append(f"""
      <div class="msg-card">
        <div class="msg-header">
          <span style="color:{from_color}"><strong>{from_role.capitalize()}</strong></span>
          <span style="color:{dest_color}">{dest}</span>
        </div>
        <div class="msg-content">"{m.get("content", "")}"</div>
      </div>""")

    diplomacy_block = ""
    if msg_rows:
        diplomacy_block = f"""
  <div class="diplomacy-section">
    <h4 class="section-label">Actividad diplomática</h4>
    {"".join(msg_rows)}
  </div>"""

    return f"""
<section class="card turn-card">
  <div class="turn-header">
    <h2>Turno {num}</h2>
    <div class="turn-tension">
      Tensión: <strong>{t_start}</strong> → <strong>{t_end}</strong>
      <span class="tension-delta" style="color:{delta_color}">{delta_str}</span>
    </div>
  </div>
  {narrative_block}
  {actions_block}
  {diplomacy_block}
</section>
"""


def render_pacts(data: dict) -> str:
    pacts = data["pacts"]
    if not pacts:
        return ""

    rows = []
    for p in pacts:
        role_a = p["role_a"]
        role_b = p["role_b"]
        color_a = FACTION_COLORS.get(role_a, "#374151")
        color_b = FACTION_COLORS.get(role_b, "#374151")
        pact_label = PACT_ES.get(p["type"], p["type"])
        secret = "Secreto" if p["is_secret"] else "Público"
        secret_class = "secret-tag" if p["is_secret"] else "public-tag"
        active = "Activo" if p["is_active"] else f"Roto (turno {p.get('broken_turn', '?')})"
        active_class = "active-tag" if p["is_active"] else "broken-tag"

        rows.append(f"""
    <div class="pact-card">
      <div class="pact-parties">
        <span style="color:{color_a}"><strong>{role_a.capitalize()}</strong></span>
        ⟷
        <span style="color:{color_b}"><strong>{role_b.capitalize()}</strong></span>
      </div>
      <div class="pact-meta">
        <span class="pact-type-pill">{pact_label}</span>
        <span class="{secret_class}">{secret}</span>
        <span class="{active_class}">{active}</span>
        <span class="muted">firmado en turno {p["created_turn"]}</span>
      </div>
    </div>""")

    return f"""
<section class="card">
  <h2>Pactos firmados</h2>
  {"".join(rows)}
</section>
"""


def render_final_state(data: dict) -> str:
    players = data["players"]
    rows = []
    for role_id, p in players.items():
        color = FACTION_COLORS.get(role_id, "#374151")
        tipo = "Humano" if not p["is_ai"] else "Bot IA"
        tipo_class = "human-tag" if not p["is_ai"] else "bot-tag"
        rows.append(f"""
    <div class="final-card" style="border-left:4px solid {color}">
      <div class="final-header">
        <strong style="color:{color}">{role_id.capitalize()}</strong>
        <span class="{tipo_class}">{tipo}</span>
      </div>
      <div class="final-resources">{resource_pills(p["resources"])}</div>
    </div>""")

    return f"""
<section class="card">
  <h2>Estado final de los recursos</h2>
  <div class="final-grid">{"".join(rows)}
  </div>
</section>
"""


# ──────────────────────────────────────────────
# HTML envolvente
# ──────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f3f4f6; color: #111827; line-height: 1.6; }
.container { max-width: 860px; margin: 0 auto; padding: 2rem 1rem 4rem; }
h1 { font-size: 1.75rem; font-weight: 700; }
h2 { font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem; }
h4.section-label { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: #6b7280; margin: 1.25rem 0 .6rem; }
p.subtitle { color: #6b7280; font-size: .9rem; margin-top:.25rem; }
p.muted, span.muted { color: #9ca3af; font-size: .85rem; }
code { font-family: monospace; background: #e5e7eb; padding: 1px 5px; border-radius: 3px; font-size: .85em; }

.card { background: #fff; border-radius: 10px; padding: 1.5rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.turn-card { border-top: 3px solid #6366f1; }

/* Header */
.header-card .header-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.25rem; }
.header-meta { display: flex; flex-direction: column; align-items: flex-end; gap: .4rem; }
.header-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: .75rem; }
.stat { background: #f9fafb; border-radius: 8px; padding: .6rem .8rem; }
.stat-label { display: block; font-size: .72rem; text-transform: uppercase; letter-spacing: .05em; color: #6b7280; }
.stat-value { display: block; font-size: 1.1rem; font-weight: 700; margin-top: .1rem; }

/* Tags */
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: .78rem; font-weight: 600; }
.status-pill { padding: 3px 10px; border-radius: 999px; font-size: .8rem; font-weight: 600; color: #fff; }
.human-tag { background: #dbeafe; color: #1d4ed8; font-size: .72rem; padding: 2px 7px; border-radius: 999px; font-weight: 600; }
.bot-tag   { background: #f3f4f6; color: #4b5563; font-size: .72rem; padding: 2px 7px; border-radius: 999px; }
.secret-tag { background: #fef3c7; color: #92400e; font-size: .72rem; padding: 2px 7px; border-radius: 999px; }
.public-tag { background: #dcfce7; color: #15803d; font-size: .72rem; padding: 2px 7px; border-radius: 999px; }
.active-tag { background: #dcfce7; color: #15803d; font-size: .72rem; padding: 2px 7px; border-radius: 999px; }
.broken-tag { background: #fee2e2; color: #b91c1c; font-size: .72rem; padding: 2px 7px; border-radius: 999px; }
.posture-pill { font-size: .72rem; padding: 2px 8px; border-radius: 999px; border: 1.5px solid; font-weight: 600; }
.pact-type-pill { background: #ede9fe; color: #5b21b6; font-size: .72rem; padding: 2px 8px; border-radius: 999px; }
.action-type-pill { background: #e0f2fe; color: #0369a1; font-size: .72rem; padding: 2px 8px; border-radius: 999px; }
.proposal-status { font-size: .8rem; font-weight: 600; }

/* Resources */
.res-pill { display: inline-block; padding: 1px 7px; border-radius: 4px; font-size: .78rem; font-weight: 700; font-family: monospace; }
.res-mil { background: #fee2e2; color: #991b1b; }
.res-dip { background: #dbeafe; color: #1e40af; }
.res-eco { background: #dcfce7; color: #15803d; }
.res-int { background: #fef9c3; color: #854d0e; }

/* Players / Final grid */
.players-grid, .final-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: .75rem; margin-top: .75rem; }
.player-card, .final-card { padding: .75rem 1rem; border-radius: 8px; background: #f9fafb; }
.player-header, .final-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: .4rem; }
.player-resources, .final-resources { display: flex; flex-wrap: wrap; gap: .3rem; }

/* Tension arc */
.tension-arc-wrap { margin: .75rem 0; }
.tension-svg { width: 100%; height: auto; }
.tension-legend { margin-top: .5rem; }
.tbar-wrap { display: inline-block; width: 100px; height: 8px; background: #e5e7eb; border-radius: 4px; vertical-align: middle; }
.tbar-fill { height: 100%; border-radius: 4px; }
.tbar-val { margin-left: 6px; font-weight: 600; vertical-align: middle; }

/* Turn */
.turn-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: .5rem; margin-bottom: .5rem; }
.turn-tension { font-size: .9rem; color: #374151; }
.tension-delta { margin-left: .5rem; font-weight: 700; }
.narrative-block { background: #f8f7ff; border-left: 3px solid #6366f1; padding: .75rem 1rem; border-radius: 0 6px 6px 0; margin-bottom: .5rem; }
.narrative-text { font-size: .92rem; color: #374151; line-height: 1.7; }

/* Actions */
.actions-section { display: flex; flex-direction: column; gap: .6rem; }
.action-card { background: #f9fafb; border-radius: 8px; padding: .75rem 1rem; }
.action-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: .4rem; margin-bottom: .4rem; }
.action-who { display: flex; align-items: center; gap: .4rem; flex-wrap: wrap; }
.action-tokens { display: flex; gap: .3rem; flex-wrap: wrap; }
.directive { font-size: .88rem; color: #374151; font-style: italic; margin: .25rem 0; }
.eval-line { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; margin-top: .35rem; }
.stars { color: #f59e0b; letter-spacing: .05em; }
.eval-detail { font-size: .78rem; color: #6b7280; }
.reasoning { margin-top: .4rem; font-size: .82rem; background: #fffbeb; border-left: 2px solid #fbbf24; padding: .4rem .6rem; border-radius: 0 4px 4px 0; color: #374151; }
.reasoning-label { font-weight: 700; color: #92400e; }

/* Intel */
.intel-details { margin-top: .4rem; }
.intel-details summary { font-size: .8rem; color: #6366f1; cursor: pointer; font-weight: 600; }
.intel-text { font-size: .82rem; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: .6rem .8rem; margin-top: .4rem; color: #166534; white-space: pre-wrap; line-height: 1.65; }

/* Diplomacy */
.diplomacy-section { display: flex; flex-direction: column; gap: .5rem; }
.msg-card { background: #f9fafb; border-radius: 8px; padding: .65rem .9rem; }
.proposal-card { background: #faf5ff; border: 1px solid #e9d5ff; }
.msg-header { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; margin-bottom: .25rem; font-size: .88rem; }
.msg-content { font-size: .85rem; color: #374151; font-style: italic; }

/* Pacts */
.pact-card { background: #f9fafb; border-radius: 8px; padding: .65rem .9rem; margin-bottom: .5rem; }
.pact-parties { font-size: .95rem; margin-bottom: .35rem; }
.pact-meta { display: flex; align-items: center; gap: .4rem; flex-wrap: wrap; }
"""


def build_html(data: dict) -> str:
    turns_html = "".join(render_turn(t, data) for t in data["turns"] if t["status"] == "finished")
    body = (
        render_header(data)
        + render_players(data)
        + render_tension_arc(data)
        + turns_html
        + render_pacts(data)
        + render_final_state(data)
    )
    game_id = data["game"]["id"]
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Informe de partida — {game_id[:8]}</title>
  <style>{CSS}</style>
</head>
<body>
  <div class="container">
    {body}
  </div>
</body>
</html>"""


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

def list_games() -> None:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    games = db.execute("SELECT * FROM games ORDER BY created_at DESC").fetchall()
    print(f"\n{'ID':38}  {'Escenario':20}  {'Estado':10}  {'Creada'}")
    print("-" * 90)
    for g in games:
        print(f"{g['id']}  {g['scenario_id']:20}  {g['status']:10}  {g['created_at'][:16]}")
    print()


def resolve_game_id(arg: str) -> str:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT id FROM games WHERE id=? OR id LIKE ?", (arg, f"{arg}%")
    ).fetchall()
    if not rows:
        print(f"No se encontró ninguna partida con id o prefijo '{arg}'.")
        sys.exit(1)
    if len(rows) > 1:
        print(f"Prefijo ambiguo '{arg}', coincide con {len(rows)} partidas. Usa más caracteres.")
        sys.exit(1)
    return rows[0]["id"]


def last_game_id() -> str:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    row = db.execute("SELECT id FROM games ORDER BY created_at DESC LIMIT 1").fetchone()
    if not row:
        print("No hay partidas en la base de datos.")
        sys.exit(1)
    return row["id"]


def main() -> None:
    args = sys.argv[1:]

    if "--list" in args:
        list_games()
        return

    game_id = resolve_game_id(args[0]) if args else last_game_id()

    print(f"Generando informe para la partida {game_id[:8]}…")
    data = load(game_id)
    html = build_html(data)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Informe guardado en: {OUT_PATH}")


if __name__ == "__main__":
    main()
