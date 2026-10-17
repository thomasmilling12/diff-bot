"""Exercise real Discord components without importing/starting the production bot."""
import ast
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

import discord


NAMES = {
    "_rc_build_admin_embed", "_RcResetConfirmView", "_RcStaffSelect",
    "_RcAdminView", "_rc_refresh_admin_card",
}
tree = ast.parse(Path("bot.py").read_text())
module = ast.Module(body=[node for node in tree.body
                         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                         and node.name in NAMES], type_ignores=[])


class StaffPanelTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = Mock()
        self.counts = {1: {"yes": 2, "maybe": 1, "no": 0},
                       2: {"yes": 1, "maybe": 0, "no": 3},
                       3: {"yes": 0, "maybe": 4, "no": 1}}
        self.db.get_all_counts.return_value = self.counts
        self.ns = {
            "discord": discord, "datetime": datetime, "timezone": timezone,
            "_rc_db": self.db, "_rc_is_admin": lambda user: user.staff,
            "_rc_refresh_panel": AsyncMock(), "_rc_post_new_panel": AsyncMock(),
            "_RcFinalizeModal": Mock(return_value="modal"),
            "_asched_load": lambda: {"days": {"Friday": {"class": "Sports"}}},
            "_asched_slot_ts": lambda entry: entry.get("ts"),
            "_HRSVP_DAYS": ("Friday", "Saturday", "Sunday"),
        }
        exec(compile(module, "bot.py", "exec"), self.ns)
        self.guild = SimpleNamespace(id=99, me=SimpleNamespace(id=42),
                                     get_member=lambda uid: SimpleNamespace(display_name="Member"))
        self.interaction = SimpleNamespace(
            guild=self.guild, user=SimpleNamespace(id=10, staff=True),
            response=SimpleNamespace(send_message=AsyncMock(), send_modal=AsyncMock(),
                                     defer=AsyncMock(), edit_message=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()), edit_original_response=AsyncMock(),
        )

    async def select(self, value):
        select = self.ns["_RcStaffSelect"]()
        select._values = [value]
        await select.callback(self.interaction)

    async def test_summary_and_persistent_dropdown(self):
        embed = self.ns["_rc_build_admin_embed"](self.guild)
        self.assertIn("`3` attending", embed.description)
        self.assertIn("`5` maybe", embed.description)
        self.assertIn("`4` not attending", embed.description)
        self.assertEqual([f.name for f in embed.fields], ["Meet 1", "Meet 2", "Meet 3"])
        self.assertTrue(all(f.inline for f in embed.fields))
        view = self.ns["_RcAdminView"]()
        self.assertTrue(view.is_persistent())
        self.assertEqual(len(view.children), 1)
        self.assertEqual(view.children[0].row, 0)
        self.assertEqual(len(view.children[0].options), 7)
        self.assertEqual(len(view.to_components()), 1)

    async def test_nonstaff_cannot_run_any_action(self):
        self.interaction.user.staff = False
        for action in ("attendance", "sync", "refresh", "reset", "finalize:1"):
            await self.select(action)
        self.ns["_rc_refresh_panel"].assert_not_awaited()
        self.ns["_rc_post_new_panel"].assert_not_awaited()
        self.interaction.response.send_modal.assert_not_awaited()
        self.db.upsert_meets.assert_not_called()

    async def test_finalize_opens_existing_modal(self):
        for n in (1, 2, 3):
            await self.select(f"finalize:{n}")
            self.ns["_RcFinalizeModal"].assert_called_with(n)
        self.assertEqual(self.interaction.response.send_modal.await_count, 3)

    async def test_refresh_preserves_data(self):
        await self.select("refresh")
        self.ns["_rc_refresh_panel"].assert_awaited_once_with(self.guild)
        self.db.reset_week.assert_not_called()
        self.ns["_rc_post_new_panel"].assert_not_awaited()

    async def test_sync_uses_schedule(self):
        await self.select("sync")
        meets = self.db.upsert_meets.call_args.args[1]
        self.assertEqual(len(meets), 3)
        self.assertEqual(meets[0]["class_name"], "Sports")
        self.db.reset_week.assert_not_called()

    async def test_attendance_returns_private_full_breakdown(self):
        self.db.get_all_responses.return_value = {
            n: {"yes": [1, 2], "maybe": [], "no": []} for n in (1, 2, 3)
        }
        await self.select("attendance")
        kwargs = self.interaction.followup.send.call_args.kwargs
        self.assertTrue(kwargs["ephemeral"])
        self.assertIn(b"Member (2)", kwargs["file"].fp.read())
        kwargs["file"].close()

    async def test_reset_requires_confirmation_and_cancel_preserves(self):
        await self.select("reset")
        self.ns["_rc_post_new_panel"].assert_not_awaited()
        view = self.interaction.response.send_message.call_args.kwargs["view"]
        await view.children[1].callback(self.interaction)
        self.ns["_rc_post_new_panel"].assert_not_awaited()
        view = self.ns["_RcResetConfirmView"](10)
        self.interaction.user.id = 20
        self.assertFalse(await view.interaction_check(self.interaction))
        self.interaction.user.id = 10
        self.assertTrue(await view.interaction_check(self.interaction))
        await view.children[0].callback(self.interaction)
        self.ns["_rc_post_new_panel"].assert_awaited_once_with(
            self.guild, ping_roles=False, reset=True)

    async def test_refresh_edits_existing_staff_message(self):
        self.db.get_messages.return_value = {"admin": 123}
        message = SimpleNamespace(edit=AsyncMock())
        channel = SimpleNamespace(fetch_message=AsyncMock(return_value=message), send=AsyncMock())
        await self.ns["_rc_refresh_admin_card"](self.guild, channel)
        channel.fetch_message.assert_awaited_once_with(123)
        message.edit.assert_awaited_once()
        channel.send.assert_not_awaited()
        self.db.reset_week.assert_not_called()

    async def test_missing_card_recreated_without_reset(self):
        self.db.get_messages.return_value = {"admin": 123}
        response = SimpleNamespace(status=404, reason="Not Found")
        channel = SimpleNamespace(
            fetch_message=AsyncMock(side_effect=discord.NotFound(response, "missing")),
            send=AsyncMock(return_value=SimpleNamespace(id=456)),
        )
        await self.ns["_rc_refresh_admin_card"](self.guild, channel)
        self.db.set_message.assert_called_once_with(99, "admin", 456)
        self.db.reset_week.assert_not_called()


if __name__ == "__main__":
    unittest.main()
