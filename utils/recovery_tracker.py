"""
utils/recovery_tracker.py
Track and compute recovery state for members flagged by the cleanup system.
"""

import time

from utils.cleanup_logic import _conn, get_flag, mark_recovered

# Human-readable labels for each event type
RECOVERY_EVENT_LABELS = {
    "message":     "Sent a message",
    "vc_join":     "Joined voice channel",
    "meet_attend": "Attended a meet",
    "verified":    "Completed verification",
    "score_up":    "Health score improved",
    "manual":      "Staff manually marked recovered",
}


def log_recovery_event(user_id: int, event_type: str) -> None:
    """
    Log a recovery event and auto-mark the member as recovered in cleanup_flags.
    Safe to call even if the member has no flag (no-op in that case).
    """
    with _conn() as conn:
        conn.execute(
            "INSERT INTO recovery_events (user_id, event_type, recorded_at) VALUES (?,?,?)",
            (user_id, event_type, time.time()),
        )
    flag = get_flag(user_id)
    if flag and not flag["recovered"]:
        mark_recovered(user_id)


def get_recovery_events(user_id: int):
    """Return all recovery events for a user, newest first."""
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM recovery_events WHERE user_id=? ORDER BY recorded_at DESC",
            (user_id,),
        ).fetchall()


def compute_recovery_status(user_id: int) -> str:
    """
    Return one of:
      - 'Recovered'           — flag is marked recovered
      - 'Partially Recovered' — events logged but flag not fully cleared
      - 'Still Inactive'      — no events, no recovery
    """
    from utils.cleanup_logic import RECOVERY_FULL, RECOVERY_PARTIAL, RECOVERY_NONE

    flag = get_flag(user_id)
    if not flag:
        return RECOVERY_NONE
    if flag["recovered"]:
        return RECOVERY_FULL
    if get_recovery_events(user_id):
        return RECOVERY_PARTIAL
    return RECOVERY_NONE
