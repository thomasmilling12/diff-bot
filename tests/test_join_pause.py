"""Offline join-pause regression tests; never import or connect the main bot."""
import ast
import asyncio
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

import discord
from discord.ext import commands

from cogs import diff_unverified_panel as unverified
from cogs import diff_welcome_join as welcome
from utils import join_pause
from utils.activity_pause import ActivityPause, command_domain, symbol_domain


TREE = ast.parse(Path("bot.py").read_text())


def extract(name, owner=None):
    body = TREE.body
    if owner:
        body = next(n for n in body if getattr(n, "name", None) == owner).body
    node = next(n for n in body if getattr(n, "name", None) == name)
    # Execute only the requested definitions, not root bot startup/decorators.
    import copy
    node = copy.deepcopy(node)
    node.decorator_list = []
    return node


def interaction(bot, done=False):
    member = Mock(spec=discord.Member)
    member.roles = []
    member.add_roles = AsyncMock()
    member.remove_roles = AsyncMock()
    guild = Mock()
    return SimpleNamespace(
        client=bot, user=member, guild=guild,
        response=SimpleNamespace(
            is_done=lambda: done, send_message=AsyncMock(),
            defer=AsyncMock(), send_modal=AsyncMock(),
        ),
        followup=SimpleNamespace(send=AsyncMock()),
    )


class JoinPauseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.state = SimpleNamespace(paused={"meets": True, "colors": True})
        self.bot = SimpleNamespace(_activity_pause=self.state, get_guild=Mock(return_value=None))
        self.ns = {
            "__name__": "offline_join_bot", "discord": discord, "commands": commands,
            "_join_pause": join_pause, "bot": self.bot, "asyncio": asyncio,
            "RULES_CHANNEL_ID": 100, "NOTIFY_ROLE_ID": 10, "MIN_GARAGE_PHOTOS": 3,
            "_JOIN_MMI_INVITE": "https://example.invalid/partner",
            "_compute_join_panel_stats": lambda guild: {},
            "_SELECT_TYPES": (discord.ui.Select,), "_wrap_select_for_reset": lambda item: None,
            "_CarRequirementsButton": lambda **kw: discord.ui.Button(label="Requirements", row=1),
            "datetime": datetime, "_join_ticket_tasks": {},
        }

    def load(self, *names):
        nodes = [extract(name) for name in names]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "<join pause>", "exec"), self.ns)

    async def test_guard_returns_private_notice_without_mentions_even_if_deferred(self):
        for done in (False, True):
            value = interaction(self.bot, done)
            self.assertFalse(await join_pause.allow_application(value))
            sender = value.followup.send if done else value.response.send_message
            args = sender.await_args
            self.assertTrue(args.kwargs["ephemeral"])
            self.assertFalse(args.kwargs["allowed_mentions"].everyone)
            self.assertIn(join_pause.APPLICATION_NOTICE, args.args[0])
        self.state.paused["meets"] = False
        self.assertTrue(await join_pause.allow_application(interaction(self.bot)))

    async def test_old_application_select_does_not_open_modal(self):
        self.load("JoinPlatformSelect")
        value = interaction(self.bot)
        select = self.ns["JoinPlatformSelect"]()
        select._values = ["playstation"]
        await select.callback(value)
        value.response.send_modal.assert_not_awaited()
        value.guild.get_channel.assert_not_called()
        value.user.add_roles.assert_not_awaited()
        self.assertIn("on hold", value.response.send_message.await_args.args[0])
        self.assertEqual(select.custom_id, "diff_join_platform_select")

    async def test_old_application_form_cannot_create_ticket_or_change_member(self):
        self.load("JoinPsnModal")
        value = interaction(self.bot)
        modal = self.ns["JoinPsnModal"]()
        await modal.on_submit(value)
        value.response.defer.assert_not_awaited()
        value.guild.create_text_channel.assert_not_called()
        value.user.add_roles.assert_not_awaited()
        value.user.edit.assert_not_called()

    async def test_all_notification_button_routes_hold_only_meet_roles(self):
        self.load("_notify_toggle_role")
        value = interaction(self.bot)
        await self.ns["_notify_toggle_role"](value, 10, "Meets", "bell")
        value.user.add_roles.assert_not_awaited()
        value.user.remove_roles.assert_not_awaited()
        for role_id in (11, 12):
            value = interaction(self.bot)
            await self.ns["_notify_toggle_role"](value, role_id, "Other", "bell")
            value.user.add_roles.assert_awaited_once()
        self.state.paused["meets"] = False
        value = interaction(self.bot)
        await self.ns["_notify_toggle_role"](value, 10, "Meets", "bell")
        value.user.add_roles.assert_awaited_once()

    async def test_join_panel_notification_button_preserves_roles(self):
        self.load("JoinPlatformSelect", "JoinPlatformView")
        value = interaction(self.bot)
        view = self.ns["JoinPlatformView"]()
        await view.notify_toggle.callback(value)
        value.user.add_roles.assert_not_awaited()
        value.user.remove_roles.assert_not_awaited()
        self.assertEqual(view.notify_toggle.custom_id, "diff_join_notify")
        self.assertIn("on hold", next(c.placeholder for c in view.children
                                     if isinstance(c, discord.ui.Select)))

    async def test_notification_prefix_aliases_cannot_bypass_pause(self):
        self.load("_cmd_notify")
        self.ns["_NOTIFY_ROLES"] = {"meets": (10, "Meets", "bell"),
                                    "carmeet": (10, "Meets", "bell"),
                                    "media": (11, "Media", "camera")}
        for name in ("meets", "carmeet"):
            value = interaction(self.bot)
            ctx = SimpleNamespace(
                author=value.user, guild=value.guild, reply=AsyncMock(),
                message=SimpleNamespace(delete=AsyncMock()),
            )
            await self.ns["_cmd_notify"](ctx, name)
            value.user.add_roles.assert_not_awaited()
            value.user.remove_roles.assert_not_awaited()
            self.assertIn("paused", ctx.reply.await_args.args[0])

    async def test_pause_hub_text_keeps_image_and_resumes_original_instructions(self):
        self.load("_join_build_panel_embed")
        embed = self.ns["_join_build_panel_embed"]()
        self.assertIn(join_pause.APPLICATION_NOTICE, embed.description)
        self.assertNotIn("start your join ticket", embed.description)
        self.assertTrue(embed.image.url)
        self.assertIn("JOIN HUB", embed.title)
        self.state.paused["meets"] = False
        self.assertIn("start your join ticket", self.ns["_join_build_panel_embed"]().description)

    async def test_startup_notice_edits_existing_message_without_posting_or_deleting(self):
        self.load("_join_build_panel_embed", "_join_refresh_pause_notice")
        self.ns["JOIN_PANEL_CHANNEL_ID"] = 123
        self.ns["JoinPlatformView"] = lambda: "existing-view"
        self.bot.user = SimpleNamespace(id=20)
        msg = SimpleNamespace(
            author=SimpleNamespace(id=20), embeds=[discord.Embed(title="DIFF — JOIN HUB")],
            edit=AsyncMock(), delete=AsyncMock(),
        )
        async def history(**kwargs):
            yield msg
        channel = SimpleNamespace(history=history, guild=None, send=AsyncMock())
        self.bot.get_channel = lambda cid: channel
        await self.ns["_join_refresh_pause_notice"]()
        msg.edit.assert_awaited_once()
        msg.delete.assert_not_awaited()
        channel.send.assert_not_awaited()
        self.assertIn("on hold", msg.edit.await_args.kwargs["embed"].description)
        async def empty_history(**kwargs):
            if False:
                yield None
        channel.history = empty_history
        await self.ns["_join_refresh_pause_notice"]()
        channel.send.assert_not_awaited()

    async def test_existing_idle_timer_cannot_delete_ticket_when_pause_starts_during_sleep(self):
        self.load("_join_idle_timer")
        channel = SimpleNamespace(send=AsyncMock(), delete=AsyncMock())
        with patch("asyncio.sleep", new=AsyncMock()):
            await self.ns["_join_idle_timer"](channel, Mock())
        channel.send.assert_not_awaited()
        channel.delete.assert_not_awaited()

    async def test_idle_timer_rechecks_pause_at_each_later_sleep(self):
        self.load("_join_idle_timer")
        for pause_at in (2, 3):
            self.state.paused["meets"] = False
            sleeps = 0
            async def sleep(delay):
                nonlocal sleeps
                sleeps += 1
                if sleeps == pause_at:
                    self.state.paused["meets"] = True
            async def history(**kwargs):
                if False:
                    yield None
            channel = SimpleNamespace(
                id=123, history=history, send=AsyncMock(), delete=AsyncMock(),
            )
            with patch("asyncio.sleep", new=sleep):
                await self.ns["_join_idle_timer"](channel, Mock())
            channel.delete.assert_not_awaited()
            self.assertEqual(sleeps, pause_at)

    async def test_unverified_auto_ping_touches_no_markers_or_discord_while_paused(self):
        cog = object.__new__(unverified.UnverifiedPanelCog)
        cog.bot = self.bot
        cog._get_channel = AsyncMock(return_value=None)
        with patch.object(unverified, "_get_last_reminder_ts") as load, \
                patch.object(unverified, "_set_last_reminder_ts") as save:
            await cog._daily_auto_ping()
        load.assert_not_called()
        save.assert_not_called()
        cog._get_channel.assert_not_awaited()
        self.state.paused["meets"] = False
        with patch.object(unverified, "_get_last_reminder_ts", return_value=0):
            await cog._daily_auto_ping()
        cog._get_channel.assert_awaited_once()

    async def test_checkin_reminder_keeps_db_untouched_but_verification_progress_remains(self):
        cog = object.__new__(welcome.DiffWelcomeJoinSystem)
        cog.bot = self.bot
        self.bot.wait_until_ready = AsyncMock()
        cog.db = Mock()
        await cog.reminder_loop()
        cog.db.reminder_candidates.assert_not_called()
        cog.db.mark_reminder_sent.assert_not_called()
        state = SimpleNamespace(has_verified_role=True)
        embed = cog.build_progress_embed(Mock(), state)
        self.assertEqual(embed.fields[-1].value, "Verified")
        self.assertNotIn(str(welcome.JOIN_MEETS_HUB_CHANNEL_ID), str(embed.to_dict()))
        self.assertIn(str(welcome.RULES_CHANNEL_ID), str(embed.to_dict()))

    async def test_verification_panel_preserves_rules_instructions_and_existing_staff_controls(self):
        cog = object.__new__(unverified.UnverifiedPanelCog)
        cog.bot = self.bot
        embed = cog._build_embed()
        self.assertIn("Verify", str(embed.to_dict()))
        self.assertNotIn(str(unverified.JOIN_MEETS_CHANNEL), str(embed.to_dict()))
        ids = [c.custom_id for c in unverified.UnverifiedPingView().children]
        self.assertEqual(ids, ["diff_unverified_ping_v2", "diff_unverified_list_v2"])
        self.state.paused["meets"] = False
        self.assertIn(str(unverified.JOIN_MEETS_CHANNEL), str(cog._build_embed().to_dict()))

    async def test_manual_reminder_text_does_not_advertise_closed_meet_applications(self):
        embed = unverified._build_reminder_embed("Staff", paused=True)
        self.assertNotIn(str(unverified.JOIN_MEETS_CHANNEL), str(embed.to_dict()))
        self.assertIn("Verify", str(embed.to_dict()))
        self.assertIn(join_pause.APPLICATION_NOTICE, str(embed.to_dict()))

    async def test_staff_ping_and_member_list_keep_original_permission_checks(self):
        value = interaction(self.bot)
        value.user.roles = []
        value.user.guild_permissions = SimpleNamespace(manage_guild=False, administrator=False)
        for button in (unverified.PingButton(), unverified.ListUnverifiedButton()):
            await button.callback(value)
        value.response.defer.assert_not_awaited()
        value.guild.get_role.assert_not_called()
        self.assertEqual(value.response.send_message.await_count, 2)

    async def test_only_selected_reminder_jobs_are_wrapped_not_verification_or_review(self):
        self.load("_unverified_dm_reminder_logic")
        state = ActivityPause("/unused-offline-pause-file", Mock())
        state.protect_namespace(self.ns, self.ns["__name__"], main=True)
        await self.ns["_unverified_dm_reminder_logic"]()
        self.bot.get_guild.assert_not_called()
        for name in ("_join_auto_bump_loop", "__join_micro_bump_logic",
                     "_unverified_dm_reminder_loop", "__stale_join_alert_task_logic"):
            self.assertEqual(symbol_domain(name), "meets")
        for name in ("JoinTicketView", "VerifyView", "CheckInView", "UnverifiedPingView",
                     "ListUnverifiedButton"):
            self.assertIsNone(symbol_domain(name))
        for name in ("verify", "refresh-join-panel", "refresh_unverified_panel", "previewwelcome"):
            self.assertIsNone(command_domain(SimpleNamespace(name=name)))
