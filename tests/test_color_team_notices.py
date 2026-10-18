"""Offline checks for the optional scheduled Color Team notices."""
import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock


tree = ast.parse(Path("bot.py").read_text())
selected = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == "WEEKLY_COLOR_TEAM_NOTICES_ENABLED"
        for target in node.targets
    ):
        selected.append(node)
    elif getattr(node, "name", None) == "_color_team_send_scheduled_notices":
        selected.append(node)
module = ast.Module(body=selected, type_ignores=[])
compiled = compile(module, "bot.py", "exec")


class ColorTeamNoticeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.send = AsyncMock()
        self.load = Mock(return_value={})
        self.save = Mock()
        self.ns = {
            "_weekly_color_load": self.load,
            "_weekly_color_save": self.save,
            "_weekly_color_today_key": Mock(side_effect=lambda name: f"{name}_key"),
            "_weekly_color_send_or_edit": self.send,
            "_weekly_color_monday_embed": Mock(return_value="monday embed"),
            "_weekly_color_tuesday_embed": Mock(return_value="tuesday embed"),
            "COLOR_SCHEDULE_HOUR": 12,
            "COLOR_TEAM_ROLE_ID": 7,
        }
        exec(compiled, self.ns)
        self.guild = SimpleNamespace(
            get_role=lambda role_id: SimpleNamespace(mention="<@&7>")
        )

    async def test_scheduled_notices_are_disabled_for_both_days(self):
        await self.ns["_color_team_send_scheduled_notices"](
            self.guild, datetime(2026, 10, 12, 12, 0), "2026-10-12"
        )
        await self.ns["_color_team_send_scheduled_notices"](
            self.guild, datetime(2026, 10, 13, 12, 0), "2026-10-13"
        )

        self.send.assert_not_awaited()
        self.load.assert_not_called()

    async def test_notices_post_at_scheduled_times_when_reenabled(self):
        self.ns["WEEKLY_COLOR_TEAM_NOTICES_ENABLED"] = True
        await self.ns["_color_team_send_scheduled_notices"](
            self.guild, datetime(2026, 10, 12, 12, 0), "2026-10-12"
        )
        await self.ns["_color_team_send_scheduled_notices"](
            self.guild, datetime(2026, 10, 13, 12, 0), "2026-10-13"
        )

        self.assertEqual(self.send.await_count, 2)
        self.assertEqual(
            self.send.await_args_list[0].args,
            ("monday_key", "<@&7> Weekly color announced — prep next vote.", "monday embed"),
        )
        self.assertEqual(
            self.send.await_args_list[1].args,
            ("tuesday_key", "<@&7> Voting is live — direct members.", "tuesday embed"),
        )
