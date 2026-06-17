"""Read-only staff stats dashboard (Phase 4b).

Runs in a daemon thread INSIDE the bot process. It is OPT-IN and safe by
default: the server only starts when the ``STATS_WEB_PASSWORD`` env var is set,
so member data is never exposed unless an operator deliberately turns it on.

Security model:
  * Binds to 127.0.0.1 only. Public exposure is the operator's job via a secure
    tunnel they run on the Pi, e.g.:
        cloudflared tunnel --url http://localhost:8081
  * Every page is gated by HTTP Basic Auth (user ``STATS_WEB_USER`` default
    "staff", password ``STATS_WEB_PASSWORD``).
  * Strictly read-only. No route mutates any data.

Thread-safety: the bot's own sqlite connections are NOT thread-safe (e.g.
``_xp_db`` is opened without check_same_thread), so this module opens its OWN
read-only connections (mode=ro) per request and never touches bot objects'
live connections. JSON files are read fresh from disk. Every data section is
wrapped in try/except and degrades to "unavailable" rather than crashing.
"""
from __future__ import annotations

import os
import json
import html
import sqlite3
import functools
import threading
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:
    _ET = None

_started = False
_start_lock = threading.Lock()

_DATA = "diff_data"
_ACTIVITY_DB = os.path.join(_DATA, "diff_activity.db")
_XP_DB = os.path.join(_DATA, "diff_xp.db")
_RC_DB = os.path.join(_DATA, "diff_rollcall.db")
_STREAKS_JSON = os.path.join(_DATA, "diff_rc_streaks.json")
_TICKET_PERF_JSON = os.path.join(_DATA, "diff_ticket_perf.json")


def start_stats_web(main):
    """Start the dashboard thread once if STATS_WEB_PASSWORD is configured.

    ``main`` is the bot's __main__ module, used only to resolve member display
    names and the GUILD_ID constant. Idempotent — safe to call from on_ready,
    which can fire multiple times on reconnect.
    """
    global _started
    with _start_lock:
        if _started:
            return
        if not os.environ.get("STATS_WEB_PASSWORD"):
            print("[stats-web] STATS_WEB_PASSWORD not set - dashboard disabled")
            return
        try:
            import flask  # noqa: F401
        except Exception as e:
            print(f"[stats-web] flask unavailable, dashboard disabled: {e!r}")
            return
        _started = True
    t = threading.Thread(
        target=_serve, args=(main,), name="stats-web", daemon=True
    )
    t.start()
    port = os.environ.get("STATS_WEB_PORT", "8081")
    print(f"[stats-web] dashboard serving on 127.0.0.1:{port}")


def _serve(main):
    from flask import Flask, request, Response

    app = Flask("diff_stats_web")
    port = int(os.environ.get("STATS_WEB_PORT", "8081"))

    def _auth_ok(auth):
        want_user = os.environ.get("STATS_WEB_USER", "staff")
        want_pw = os.environ.get("STATS_WEB_PASSWORD", "")
        return bool(auth) and auth.username == want_user and auth.password == want_pw

    def _requires_auth(fn):
        @functools.wraps(fn)
        def _wrap(*a, **k):
            if not _auth_ok(request.authorization):
                return Response(
                    "Authentication required.",
                    401,
                    {"WWW-Authenticate": 'Basic realm="DIFF Stats"'},
                )
            return fn(*a, **k)
        return _wrap

    @app.route("/healthz")
    def _healthz():
        return "ok", 200

    @app.route("/")
    @_requires_auth
    def _home():
        from flask import Response as _R
        return _R(_render_page(main), mimetype="text/html")

    try:
        app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"[stats-web] server stopped: {e!r}")


# ---------------------------------------------------------------------------
# Data helpers (all read-only, all defensive)
# ---------------------------------------------------------------------------

def _ro_conn(path):
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _guild_id(main):
    try:
        return int(getattr(main, "GUILD_ID"))
    except Exception:
        return 0


def _name(main, uid):
    try:
        bot = getattr(main, "bot", None)
        gid = _guild_id(main)
        g = bot.get_guild(gid) if bot else None
        m = g.get_member(int(uid)) if g else None
        if m is not None:
            return m.display_name
    except Exception:
        pass
    return f"User {uid}"


