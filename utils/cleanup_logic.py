"""
utils/cleanup_logic.py
Smart Auto Cleanup + Recovery System — core config, DB helpers, and logic.

All thresholds and toggles live in CLEANUP_CONFIG at the top.
"""

import contextlib
import logging
import sqlite3
import time
from pathlib import Path

log = logging.getLogger("diff_cleanup")

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG  —  edit these to tune the entire system
# ══════════════════════════════════════════════════════════════════════════════
CLEANUP_CONFIG = {
    # ── DM + escalation toggles ────────────────────────────────────────────
    "dm_reminders_enabled":    True,   # send re-engagement DMs automatically
    "auto_kick_enabled":       False,  # never kick without staff review unless set True
    "require_staff_review":    True,   # always require staff to confirm removal

    # ── Grace periods (days) ───────────────────────────────────────────────
    "grace_period_at_risk":    3,      # days before At Risk → Cleanup Review
    "grace_period_ghost":      2,      # days before Ghost  → Cleanup Review

    # ── Reminder limits ────────────────────────────────────────────────────
    "max_reminders":           2,      # max DMs before just escalating
    "reminder_cooldown_days":  3,      # min days between DMs to the same person

    # ── Scan thresholds ────────────────────────────────────────────────────
    "min_join_age_days":        7,     # ignore members who joined < N days ago
    "inactivity_days_at_risk":  7,     # days silent → At Risk candidate
    "inactivity_days_ghost":   14,     # days silent → Ghost candidate
    "scan_score_at_risk_max":  59,     # health score ≤ this = At Risk
    "scan_score_ghost_max":    39,     # health score ≤ this = Ghost
}

# Roles that are ALWAYS skipped — add/remove names as needed
EXEMPT_ROLE_NAMES: set[str] = {
    "Leader", "Co-Leader", "Manager", "Moderator", "Admin",
    "Host", "Senior Host", "Head Host", "Junior Host", "Staff",
    "Bot",
}
EXEMPT_ROLE_IDS: set[int] = set()  # add specific role IDs here if needed

# ── Flag / tier / review constants ────────────────────────────────────────────
FLAG_SAFE    = "Safe"
FLAG_AT_RISK = "At Risk"
FLAG_GHOST   = "Ghost"
FLAG_REVIEW  = "Cleanup Review"

REVIEW_PENDING  = "Pending"
REVIEW_KEEP     = "Keep"
REVIEW_MONITOR  = "Monitor"
REVIEW_REMOVE   = "Remove"
REVIEW_REENGAGE = "Re-engage Again"

RECOVERY_FULL    = "Recovered"
RECOVERY_PARTIAL = "Partially Recovered"
RECOVERY_NONE    = "Still Inactive"

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE LAYER
# ══════════════════════════════════════════════════════════════════════════════
_DB_PATH = Path("database/retention.db")


