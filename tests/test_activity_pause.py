"""Offline pause coverage: no bot import, Discord connection, or feature-data writes."""
import ast
import asyncio
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock

import discord
from discord.ext import commands, tasks

from utils.activity_pause import ActivityPause, command_domain, symbol_domain


def writer(path, value):
    Path(path).write_text(json.dumps(value))


def interaction(done=False):
    return SimpleNamespace(
        response=SimpleNamespace(is_done=lambda: done, send_message=AsyncMock()),
        followup=SimpleNamespace(send=AsyncMock()),
    )


class ActivityPauseTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "activity_pause.json"
        self.state = ActivityPause(self.path, writer)

    async def test_default_pauses_both_without_writing_any_data(self):
        self.assertEqual(self.state.paused, {"meets": True, "colors": True})
        self.assertFalse(self.path.exists())

    async def test_resume_and_pause_survive_restarts_independently(self):
        self.state.set_paused(["meets"], False)
        restored = ActivityPause(self.path, writer)
        self.assertEqual(restored.paused, {"meets": False, "colors": True})
        restored.set_paused(["meets"], True)
        self.assertEqual(ActivityPause(self.path, writer).paused,
                         {"meets": True, "colors": True})

    async def test_invalid_or_unreadable_state_fails_closed(self):
        for data in ('{bad json', '{"version":1,"paused":{"meets":false}}',
                     '{"version":1,"paused":{"meets":"no","colors":false}}'):
            self.path.write_text(data)
            with self.assertLogs("utils.activity_pause", level="ERROR"):
                restored = ActivityPause(self.path, writer)
            self.assertEqual(restored.paused, {"meets": True, "colors": True})
            self.assertIsNotNone(restored.load_error)
            self.assertEqual(self.path.read_text(), data)

    async def test_failed_save_does_not_change_state_or_release_jobs(self):
        self.state.writer = Mock(side_effect=OSError("disk full"))
        with self.assertRaises(OSError):
            self.state.set_paused(["meets"], False)
        self.assertTrue(self.state.paused["meets"])
        self.assertFalse(self.state._running["meets"].is_set())

    async def test_bad_domain_cannot_create_uncontrolled_setting(self):
        for domains in (["bad"], [], ["meets", "bad"]):
            with self.assertRaises(ValueError):
                self.state.set_paused(domains, False)
        self.assertFalse(self.path.exists())

    async def test_suspended_long_running_job_resumes_without_restarting(self):
        reached = AsyncMock()

        async def work():
            await self.state.wait_until_running("meets")
            await reached()
        task = asyncio.create_task(work())
        await asyncio.sleep(0)
        reached.assert_not_awaited()
        self.state.set_paused(["colors"], False)
        await asyncio.sleep(0)
        reached.assert_not_awaited()
        self.state.set_paused(["meets"], False)
        await asyncio.wait_for(task, 1)
        reached.assert_awaited_once()

    async def test_wrapped_job_skips_work_without_mutating_records_or_markers(self):
        data = {"votes": [1, 2], "last_sent": None, "schedule": {"host_id": 42}}
        before = copy.deepcopy(data)

        async def work():
            data["last_sent"] = 100
            data["votes"].clear()
            return 7
        guarded = self.state.wrap_action(work, "colors")
        self.assertIsNone(await guarded())
        self.assertEqual(data, before)
        self.state.set_paused(["colors"], False)
        self.assertEqual(await guarded(), 7)

    async def test_old_buttons_and_modals_receive_private_pause_notice(self):
        for base in (discord.ui.View, discord.ui.Modal):
            class ExistingControl(base):
                async def interaction_check(self, value):
                    self.original_called = True
                    return False
            self.state.protect_view(ExistingControl, "meets")
            control = ExistingControl(title="Test") if base is discord.ui.Modal else ExistingControl()
            value = interaction()
            self.assertFalse(await control.interaction_check(value))
            self.assertFalse(hasattr(control, "original_called"))
            payload = value.response.send_message.await_args
            self.assertTrue(payload.kwargs["ephemeral"])
            self.assertFalse(payload.kwargs["allowed_mentions"].everyone)
            self.assertIn("temporarily paused", payload.args[0])
            self.state.set_paused(["meets"], False)
            self.assertFalse(await control.interaction_check(interaction()))
            self.assertTrue(control.original_called)  # Original permissions still decide.
            self.state.set_paused(["meets"], True)

    async def test_deferred_interaction_uses_private_followup(self):
        value = interaction(done=True)
        self.assertFalse(await self.state.interaction_allowed(value, "colors"))
        value.response.send_message.assert_not_awaited()
        self.assertTrue(value.followup.send.await_args.kwargs["ephemeral"])

    async def test_guard_keeps_existing_ids_and_does_not_wrap_twice(self):
        class ExistingView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                self.add_item(discord.ui.Button(custom_id="existing_vote_id", label="Vote"))
        self.state.protect_view(ExistingView, "colors")
        original_check = ExistingView.interaction_check
        self.state.protect_view(ExistingView, "colors")
        self.assertIs(ExistingView.interaction_check, original_check)
        self.assertEqual(ExistingView().children[0].custom_id, "existing_vote_id")

    async def test_loop_skips_one_tick_but_is_not_cancelled(self):
        calls = AsyncMock()

        @tasks.loop(seconds=1)
        async def _asched_refresh_loop():
            await calls()
        namespace = {"_asched_refresh_loop": _asched_refresh_loop}
        self.state.protect_namespace(namespace, __name__, main=True)
        await _asched_refresh_loop()
        calls.assert_not_awaited()
        self.state.set_paused(["meets"], False)
        await _asched_refresh_loop()
        calls.assert_awaited_once()

    async def test_mixed_cog_only_pauses_meet_job_not_moderation_or_backups(self):
        class MixedCog:
            __module__ = "cogs.diff_advanced_features"

            @tasks.loop(seconds=1)
            async def _reminder_check(self):
                self.reminder_ran = True

            @tasks.loop(seconds=1)
            async def _daily_backup(self):
                self.backup_ran = True
        cog = MixedCog()
        bot = SimpleNamespace(extensions={}, cogs={"mixed": cog})
        self.state.protect_cogs(bot)
        await cog._reminder_check()
        self.assertFalse(hasattr(cog, "reminder_ran"))
        await cog._daily_backup()
        self.assertTrue(cog.backup_ran)

    async def test_commands_permissions_status_and_independent_resume(self):
        bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
        self.addAsyncCleanup(bot.close)
        self.state.install_commands(bot, {20})
        member = SimpleNamespace(roles=[], guild_permissions=SimpleNamespace(administrator=False))
        ctx = SimpleNamespace(author=member, send=AsyncMock())
        resume = bot.get_command("resumeactivities")
        await resume.callback(ctx, "both")
        self.assertEqual(ctx.send.await_args.args[0], "Leadership only.")
        self.assertTrue(all(self.state.paused.values()))
        member.roles = [SimpleNamespace(id=20)]
        await resume.callback(ctx, "meets")
        self.assertTrue(all(self.state.paused.values()))
        self.assertIn("normal weekly resets", ctx.send.await_args.args[0])
        await resume.callback(ctx, "meets", "confirm")
        self.assertEqual(self.state.paused, {"meets": False, "colors": True})
        await bot.get_command("activitystatus").callback(ctx)
        status = ctx.send.await_args.args[0]
        self.assertIn("Car meets:** RUNNING", status)
        self.assertIn("Crew colors:** PAUSED", status)
        await bot.get_command("pauseactivities").callback(ctx, "meets")
        self.assertTrue(all(self.state.paused.values()))
        await resume.callback(ctx, "invalid", "confirm")
        self.assertTrue(all(self.state.paused.values()))
        self.assertEqual(len(bot.commands), 4)  # These three plus standard help.

    async def test_prefix_and_slash_gates_do_not_stop_moderation(self):
        bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
        self.addAsyncCleanup(bot.close)
        self.state.install_commands(bot, {20})
        check = bot._checks[-1]
        ctx = SimpleNamespace(command=SimpleNamespace(name="officialmeet"), send=AsyncMock())
        self.assertFalse(await check(ctx))
        ctx.command = SimpleNamespace(name="ban")
        self.assertTrue(await check(ctx))
        value = interaction()
        value.command = SimpleNamespace(name="force-color-vote")
        self.assertFalse(await bot.tree.interaction_check(value))
        value = interaction()
        value.command = SimpleNamespace(name="ban")
        self.assertTrue(await bot.tree.interaction_check(value))

    async def test_cog_recovery_is_guarded_before_registration_yields(self):
        class RecoveredCog:
            __module__ = "cogs.diff_advanced_features"

            @tasks.loop(seconds=1)
            async def _reminder_check(self):
                self.did_send = True
        cog = RecoveredCog()

        async def add_cog(value):
            await value._reminder_check()
        bot = SimpleNamespace(add_cog=add_cog)
        self.state.install_cog_loading(bot)
        await bot.add_cog(cog)
        self.assertFalse(hasattr(cog, "did_send"))

    async def test_existing_views_can_be_registered_during_pause(self):
        class FeatureCog:
            __module__ = "cogs.diff_attendance"

            async def _rebuild_session_views(self):
                self.registered = True

            async def finalize(self):
                self.finalized = True
        cog = FeatureCog()
        self.state.protect_cog(cog)
        await cog._rebuild_session_views()
        self.assertTrue(cog.registered)
        await cog.finalize()
        self.assertFalse(hasattr(cog, "finalized"))

    async def test_color_dm_timer_rechecks_pause_after_sleep_and_between_members(self):
        source = Path("cogs/diff_color_team_scheduler.py").read_text()
        method = next(n for n in ast.walk(ast.parse(source))
                      if isinstance(n, ast.AsyncFunctionDef) and n.name == "send_dm_reminders")
        namespace = {
            "asyncio": SimpleNamespace(sleep=AsyncMock()), "discord": discord,
            "REMINDER_DELAY_MINUTES": 30, "COLOR_CHANNEL_ID": 1, "COLOR_ROLE_ID": 2,
        }
        exec(compile(ast.Module(body=[method], type_ignores=[]), "<color timer>", "exec"),
             namespace)
        first = SimpleNamespace(id=1, bot=False, display_name="First", send=AsyncMock())
        second = SimpleNamespace(id=2, bot=False, display_name="Second", send=AsyncMock())
        channel = Mock(spec=discord.TextChannel)
        channel.guild = SimpleNamespace(get_role=lambda rid: SimpleNamespace(members=[first, second]))
        channel.name = "colors"
        bot = SimpleNamespace(_activity_pause=self.state, get_channel=Mock(return_value=channel))
        cog = SimpleNamespace(bot=bot, state=SimpleNamespace(available=[], not_available=[]))
        await namespace["send_dm_reminders"](cog)
        bot.get_channel.assert_not_called()
        self.state.set_paused(["colors"], False)
        first.send.side_effect = lambda *args, **kwargs: self.state.set_paused(["colors"], True)
        await namespace["send_dm_reminders"](cog)
        first.send.assert_awaited_once()
        second.send.assert_not_awaited()