def _week_key(dt=None):
    now = dt or (datetime.now(_ET) if _ET else datetime.now())
    iso = now.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def _overview(main):
    out = {"total": "n/a", "tiers": {}}
    try:
        fn = getattr(main, "_memberstats_query", None)
        if callable(fn):
            stats = fn() or {}
            out["total"] = stats.get("total_tracked", "n/a")
            out["verified_pct"] = stats.get("verified_pct")
            out["recent_7d"] = stats.get("recent_7d")
            out["inactive_7d"] = stats.get("inactive_7d")
    except Exception:
        pass
    try:
        with _ro_conn(_ACTIVITY_DB) as c:
            rows = c.execute(
                "SELECT health_tier, COUNT(*) AS n FROM member_activity "
                "WHERE health_tier IS NOT NULL GROUP BY health_tier"
            ).fetchall()
            out["tiers"] = {r["health_tier"]: r["n"] for r in rows}
    except Exception:
        pass
    return out


def _xp_leaderboard(main, limit=15):
    gid = _guild_id(main)
    rows = []
    try:
        with _ro_conn(_XP_DB) as c:
            rows = c.execute(
                "SELECT user_id, xp, level FROM xp WHERE guild_id=? "
                "ORDER BY xp DESC LIMIT ?",
                (gid, limit),
            ).fetchall()
    except Exception:
        return []
    return [(_name(main, r["user_id"]), r["level"], r["xp"]) for r in rows]


def _motw(main, limit=5):
    gid = _guild_id(main)
    wk = _week_key()
    rows = []
    try:
        with _ro_conn(_XP_DB) as c:
            rows = c.execute(
                "SELECT user_id, week_xp FROM xp_week "
                "WHERE guild_id=? AND week_key=? ORDER BY week_xp DESC LIMIT ?",
                (gid, wk, limit),
            ).fetchall()
    except Exception:
        return wk, []
    return wk, [(_name(main, r["user_id"]), r["week_xp"]) for r in rows]


def _badge_leaderboard(main, limit=10):
    gid = _guild_id(main)
    rows = []
    try:
        with _ro_conn(_XP_DB) as c:
            rows = c.execute(
                "SELECT user_id, COUNT(*) AS n FROM xp_badges WHERE guild_id=? "
                "GROUP BY user_id ORDER BY n DESC LIMIT ?",
                (gid, limit),
            ).fetchall()
    except Exception:
        return []
    return [(_name(main, r["user_id"]), r["n"]) for r in rows]


def _attendance(main, limit=15):
    gid = _guild_id(main)
    rows = []
    try:
        with _ro_conn(_RC_DB) as c:
            rows = c.execute(
                "SELECT user_id, attended_count, no_show_count, yes_count "
                "FROM attendance_stats WHERE guild_id=? "
                "ORDER BY attended_count DESC LIMIT ?",
                (gid, limit),
            ).fetchall()
    except Exception:
        return []
    out = []
    for r in rows:
        att = r["attended_count"] or 0
        ns = r["no_show_count"] or 0
        denom = att + ns
        rate = f"{(att / denom * 100):.0f}%" if denom else "-"
        out.append((_name(main, r["user_id"]), att, ns, rate))
    return out


