"""Offline checks for roll-call layout and weekly reset retention."""
import ast
import asyncio
from datetime import datetime, timedelta, timezone
import re
import sqlite3
from pathlib import Path
import tempfile
import time
import unittest
from zoneinfo import ZoneInfo
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import discord


BOT_SOURCE = Path("bot.py").read_text()
EST = ZoneInfo("America/New_York")


def load_definitions(names, namespace):
    tree = ast.parse(BOT_SOURCE)
    nodes = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name in names
    ]
    missing = names - {node.name for node in nodes}
    if missing:
        raise AssertionError(f"Definitions not found: {sorted(missing)}")
    module = ast.Module(body=nodes, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "bot.py", "exec"), namespace)


class FakeDB:
    def __init__(self, meets):
        self.meets = meets
        self.counts = {}

    def get_meets(self, _guild_id):
        return self.meets

    def get_counts(self, _guild_id, meet_number):
        return self.counts.get(meet_number, {"yes": 0, "maybe": 0, "no": 0})


def scheduled_meet(number, day, ts, finalized=0):
    return {
        "meet_number": number,
        "class_name": f"Class {number}",
        "start_time": "9:00 PM",
        "host_id": None,
        "date_text": day,
        "is_finalized": finalized,
        "scheduled_ts": ts,
    }


class RollCallCycleSafetyTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDB([])
        self.ns = {
            "datetime": datetime,
            "timedelta": timedelta,
            "timezone": timezone,
            "time": time,
            "re": re,
            "discord": discord,
            "_EST_TZ": EST,
            "_rc_db": self.db,
            "_readable_host": lambda _guild, host_id: f"<@{host_id}>" if host_id else "*No host assigned*",
            "DIFF_LOGO_URL": "",
            "_parse_meet_ts": lambda _day, _time: None,
        }
        load_definitions({
            "_rc_meet_schedule_ts",
            "_rc_auto_reset_ready",
            "_rc_build_header_embed",
            "_rc_build_meet_embed",
            "_rc_meet_render_order",
            "_RcBtn",
            "_RollCallDB",
            "_rc_weekly_reset_loop",
        }, self.ns)

    def test_reset_waits_until_monday_after_last_scheduled_meet_week(self):
        last_meet = int(datetime(2026, 10, 21, 21, tzinfo=EST).timestamp())
        self.db.meets = [scheduled_meet(1, "Wednesday", last_meet)]
        in_meet_week = int(datetime(2026, 10, 22, 12, tzinfo=EST).timestamp())
        next_monday = int(datetime(2026, 10, 26, 0, 5, tzinfo=EST).timestamp())

        self.assertFalse(self.ns["_rc_auto_reset_ready"](7, in_meet_week))
        self.assertTrue(self.ns["_rc_auto_reset_ready"](7, next_monday))

    def test_unknown_date_with_responses_blocks_automatic_reset(self):
        self.db.meets = [{
            "meet_number": 1,
            "class_name": "TBD",
            "start_time": "TBD",
            "date_text": "TBD",
            "scheduled_ts": None,
            "is_finalized": 0,
        }]
        self.db.counts[1] = {"yes": 1, "maybe": 0, "no": 0}
        now_ts = int(datetime(2026, 10, 26, 1, tzinfo=EST).timestamp())
        self.assertFalse(self.ns["_rc_auto_reset_ready"](7, now_ts))

        self.db.counts[1] = {"yes": 0, "maybe": 0, "no": 0}
        self.assertTrue(self.ns["_rc_auto_reset_ready"](7, now_ts))

    def test_failed_repost_does_not_repeat_a_committed_reset(self):
        state = {"last_weekly_reset": "2026-10-19"}
        saved = []

        class FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, 26, 0, 5, tzinfo=tz)

        self.ns.update({
            "datetime": FrozenDateTime,
            "asyncio": asyncio,
            "bot": SimpleNamespace(
                wait_until_ready=AsyncMock(),
                get_guild=lambda _guild_id: SimpleNamespace(id=7),
                is_closed=lambda: True,
            ),
            "GUILD_ID": 7,
            "_rc_reminder_state_load": lambda: state,
            "_rc_reminder_state_save": Mock(side_effect=lambda value: saved.append(dict(value))),
            "_rc_auto_reset_ready": Mock(return_value=True),
            "_rc_post_new_panel": AsyncMock(return_value="reset-only"),
        })

        asyncio.run(self.ns["_rc_weekly_reset_loop"]())

        self.assertEqual(state["last_weekly_reset"], "2026-10-26")
        self.assertEqual(saved[0]["last_weekly_reset"], "2026-10-26")

    def test_failed_reset_without_channel_does_not_advance_marker(self):
        state = {"last_weekly_reset": "2026-10-19"}
        save = Mock()
        post = AsyncMock(return_value="failed")
        self.ns.update({
            "datetime": type("FrozenDateTime", (datetime,), {
                "now": classmethod(lambda cls, tz=None: cls(2026, 10, 26, 0, 5, tzinfo=tz)),
            }),
            "asyncio": asyncio,
            "bot": SimpleNamespace(
                wait_until_ready=AsyncMock(),
                get_guild=lambda _guild_id: SimpleNamespace(id=7),
                is_closed=lambda: True,
            ),
            "GUILD_ID": 7,
            "_rc_reminder_state_load": lambda: state,
            "_rc_reminder_state_save": save,
            "_rc_auto_reset_ready": Mock(return_value=True),
            "_rc_post_new_panel": post,
        })

        asyncio.run(self.ns["_rc_weekly_reset_loop"]())

        self.assertEqual(state["last_weekly_reset"], "2026-10-19")
        save.assert_not_called()
        post.assert_awaited_once()

    def test_stored_timestamp_prevents_weekday_roll_forward(self):
        row = {
            "date_text": "Thursday",
            "start_time": "9:00 PM",
            "scheduled_ts": 123456,
        }
        self.assertEqual(self.ns["_rc_meet_schedule_ts"](row), 123456)

    def test_header_and_meet_cards_are_compact_and_use_correct_labels(self):
        first_ts = int(datetime(2026, 10, 21, 21, tzinfo=EST).timestamp())
        second_ts = int(datetime(2026, 10, 22, 21, tzinfo=EST).timestamp())
        self.db.meets = [
            scheduled_meet(1, "Wednesday, October 21, 2026", first_ts),
            scheduled_meet(2, "Thursday, October 22, 2026", second_ts),
            {
                "meet_number": 3,
                "class_name": "TBD",
                "start_time": "TBD",
                "host_id": None,
                "date_text": "TBD",
                "scheduled_ts": None,
                "is_finalized": 0,
            },
        ]
        self.db.counts[1] = {"yes": 2, "maybe": 1, "no": 3}
        guild = type("Guild", (), {"id": 7})()

        header = self.ns["_rc_build_header_embed"](guild)
        card = self.ns["_rc_build_meet_embed"](guild, 1)
        button = self.ns["_RcBtn"](1, "yes", 0)

        self.assertIn(f"<t:{first_ts}:D>", header.description)
        self.assertIn(f"<t:{second_ts}:D>", header.description)
        self.assertNotIn("Week of", header.description)
        self.assertNotIn("Resets <", header.description)
        self.assertEqual(card.title, "Meet 1 · Class 1")
        self.assertEqual([field.name for field in card.fields], ["\u200b", "🗓 When", "👤 Host", "RSVPs"])
        self.assertFalse(card.fields[1].inline)
        self.assertFalse(card.fields[2].inline)
        self.assertEqual(button.label, "✅ Going")
        self.assertEqual(button.custom_id, "diff_rollcall:1:yes")

    def test_existing_database_gets_timestamp_column_and_keeps_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = sqlite3.connect(f"{tmp}/rollcall.sqlite")
            conn.row_factory = sqlite3.Row
            conn.execute("""
                CREATE TABLE rollcall_meets (
                    guild_id INTEGER NOT NULL,
                    meet_number INTEGER NOT NULL,
                    class_name TEXT NOT NULL DEFAULT 'TBD',
                    start_time TEXT NOT NULL DEFAULT 'TBD',
                    host_id INTEGER,
                    date_text TEXT NOT NULL DEFAULT 'TBD',
                    is_finalized INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (guild_id, meet_number)
                )
            """)
            db = object.__new__(self.ns["_RollCallDB"])
            db.conn = conn
            db._setup()
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(rollcall_meets)")}
            self.assertIn("scheduled_ts", columns)

            db.upsert_meets(7, [{
                "meet_number": 1,
                "class_name": "Camber",
                "start_time": "9:00 PM",
                "date_text": "October 21, 2026",
                "scheduled_ts": 1_792_631_400,
            }])
            self.assertEqual(db.get_meets(7)[0]["scheduled_ts"], 1_792_631_400)
            conn.close()


if __name__ == "__main__":
    unittest.main()
