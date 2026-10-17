"""Offline checks for the compact auto-schedule builder panel."""
import ast
from datetime import datetime, timezone
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
from unittest.mock import patch

import discord

from utils import reminder_layouts


BOT_SOURCE = Path("bot.py").read_text()


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


class ScheduleBuilderLayoutTests(unittest.TestCase):
    def test_upcoming_then_unscheduled_then_past_and_stable_ids(self):
        schedule = {
            "days": {
                "Meet 1": {"ts": 200, "host_id": "11", "host_status": "yes", "class": "Caber"},
                "Meet 2": {"ts": 20, "host_id": "22", "host_status": "yes", "class": "Cars"},
                "Meet 3": {"host_id": None, "class": "TBD"},
            }
        }
        ns = {
            "discord": discord,
            "time": time,
            "_HRSVP_DAYS": ["Meet 1", "Meet 2", "Meet 3"],
            "_asched_load": lambda: schedule,
            "_asched_slot_ts": lambda entry: entry.get("ts"),
            "_hrsvp_load": lambda: {},
            "_readable_host": lambda _guild, uid: f"<@{uid}>" if uid else None,
            "_hrsvp_uid": lambda item: item["uid"],
            "_reminder_ui": reminder_layouts,
            "utc_now": lambda: datetime.now(timezone.utc),
            "DIFF_LOGO_URL": "",
        }
        load_definitions({
            "_asched_console_order",
            "_asched_build_console_header_embed",
            "_asched_build_console_meet_embed",
        }, ns)

        with patch("time.time", return_value=100):
            self.assertEqual(
                ns["_asched_console_order"](schedule, now_ts=100),
                ["Meet 1", "Meet 3", "Meet 2"],
            )
            header = ns["_asched_build_console_header_embed"]()
            past_card = ns["_asched_build_console_meet_embed"](2, "Meet 2")

        self.assertEqual(header.title, "Weekly Schedule Builder")
        self.assertIn("1/2 upcoming assigned", header.description)
        self.assertIn("1 past", header.description)
        self.assertEqual(header.fields, [])
        self.assertIn("**Past**", past_card.description)
        self.assertNotIn("Confirmed", past_card.description)
        self.assertNotIn("<t:20:R>", past_card.description)
        self.assertEqual(past_card.title, "Meet 2")

    def test_compact_controls_and_legacy_button_ids(self):
        ns = {
            "discord": discord,
            "_ASCHED_REFRESH_ID": "diff_auto_sched_refresh",
            "_ASCHED_REBUILD_ID": "diff_auto_sched_rebuild",
            "_ASCHED_SUBMIT_ID": "diff_auto_sched_submit",
            "_LEADERSHIP_HOST_ROLE_IDS": {1},
            "_LEADERSHIP_ROLE_IDS": {1},
        }
        load_definitions({
            "_ASchedReminderBtn",
            "_ASchedOverrideBtn",
            "_ASchedSubmitBtn",
            "_ASchedPingNonRespondersBtn",
            "_ASchedRefreshBtn",
            "_ASchedMoreActionsSelect",
            "AutoScheduleView",
            "_ASchedLegacyActionsView",
        }, ns)
        view = ns["AutoScheduleView"]()
        children = view.children
        custom_ids = {item.custom_id for item in children}
        self.assertEqual(
            custom_ids,
            {
                "diff_auto_sched_rebuild",
                "diff_asched_override",
                "diff_auto_sched_submit",
                "diff_auto_sched_more",
            },
        )
        menu = next(item for item in children if isinstance(item, discord.ui.Select))
        self.assertEqual(menu.row, 1)
        self.assertEqual(len([item for item in children if item.row == 0]), 3)
        legacy_ids = {item.custom_id for item in ns["_ASchedLegacyActionsView"]().children}
        self.assertEqual(
            legacy_ids,
            {
                "diff_auto_sched_refresh",
                "diff_auto_sched_remind",
                "diff_asched_ping_nonresponders",
            },
        )

    def test_more_actions_route_to_existing_callbacks(self):
        calls = []

        class StubAction:
            async def callback(self, _interaction):
                calls.append(type(self).__name__)

        ns = {
            "discord": discord,
            "_ASCHED_REFRESH_ID": "diff_auto_sched_refresh",
            "_ASCHED_REBUILD_ID": "diff_auto_sched_rebuild",
            "_ASCHED_SUBMIT_ID": "diff_auto_sched_submit",
            "_LEADERSHIP_HOST_ROLE_IDS": {1},
            "_LEADERSHIP_ROLE_IDS": {1},
            "_ASchedRefreshBtn": type("Refresh", (StubAction,), {}),
            "_ASchedReminderBtn": type("Reminder", (StubAction,), {}),
            "_ASchedPingNonRespondersBtn": type("Ping", (StubAction,), {}),
        }
        load_definitions({"_ASchedMoreActionsSelect"}, ns)
        select = ns["_ASchedMoreActionsSelect"]()

        async def exercise():
            for value in ("refresh", "reminders", "nonresponders"):
                select._values = [value]
                await select.callback(object())

        import asyncio
        asyncio.run(exercise())
        self.assertEqual(calls, ["Refresh", "Reminder", "Ping"])

    def test_reordering_edits_existing_messages_and_preserves_meet_data(self):
        import asyncio

        schedule = {
            "days": {
                "Meet 1": {"host_id": "11", "class": "Caber"},
                "Meet 2": {"host_id": "22", "class": "Cars", "ts": 20},
                "Meet 3": {"host_id": "33", "class": "Bennys cars", "ts": 200},
            },
            "console_message_ids": {
                "header": 10,
                "Meet 1": 20,
                "Meet 2": 30,
                "Meet 3": 40,
            },
        }
        original_days = {day: dict(entry) for day, entry in schedule["days"].items()}
        messages = {
            10: SimpleNamespace(edit=AsyncMock()),
            20: SimpleNamespace(edit=AsyncMock()),
            30: SimpleNamespace(edit=AsyncMock()),
            40: SimpleNamespace(edit=AsyncMock()),
        }

        class FakeChannel:
            def __init__(self):
                self.send = AsyncMock()

            async def fetch_message(self, message_id):
                return messages[message_id]

        channel = FakeChannel()
        ns = {
            "discord": discord,
            "time": time,
            "_HRSVP_DAYS": ["Meet 1", "Meet 2", "Meet 3"],
            "_asched_load": lambda: schedule,
            "_asched_save": lambda _schedule: None,
            "_asched_get_console_ids": lambda s: dict(s["console_message_ids"]),
            "_asched_resolve_console_channel": AsyncMock(return_value=channel),
            "_asched_build_console_header_embed": lambda: "header",
            "_asched_build_console_meet_embed": lambda idx, day: f"Meet {idx} / {day}",
            "_asched_slot_ts": lambda entry: entry.get("ts"),
            "_asched_render_console": AsyncMock(),
            "AutoScheduleView": lambda _client: "view",
        }
        load_definitions({"_asched_console_order", "_asched_update_panel"}, ns)

        with patch("time.time", return_value=100):
            asyncio.run(ns["_asched_update_panel"](object()))

        self.assertEqual(schedule["console_message_ids"], {
            "header": 10,
            "Meet 1": 30,
            "Meet 2": 40,
            "Meet 3": 20,
        })
        self.assertEqual(
            [messages[mid].edit.await_args.kwargs["embed"] for mid in (20, 30, 40)],
            ["Meet 3 / Meet 3", "Meet 1 / Meet 1", "Meet 2 / Meet 2"],
        )
        self.assertEqual(schedule["days"], original_days)
        channel.send.assert_not_awaited()
        ns["_asched_render_console"].assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