def _streaks(main, limit=10):
    try:
        with open(_STREAKS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        return []
    items = []
    for uid, rec in data.items():
        if not isinstance(rec, dict):
            continue
        items.append((uid, rec.get("streak", 0) or 0, rec.get("best", 0) or 0))
    items.sort(key=lambda x: (x[2], x[1]), reverse=True)
    return [(_name(main, uid), cur, best) for uid, cur, best in items[:limit]]


def _tickets(main, limit=12):
    try:
        with open(_TICKET_PERF_JSON, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception:
        return []
    out = []
    for sid, rec in data.items():
        if not isinstance(rec, dict):
            continue
        closed = rec.get("closed", 0) or 0
        claimed = rec.get("claimed", 0) or 0
        total = rec.get("total_seconds", 0) or 0
        avg = "-"
        if closed:
            secs = total / closed
            if secs >= 3600:
                avg = f"{secs / 3600:.1f}h"
            else:
                avg = f"{secs / 60:.0f}m"
        out.append((_name(main, sid), claimed, closed, avg))
    out.sort(key=lambda x: x[2], reverse=True)
    return out[:limit]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

_CSS = """
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#e6edf3;font:15px/1.5 -apple-system,
BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
header{padding:24px 28px;background:linear-gradient(135deg,#161b22,#1f2630);
border-bottom:1px solid #30363d}
h1{margin:0;font-size:22px;letter-spacing:.3px}
.sub{color:#8b949e;font-size:13px;margin-top:4px}
.wrap{max-width:1100px;margin:0 auto;padding:24px 28px}
.cards{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:28px}
.card{flex:1 1 150px;background:#161b22;border:1px solid #30363d;border-radius:12px;
padding:16px 18px}
.card .v{font-size:26px;font-weight:700}
.card .l{color:#8b949e;font-size:12px;text-transform:uppercase;letter-spacing:.6px;
margin-top:4px}
section{background:#161b22;border:1px solid #30363d;border-radius:12px;
padding:18px 20px;margin-bottom:22px}
section h2{margin:0 0 14px;font-size:16px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:8px 10px;font-size:14px}
th{color:#8b949e;font-weight:600;border-bottom:1px solid #30363d;font-size:12px;
text-transform:uppercase;letter-spacing:.5px}
tr:nth-child(even) td{background:#1c2230}
td.r,th.r{text-align:right}
.rank{color:#8b949e;width:34px}
.empty{color:#8b949e;font-style:italic;padding:6px 2px}
footer{color:#6e7681;font-size:12px;text-align:center;padding:18px}
"""


def _esc(v):
    return html.escape(str(v))


def _table(headers, rows, ranked=True):
    if not rows:
        return '<div class="empty">No data available.</div>'
    parts = ["<table><thead><tr>"]
    if ranked:
        parts.append('<th class="rank">#</th>')
    for i, h in enumerate(headers):
        cls = ' class="r"' if i > 0 else ""
        parts.append(f"<th{cls}>{_esc(h)}</th>")
    parts.append("</tr></thead><tbody>")
    for idx, row in enumerate(rows, 1):
        parts.append("<tr>")
        if ranked:
            parts.append(f'<td class="rank">{idx}</td>')
        for i, cell in enumerate(row):
            cls = ' class="r"' if i > 0 else ""
            parts.append(f"<td{cls}>{_esc(cell)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def _render_page(main):
    try:
        ov = _overview(main)
    except Exception:
        ov = {"total": "n/a", "tiers": {}}
    tiers = ov.get("tiers", {})

    cards = [
        ("Members tracked", ov.get("total", "n/a")),
        ("Verified %", ov.get("verified_pct", "n/a")),
        ("Active 7d", ov.get("recent_7d", "n/a")),
        ("Inactive 7d", ov.get("inactive_7d", "n/a")),
        ("Strong", tiers.get("Strong", 0)),
        ("Active", tiers.get("Active", 0)),
        ("At Risk", tiers.get("At Risk", 0)),
        ("Ghost", tiers.get("Ghost", 0)),
    ]
    card_html = "".join(
        f'<div class="card"><div class="v">{_esc(v)}</div>'
        f'<div class="l">{_esc(l)}</div></div>'
        for l, v in cards
    )

    xp = _table(["Member", "Level", "XP"], _xp_leaderboard(main))
    wk, motw_rows = _motw(main)
    motw = _table(["Member", "Weekly XP"], motw_rows)
    badges = _table(["Member", "Badges"], _badge_leaderboard(main))
    att = _table(
        ["Member", "Attended", "No-shows", "Show-up %"], _attendance(main)
    )
    streaks = _table(["Member", "Current", "Best"], _streaks(main))
    tickets = _table(
        ["Staff", "Claimed", "Closed", "Avg close"], _tickets(main)
    )

    now = datetime.now(_ET) if _ET else datetime.now()
    stamp = now.strftime("%b %d, %Y %I:%M %p %Z")

    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>DIFF Meets - Staff Stats</title>"
        f"<style>{_CSS}</style></head><body>"
        "<header><h1>DIFF Meets - Staff Stats</h1>"
        f"<div class='sub'>Read-only dashboard - generated {_esc(stamp)}</div>"
        "</header><div class='wrap'>"
        f"<div class='cards'>{card_html}</div>"
        f"<section><h2>XP Leaderboard</h2>{xp}</section>"
        f"<section><h2>Member of the Week - {_esc(wk)} (live)</h2>{motw}</section>"
        f"<section><h2>Badge Leaderboard</h2>{badges}</section>"
        f"<section><h2>Attendance Leaderboard</h2>{att}</section>"
        f"<section><h2>Roll-Call Streaks</h2>{streaks}</section>"
        f"<section><h2>Ticket Performance</h2>{tickets}</section>"
        "</div><footer>DIFF Meets V2 - read-only - data stays on the Pi</footer>"
        "</body></html>"
    )