class PauseCoverageTests(unittest.TestCase):
    def test_all_primary_entry_points_are_classified(self):
        for name in ("officialmeet", "planmeet", "refreshschedule", "lockslot", "hostnudge",
                     "postrollcall", "meet-rsvp", "attendance-close", "rebuildcolorvote",
                     "force-color-winner", "log-color-submission"):
            self.assertIn(command_domain(SimpleNamespace(name=name)), ("meets", "colors"), name)
        for name in ("bothealth", "ban", "kick", "warn", "backup", "hosthub", "hostnote",
                     "unflaghost", "activitystatus", "pauseactivities", "resumeactivities"):
            self.assertIsNone(command_domain(SimpleNamespace(name=name)), name)
        for name in ("_HrsvpMeetView", "_HostAvailModal", "_RcStaffSelect", "AutoScheduleView",
                     "_OfficialMeetModal", "_PlanMeetModal", "_HostHubLiveMeetSelect"):
            self.assertEqual(symbol_domain(name), "meets", name)
        self.assertEqual(symbol_domain("ColorSubmissionModal"), "colors")
        self.assertIsNone(symbol_domain("_RcNoShowDisputeView"))
        self.assertIsNone(symbol_domain("_BlacklistFlowView"))
        self.assertIsNone(symbol_domain("UnifiedHostHubView"))
        self.assertEqual(symbol_domain("_PollView", "cogs.diff_community_features"), "meets")
        self.assertIsNone(symbol_domain("_GiveawayView", "cogs.diff_community_features"))
        self.assertEqual(symbol_domain("_rc_collect_color_voters"), "colors")

    def test_long_running_jobs_wait_inside_each_iteration_and_resets_wait_at_startup(self):
        tree = ast.parse(Path("bot.py").read_text())
        functions = {n.name: n for n in tree.body if isinstance(n, ast.AsyncFunctionDef)}
        for name in ("_om_recur_loop", "_om_autopost_from_schedule_loop", "_popup_auto_end_loop",
                     "_rc_auto_archive_loop", "_rc_saturday_reminder_loop", "_rc_public_reminder_loop",
                     "_rc_t5h_reminder_loop", "_rc_pruning_report_loop", "_hrsvp_auto_reset_loop",
                     "_host_avail_nudge_loop", "_rc_weekly_reset_loop", "_hrsvp_escalation_loop",
                     "_cc_reminder_loop"):
            loop = next(n for n in ast.walk(functions[name])
                        if isinstance(n, ast.While) and "is_closed" in ast.unparse(n.test))
            self.assertTrue(any("wait_until_running" in ast.unparse(n)
                                for n in loop.body), name)
            if name in ("_hrsvp_auto_reset_loop", "_rc_weekly_reset_loop"):
                preceding = functions[name].body[:functions[name].body.index(loop)]
                self.assertTrue(any("wait_until_running" in ast.unparse(n) for n in preceding), name)
