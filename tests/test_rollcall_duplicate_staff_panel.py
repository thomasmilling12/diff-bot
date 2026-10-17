"""Regression checks for the core/extension roll-call staff-panel writers."""
import ast
import asyncio
import re
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

import discord


NAMES = {"_RcAdminView", "_RcStaffSelect", "_rc_refresh_admin_card", "_rc_refresh_admin_card_locked",
         "_rc_classify_msg", "_rc_staff_lock", "_rc_staff_locks"}
tree = ast.parse(Path("bot.py").read_text())
module = ast.Module(body=[n for n in tree.body
                         if getattr(n, "name", None) in NAMES], type_ignores=[])


async def history(messages):
    for message in messages:
        yield message


def card(message_id, custom_id="diff_rollcall:staff_action", author=42):
    return SimpleNamespace(
        id=message_id, author=SimpleNamespace(id=author),
        components=[SimpleNamespace(children=[SimpleNamespace(custom_id=custom_id)])],
        embeds=[], edit=AsyncMock(), delete=AsyncMock(),
    )


class DuplicateStaffPanelTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.stored = {"admin": 10}
        self.panel = {"admin_message_id": 20}
        self.db = Mock()
        self.db.get_messages.side_effect = lambda guild: dict(self.stored)
        self.db.get_panel.side_effect = lambda guild: dict(self.panel)
        self.db.set_message.side_effect = lambda guild, slot, mid: self.stored.update({slot: mid})
        self.ns = {
            "asyncio": asyncio, "re": re, "discord": discord,
            "_rc_staff_locks": {}, "_rc_db": self.db, "_rc_build_admin_embed": Mock(return_value=discord.Embed()),
        }
        exec(compile(module, "bot.py", "exec"), self.ns)
        self.guild = SimpleNamespace(id=99, me=SimpleNamespace(id=42))

    async def test_stale_ids_edit_one_card_and_delete_only_staff_duplicates(self):
        old = card(20, "diff_rollcall_finalize:select_v2")
        duplicate = card(30)
        meet = card(40, "diff_rollcall:1:yes")
        user_message = card(50, author=7)
        async def fetch(mid):
            if mid == 10:
                raise discord.NotFound(SimpleNamespace(status=404, reason="Missing"), "gone")
            return old
        channel = SimpleNamespace(
            fetch_message=AsyncMock(side_effect=fetch),
            history=lambda **kw: history([user_message, meet, duplicate, old]),
            send=AsyncMock(),
        )
        await self.ns["_rc_refresh_admin_card"](self.guild, channel)
        old.edit.assert_awaited_once()
        duplicate.delete.assert_awaited_once()
        meet.delete.assert_not_awaited()
        user_message.delete.assert_not_awaited()
        channel.send.assert_not_awaited()
        self.db.set_message.assert_called_once_with(99, "admin", 20)

    async def test_scan_failure_never_posts_a_replacement(self):
        card_msg = card(10)
        async def failed_history(**kwargs):
            raise discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "denied")
            yield
        channel = SimpleNamespace(fetch_message=AsyncMock(return_value=card_msg),
                                  history=failed_history, send=AsyncMock())
        with self.assertRaises(discord.Forbidden):
            await self.ns["_rc_refresh_admin_card"](self.guild, channel)
        channel.send.assert_not_awaited()
        card_msg.delete.assert_not_awaited()

    async def test_both_staff_component_generations_are_recovered(self):
        classify = self.ns["_rc_classify_msg"]
        self.assertEqual(classify(card(1, "diff_rollcall:staff_action"), 42), "admin")
        self.assertEqual(classify(card(2, "diff_rollcall_finalize:select_v2"), 42), "admin")
        self.assertEqual(classify(card(3, "diff_rollcall:1:yes"), 42), "meet1")
        self.assertIsNone(classify(card(4, author=5), 42))


if __name__ == "__main__":
    unittest.main()