def _db() -> sqlite3.Connection:
    """Open a new connection (WAL mode, Row factory)."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextlib.contextmanager
def _conn():
    """Context-manager that commits on exit or rolls back on error."""
    conn = _db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables. Safe to call on every boot (idempotent)."""
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cleanup_flags (
                user_id           INTEGER PRIMARY KEY,
                display_name      TEXT,
                flag_type         TEXT    DEFAULT 'Safe',
                flagged_at        REAL,
                grace_expires_at  REAL,
                reminders_sent    INTEGER DEFAULT 0,
                last_reminder_at  REAL,
                review_state      TEXT    DEFAULT 'Pending',
                action_taken      TEXT,
                recovered         INTEGER DEFAULT 0,
                recovered_at      REAL,
                reason            TEXT,
                health_score      INTEGER DEFAULT 0,
                health_tier       TEXT,
                days_inactive     INTEGER DEFAULT 0,
                is_verified       INTEGER DEFAULT 0,
                meet_count        INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recovery_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                event_type  TEXT,
                recorded_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS action_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER,
                display_name TEXT,
                action       TEXT,
                performed_by TEXT,
                notes        TEXT,
                created_at   REAL
            )
        """)


# ══════════════════════════════════════════════════════════════════════════════
# EXEMPTION CHECK
# ══════════════════════════════════════════════════════════════════════════════
def is_exempt(member) -> bool:
    """Return True if this member should be skipped during cleanup scans."""
    if member.bot:
        return True
    role_names = {r.name for r in member.roles}
    if role_names & EXEMPT_ROLE_NAMES:
        return True
    role_ids = {r.id for r in member.roles}
    if role_ids & EXEMPT_ROLE_IDS:
        return True
    # Too new — respect onboarding window
    min_age_s = CLEANUP_CONFIG["min_join_age_days"] * 86400
    if member.joined_at and (time.time() - member.joined_at.timestamp()) < min_age_s:
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# FLAG CRUD
# ══════════════════════════════════════════════════════════════════════════════
def get_flag(user_id: int):
    """Return the cleanup_flags row for user_id, or None."""
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM cleanup_flags WHERE user_id = ?", (user_id,)
        ).fetchone()


def set_flag(
    user_id:      int,
    display_name: str,
    flag_type:    str,
    reason:       str,
    health_score: int  = 0,
    health_tier:  str  = "",
    days_inactive: int = 0,
    is_verified:  bool = False,
    meet_count:   int  = 0,
) -> None:
    """Upsert a flag. Preserves reminders_sent / flagged_at if already exists."""
    now  = time.time()
    cfg  = CLEANUP_CONFIG
    if flag_type == FLAG_GHOST:
        grace = cfg["grace_period_ghost"] * 86400
    elif flag_type == FLAG_AT_RISK:
        grace = cfg["grace_period_at_risk"] * 86400
    else:
        grace = 0
    grace_expires = now + grace

    existing = get_flag(user_id)
    if existing and existing["recovered"]:
        return  # already recovered — don't re-flag until scan resets it

    if existing:
        # Update fields but keep reminders_sent and flagged_at intact
        with _conn() as conn:
            conn.execute(
                """UPDATE cleanup_flags
                   SET display_name=?, flag_type=?, grace_expires_at=?,
                       reason=?, health_score=?, health_tier=?,
                       days_inactive=?, is_verified=?, meet_count=?
                   WHERE user_id=?""",
                (
                    display_name, flag_type, grace_expires,
                    reason, health_score, health_tier,
                    days_inactive, int(is_verified), meet_count,
                    user_id,
                ),
            )
    else:
        with _conn() as conn:
            conn.execute(
                """INSERT INTO cleanup_flags
                   (user_id, display_name, flag_type, flagged_at, grace_expires_at,
                    reminders_sent, review_state, recovered, reason,
                    health_score, health_tier, days_inactive, is_verified, meet_count)
                   VALUES (?,?,?,?,?, 0,'Pending',0,?, ?,?,?,?,?)""",
                (
                    user_id, display_name, flag_type, now, grace_expires,
                    reason, health_score, health_tier,
                    days_inactive, int(is_verified), meet_count,
                ),
            )


def clear_flag(user_id: int) -> bool:
    """Delete the flag row entirely. Returns True if something was deleted."""
    with _conn() as conn:
        cur = conn.execute("DELETE FROM cleanup_flags WHERE user_id=?", (user_id,))
        return cur.rowcount > 0


def mark_recovered(user_id: int) -> None:
    """Mark a flagged member as recovered (sets flag_type→Safe, review_state→Keep)."""
    with _conn() as conn:
        conn.execute(
            """UPDATE cleanup_flags
               SET recovered=1, recovered_at=?, review_state='Keep', flag_type='Safe'
               WHERE user_id=?""",
            (time.time(), user_id),
        )


def set_review_decision(user_id: int, decision: str) -> None:
    """Set staff review decision: Keep / Monitor / Remove / Re-engage Again."""
    with _conn() as conn:
        conn.execute(
            "UPDATE cleanup_flags SET review_state=?, action_taken=? WHERE user_id=?",
            (decision, decision, user_id),
        )


# ══════════════════════════════════════════════════════════════════════════════
# REMINDER HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def should_send_reminder(user_id: int) -> bool:
    """True if this member is eligible for another reminder DM right now."""
    row = get_flag(user_id)
    if not row or row["recovered"]:
        return False
    if row["reminders_sent"] >= CLEANUP_CONFIG["max_reminders"]:
        return False
    cooldown = CLEANUP_CONFIG["reminder_cooldown_days"] * 86400
    last = row["last_reminder_at"]
    if last and (time.time() - last) < cooldown:
        return False
    return True


def record_reminder_sent(user_id: int) -> None:
    """Increment reminder count and stamp last_reminder_at."""
    with _conn() as conn:
        conn.execute(
            """UPDATE cleanup_flags
               SET reminders_sent=reminders_sent+1, last_reminder_at=?
               WHERE user_id=?""",
            (time.time(), user_id),
        )


# ══════════════════════════════════════════════════════════════════════════════
# QUERIES FOR COMMANDS
# ══════════════════════════════════════════════════════════════════════════════
def get_review_queue():
    """All members whose grace period expired and who are not yet recovered."""
    now = time.time()
    with _conn() as conn:
        return conn.execute(
            """SELECT * FROM cleanup_flags
               WHERE recovered=0 AND (flag_type=? OR grace_expires_at < ?)
               ORDER BY health_score ASC""",
            (FLAG_REVIEW, now),
        ).fetchall()


def get_recoveries(limit: int = 25):
    """Members who recovered after being flagged, most recent first."""
    with _conn() as conn:
        return conn.execute(
            """SELECT * FROM cleanup_flags
               WHERE recovered=1
               ORDER BY recovered_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()


def get_all_active_flags():
    """Every non-recovered flag, lowest score first."""
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM cleanup_flags WHERE recovered=0 ORDER BY health_score ASC"
        ).fetchall()


def log_action(
    user_id: int, display_name: str,
    action: str, performed_by: str, notes: str = ""
) -> None:
    with _conn() as conn:
        conn.execute(
            """INSERT INTO action_history
               (user_id, display_name, action, performed_by, notes, created_at)
               VALUES (?,?,?,?,?,?)""",
            (user_id, display_name, action, performed_by, notes, time.time()),
        )


def get_stats() -> dict:
    """Aggregate counts for !cleanupstats."""
    with _conn() as conn:
        def _count(sql, *args):
            return conn.execute(sql, args).fetchone()[0]

        return {
            "total_flagged":  _count("SELECT COUNT(*) FROM cleanup_flags"),
            "recovered":      _count("SELECT COUNT(*) FROM cleanup_flags WHERE recovered=1"),
            "in_review":      _count(
                "SELECT COUNT(*) FROM cleanup_flags WHERE flag_type=? AND recovered=0",
                FLAG_REVIEW,
            ),
            "still_inactive": _count("SELECT COUNT(*) FROM cleanup_flags WHERE recovered=0"),
            "at_risk":        _count(
                "SELECT COUNT(*) FROM cleanup_flags WHERE flag_type=? AND recovered=0",
                FLAG_AT_RISK,
            ),
            "ghost":          _count(
                "SELECT COUNT(*) FROM cleanup_flags WHERE flag_type=? AND recovered=0",
                FLAG_GHOST,
            ),
            "removed":        _count(
                "SELECT COUNT(*) FROM action_history WHERE action='Removed'"
            ),
        }
