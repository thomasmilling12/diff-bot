"""Management briefing checks without starting the bot or touching live data."""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import time
import unittest
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

import discord
from utils import reminder_layouts as ui

NAMES = {
    "_mgmt_recent_warnings", "_mgmt_briefing_host_status", "_mgmt_briefing_next_meet",
    "_mgmt_send_daily_briefing", "__mgmt_daily_briefing_loop_logic",
}
tree = ast.parse(Path("bot.py").read_text())
module = ast.Module(body=[n for n in tree.body if getattr(n, "name", None) in NAMES],
                    type_ignores=[])


class BriefingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.channel = SimpleNamespace(send=AsyncMock())
        self.role = SimpleNamespace(members=[SimpleNamespace(id=1, bot=False),
                                            SimpleNamespace(id=2, bot=False)])
        self.guild = SimpleNamespace(id=5, get_role=lambda rid: self.role)
        self.schedule = {"days": {}}
        self.rsvps = {day: {"no": [1, 2]} for day in ("Meet 1", "Meet 2", "Meet 3")}
        self.ns = {
            "discord": discord, "datetime": datetime, "timezone": timezone, "timedelta": timedelta,
            "_EST_TZ": ZoneInfo("America/New_York"), "time": time, "_reminder_ui": ui,
            "HOST_ROLE_ID": 10, "HOST_RSVP_CHANNEL_ID": 20, "GUILD_ID": 5,
            "ROLL_CALL_URL": "https://discord.com/channels/5/30",
            "_HRSVP_DAYS": ("Meet 1", "Meet 2", "Meet 3"),
            "_warnings_load": lambda: {}, "_asched_load": lambda: self.schedule,
            "_asched_slot_ts": lambda slot: slot.get("ts"), "_hrsvp_load": lambda: self.rsvps,
            "_hrsvp_uid": lambda entry: entry, "_om_load_records": lambda: {},
            "_mgmt_channel_obj": AsyncMock(return_value=self.channel),
            "_mgmt_open_join_tickets": lambda guild: [],
            "_mgmt_open_appeal_tickets": lambda guild: [],
            "_mgmt_snapshot_load": lambda: {}, "_mgmt_snapshot_save": Mock(),
            "bot": SimpleNamespace(guilds=[self.guild]),
        }
        exec(compile(module, "bot.py", "exec"), self.ns)

    async def test_empty_snapshot_is_compact_and_has_links(self):
        self.assertTrue(await self.ns["_mgmt_send_daily_briefing"](self.guild))
        kwargs = self.channel.send.call_args.kwargs
        embed = kwargs["embed"]
        self.assertEqual(len(embed.fields), 3)
        self.assertIn("No open join", embed.fields[0].value)
        self.assertEqual(embed.color, discord.Color.green())
        self.assertEqual(len(kwargs["view"].children), 2)
        self.assertEqual(kwargs["allowed_mentions"].to_dict(), {"parse": []})

    async def test_busy_snapshot_preserves_oldest_ticket_and_warning_count(self):
        self.ns["_mgmt_open_join_tickets"] = lambda guild: [(SimpleNamespace(mention="<#123>"), 27)]
        self.ns["_mgmt_recent_warnings"] = lambda **kw: [object()]
        self.rsvps["Meet 2"] = {"no": [2]}
        await self.ns["_mgmt_send_daily_briefing"](self.guild)
        embed = self.channel.send.call_args.kwargs["embed"]
        self.assertIn("<#123> (27h)", embed.fields[0].value)
        self.assertEqual(embed.color, discord.Color.orange())
        self.assertTrue(any(f.name.startswith("Warnings") for f in embed.fields))

    def test_partial_host_availability_is_not_all_responded(self):
        self.rsvps["Meet 2"] = {"yes": [2]}
        pending, label = self.ns["_mgmt_briefing_host_status"](self.guild)
        self.assertEqual(pending, 1)
        self.assertNotIn("All hosts", label)
        self.schedule["days"]["Meet 2"] = {"ts": time.time()-60}
        self.assertEqual(self.ns["_mgmt_briefing_host_status"](self.guild)[0], 0)

    def test_missing_host_role_is_not_all_clear(self):
        self.guild.get_role = lambda rid: None
        pending, label = self.ns["_mgmt_briefing_host_status"](self.guild)
        self.assertIsNone(pending)
        self.assertIn("unavailable", label)

    async def test_next_meet_includes_schedule_and_uses_fixed_timestamp(self):
        ts = int(time.time())+7200
        self.schedule["days"] = {"Meet 1": {"ts": ts, "host_id": 1, "class": "Sports"},
                                 "Meet 2": {"ts": ts-8000, "host_id": 1, "class": "Past"}}
        self.ns["_om_load_records"] = lambda: {
            "bad": {"timestamp": "invalid"}, "past": {"timestamp": ts-9000},
            "later": {"timestamp": ts+3600, "theme": "Later"}, "malformed": None,
        }
        self.assertEqual(self.ns["_mgmt_briefing_next_meet"](), (ts, "Sports"))
        await self.ns["_mgmt_send_daily_briefing"](self.guild)
        embed = self.channel.send.call_args.kwargs["embed"]
        self.assertIn(f"<t:{ts}:F>", embed.fields[-1].value)
        self.assertNotIn(":R>", embed.fields[-1].value)

    def test_formal_warnings_skip_malformed_and_old_entries(self):
        now = datetime.now(timezone.utc)
        self.ns["_warnings_load"] = lambda: {
            "1": [{"timestamp": now.isoformat(), "id": "current"},
                  {"timestamp": (now-timedelta(days=2)).isoformat()},
                  {"timestamp": "invalid"}, None],
            "bad": None,
        }
        warnings = self.ns["_mgmt_recent_warnings"](days=1)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["id"], "current")

    async def test_missing_channel_is_unsent(self):
        self.ns["_mgmt_channel_obj"] = AsyncMock(return_value=None)
        self.assertFalse(await self.ns["_mgmt_send_daily_briefing"](self.guild))
        self.channel.send.assert_not_awaited()

    async def test_daily_marker_only_after_success_and_merges_fresh_state(self):
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, 17, 9, 6, tzinfo=tz)
        self.ns["datetime"] = Clock
        self.ns["_mgmt_snapshot_load"] = lambda: {"other_flag": "keep"}
        sender = AsyncMock(side_effect=RuntimeError("send failed"))
        self.ns["_mgmt_send_daily_briefing"] = sender
        await self.ns["__mgmt_daily_briefing_loop_logic"]()
        self.ns["_mgmt_snapshot_save"].assert_not_called()
        sender.side_effect = None
        sender.return_value = False
        await self.ns["__mgmt_daily_briefing_loop_logic"]()
        self.ns["_mgmt_snapshot_save"].assert_not_called()
        sender.return_value = True
        await self.ns["__mgmt_daily_briefing_loop_logic"]()
        saved = self.ns["_mgmt_snapshot_save"].call_args.args[0]
        self.assertEqual(saved, {"other_flag": "keep", "_briefing_sent": "2026-10-17"})


if __name__ == "__main__":
    unittest.main()
