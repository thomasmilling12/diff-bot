"""Exercise the real builder and callback offline, using only in-memory stores."""
import ast
import asyncio
import copy
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

import discord


TREE = ast.parse(Path("bot.py").read_text())
DAYS = ["Meet 1", "Meet 2", "Meet 3"]
STAMP = 1900000000


class RebuildRecoveryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.schedule = {
            "days": {day: {} for day in DAYS},
            "console_message_ids": {"header": 11, "Meet 1": 12, "Meet 2": 13, "Meet 3": 14},
        }
        self.responses = {
            "Meet 1": {"yes": [{"uid": "101", "day": "Thursday", "time": "8 PM",
                                "theme": "Sports", "ts": STAMP}], "no": ["202"]},
        }
        self.member = SimpleNamespace(display_name="Test host", send=AsyncMock())
        self.ns = {
            "discord": discord, "asyncio": asyncio,
            "_HRSVP_DAYS": DAYS, "_ASCHED_REBUILD_ID": "diff_auto_sched_rebuild",
            "_LEADERSHIP_HOST_ROLE_IDS": {7}, "UPCOMING_MEET_CHANNEL_ID": 15,
            "_ASCHED_REBUILD_TIMEOUT": 1, "_ASCHED_REBUILD_REPLY_TIMEOUT": 0.05,
            "_asched_rebuild_running": set(),
            "_hrsvp_load": lambda: copy.deepcopy(self.responses),
            "_asched_load": lambda: copy.deepcopy(self.schedule),
            "_asched_save": Mock(side_effect=self.save),
            "_this_week_weekday_ts": lambda *args: None,
            "_parse_meet_ts": lambda *args: None,
            "_asched_slot_ts": lambda entry: entry.get("pinned_ts"),
            "_asched_prior_week_slots": lambda schedule: [],
            "_asched_prior_week_notice": lambda days: "Previous-week slots",
            "_asched_update_panel": AsyncMock(),
            "_asched_post_finalized": AsyncMock(),
            "_rc_sync_from_schedule": AsyncMock(),
            "_hrel_track_confirmed": Mock(),
            "utc_now": lambda: datetime.now(timezone.utc),
        }
        names = {
            "_hrsvp_uid", "_hrsvp_entry_ts", "_asched_pick_host", "_asched_build",
            "_asched_rebuild_reply", "_asched_run_rebuild", "AutoScheduleView",
        }
        nodes = [copy.deepcopy(n) for n in TREE.body if getattr(n, "name", None) in names]
        self.assertEqual({n.name for n in nodes}, names)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "bot.py", "exec"), self.ns)
        self.interaction = self.interaction_for_staff()
        self.before_responses = copy.deepcopy(self.responses)

    def interaction_for_staff(self):
        return SimpleNamespace(
            user=SimpleNamespace(roles=[SimpleNamespace(id=7)]),
            guild=SimpleNamespace(id=99, get_member=lambda uid: self.member if uid == 101 else None),
            client=object(),
            response=SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
            edit_original_response=AsyncMock(),
        )

    def save(self, schedule):
        self.schedule = copy.deepcopy(schedule)

    async def rebuild(self, interaction=None):
        await self.ns["AutoScheduleView"].rebuild_btn(None, interaction or self.interaction, None)

    def last_message(self):
        return self.interaction.edit_original_response.call_args.kwargs["content"]

    def assert_unchanged_responses(self):
        self.assertEqual(self.responses, self.before_responses)
        self.assertEqual(self.ns["_asched_rebuild_running"], set())

    def fill_all(self):
        for day in DAYS:
            self.responses[day] = copy.deepcopy(self.responses["Meet 1"])
        self.before_responses = copy.deepcopy(self.responses)

    async def test_real_saved_proposal_becomes_assignment_and_reply_finishes(self):
        async def panel(client):
            self.interaction.response.defer.assert_awaited_once_with(ephemeral=True)
            self.assertEqual(self.schedule["days"]["Meet 1"]["host_id"], 101)
            self.assertIn("Schedule saved", self.last_message())
        self.ns["_asched_update_panel"].side_effect = panel
        ids = copy.deepcopy(self.schedule["console_message_ids"])
        await self.rebuild()
        entry = self.schedule["days"]["Meet 1"]
        self.assertEqual((entry["day"], entry["time"], entry["class"]), ("Thursday", "8 PM", "Sports"))
        self.assertEqual(entry["pinned_ts"], STAMP)
        self.assertEqual(entry["host_status"], "yes")
        self.assertEqual(self.schedule["console_message_ids"], ids)
        self.ns["_rc_sync_from_schedule"].assert_awaited_once()
        self.member.send.assert_awaited_once()
        self.ns["_hrel_track_confirmed"].assert_called_once_with("101")
        self.assertIn("Schedule rebuilt", self.last_message())
        self.assert_unchanged_responses()

    async def test_locked_assignment_is_not_replaced(self):
        locked = {"locked": True, "host_id": 999, "host_status": "yes",
                  "class": "Existing", "day": "Friday", "time": "9 PM", "attendees": [44]}
        self.schedule["days"]["Meet 1"] = copy.deepcopy(locked)
        await self.rebuild()
        self.assertEqual(self.schedule["days"]["Meet 1"], locked)
        self.assert_unchanged_responses()

    async def test_nonstaff_cannot_start_work(self):
        self.interaction.user.roles = []
        await self.rebuild()
        self.interaction.response.defer.assert_not_awaited()
        self.ns["_asched_save"].assert_not_called()
        self.ns["_asched_update_panel"].assert_not_awaited()
        self.assertEqual(self.interaction.response.send_message.call_args.args[0],
                         "Only staff can rebuild the schedule.")

    async def test_save_failure_does_not_claim_success_or_send_notifications(self):
        self.ns["_asched_save"].side_effect = OSError("private details must not be echoed")
        with patch("builtins.print") as logged:
            await self.rebuild()
        message = self.last_message()
        self.assertIn("saving the schedule", message)
        self.assertIn("could not be confirmed", message)
        self.assertIn("OSError", message)
        self.assertNotIn("private details", message + str(logged.call_args_list))
        self.ns["_asched_update_panel"].assert_not_awaited()
        self.ns["_rc_sync_from_schedule"].assert_not_awaited()
        self.member.send.assert_not_awaited()
        self.assert_unchanged_responses()

    async def test_stalled_network_steps_finish_with_stage_and_preserve_saved_assignment(self):
        for dependency, stage, filled in (
            ("_asched_update_panel", "refreshing the schedule panel", False),
            ("_asched_post_finalized", "posting the finalized schedule", True),
            ("_rc_sync_from_schedule", "syncing roll call", False),
        ):
            with self.subTest(stage=stage):
                self.setUp()
                if filled:
                    self.fill_all()
                self.ns["_ASCHED_REBUILD_TIMEOUT"] = 0.03
                cancelled = asyncio.Event()
                async def stall(*args):
                    try:
                        await asyncio.Event().wait()
                    finally:
                        cancelled.set()
                self.ns[dependency].side_effect = stall
                await self.rebuild()
                self.assertTrue(cancelled.is_set())
                self.assertIn("timed out", self.last_message())
                self.assertIn(stage, self.last_message())
                self.assertIn("schedule was saved", self.last_message())
                self.assertEqual(self.schedule["days"]["Meet 1"]["host_id"], 101)
                self.member.send.assert_not_awaited()
                self.assert_unchanged_responses()

    async def test_stalled_dm_does_not_leave_rebuild_running_or_erase_assignment(self):
        self.ns["_ASCHED_REBUILD_TIMEOUT"] = 0.03
        async def stall(**kwargs):
            await asyncio.Event().wait()
        self.member.send.side_effect = stall
        await self.rebuild()
        self.assertIn("timed out", self.last_message())
        self.assertIn("assignment DM for Meet 1", self.last_message())
        self.assertEqual(self.schedule["days"]["Meet 1"]["host_id"], 101)
        self.ns["_hrel_track_confirmed"].assert_not_called()
        self.assert_unchanged_responses()

    async def test_discord_failure_reports_step_instead_of_false_success(self):
        self.ns["_rc_sync_from_schedule"].side_effect = RuntimeError("private details")
        with patch("builtins.print") as logged:
            await self.rebuild()
        self.assertIn("failed (RuntimeError)", self.last_message())
        self.assertIn("syncing roll call", self.last_message())
        self.assertNotIn("private details", self.last_message() + str(logged.call_args_list))
        self.member.send.assert_not_awaited()
        self.assert_unchanged_responses()

    async def test_reported_panel_failure_stops_later_notifications(self):
        self.ns["_asched_update_panel"].return_value = False
        await self.rebuild()
        self.assertIn("failed", self.last_message())
        self.assertIn("refreshing the schedule panel", self.last_message())
        self.assertEqual(self.schedule["days"]["Meet 1"]["host_id"], 101)
        self.ns["_rc_sync_from_schedule"].assert_not_awaited()
        self.member.send.assert_not_awaited()
        self.assert_unchanged_responses()

    async def test_final_cache_save_preserves_new_panel_ids(self):
        new_ids = {"header": 21, "Meet 1": 24, "Meet 2": 22, "Meet 3": 23}
        async def panel(client):
            self.schedule["console_message_ids"] = copy.deepcopy(new_ids)
            return True
        self.ns["_asched_update_panel"].side_effect = panel
        await self.rebuild()
        self.assertEqual(self.schedule["console_message_ids"], new_ids)
        self.assertEqual(self.schedule["days"]["Meet 1"]["host_name"], "Test host")
        self.assert_unchanged_responses()

    async def test_final_cache_save_does_not_overwrite_a_newer_staff_override(self):
        override = {"locked": True, "host_id": 303, "host_status": "yes",
                    "host_name": "Replacement", "class": "Manual",
                    "day": "Friday", "time": "10 PM", "attendees": [42]}
        async def during_sync(*args):
            self.schedule["days"]["Meet 1"] = copy.deepcopy(override)
        self.ns["_rc_sync_from_schedule"].side_effect = during_sync
        await self.rebuild()
        self.assertEqual(self.schedule["days"]["Meet 1"], override)
        self.assert_unchanged_responses()

    async def test_overlapping_click_does_not_rebuild_or_duplicate_side_effects(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def panel(client):
            entered.set()
            await release.wait()
        self.ns["_asched_update_panel"].side_effect = panel
        first = asyncio.create_task(self.rebuild())
        try:
            await asyncio.wait_for(entered.wait(), timeout=1)
            second = self.interaction_for_staff()
            await self.rebuild(second)
            self.assertIn("already running", second.edit_original_response.call_args.kwargs["content"])
            self.assertEqual(self.ns["_asched_save"].call_count, 1)
            self.member.send.assert_not_awaited()
        finally:
            release.set()
            await first
        self.member.send.assert_awaited_once()
        self.ns["_rc_sync_from_schedule"].assert_awaited_once()
        self.assert_unchanged_responses()

    async def test_external_cancellation_releases_guard_without_restarting(self):
        entered = asyncio.Event()
        async def panel(client):
            entered.set()
            await asyncio.Event().wait()
        self.ns["_asched_update_panel"].side_effect = panel
        task = asyncio.create_task(self.rebuild())
        await asyncio.wait_for(entered.wait(), timeout=1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(self.schedule["days"]["Meet 1"]["host_id"], 101)
        self.assert_unchanged_responses()

    async def test_failed_status_edit_uses_followup_without_rebuilding(self):
        self.interaction.edit_original_response.side_effect = RuntimeError("edit failed")
        await self.rebuild()
        replies = [call.args[0] for call in self.interaction.followup.send.call_args_list]
        self.assertIn("Schedule saved", replies[0])
        self.assertIn("Schedule rebuilt", replies[-1])
        self.member.send.assert_awaited_once()
        self.assert_unchanged_responses()

    async def test_status_delivery_also_has_a_deadline(self):
        self.ns["_ASCHED_REBUILD_REPLY_TIMEOUT"] = 0.01
        self.interaction.followup.send.side_effect = RuntimeError("delivery failed")
        async def stall(**kwargs):
            await asyncio.Event().wait()
        self.interaction.edit_original_response.side_effect = stall
        await asyncio.wait_for(self.rebuild(), timeout=1)
        self.assertEqual(self.interaction.followup.send.await_count, 2)
        self.member.send.assert_awaited_once()
        self.assert_unchanged_responses()

    async def test_failure_releases_guard_for_a_deliberate_staff_retry(self):
        self.ns["_asched_update_panel"].side_effect = RuntimeError("offline")
        await self.rebuild()
        self.assertIn("failed", self.last_message())
        self.ns["_asched_update_panel"].side_effect = None
        await self.rebuild()
        self.assertIn("Schedule rebuilt", self.last_message())
        self.assert_unchanged_responses()


class BuilderPanelOutcomeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.schedule = {
            "days": {day: {"host_id": 101} for day in DAYS},
            "console_message_ids": {"header": 10, "Meet 1": 11, "Meet 2": 12, "Meet 3": 13},
        }
        self.messages = {mid: SimpleNamespace(edit=AsyncMock(), delete=AsyncMock())
                         for mid in (10, 11, 12, 13)}
        async def no_history(**kwargs):
            if False:
                yield
        self.channel = SimpleNamespace(
            fetch_message=AsyncMock(side_effect=lambda mid: self.messages[mid]),
            send=AsyncMock(side_effect=[SimpleNamespace(id=mid) for mid in (20, 21, 22, 23)]),
            history=no_history,
        )
        self.client = SimpleNamespace(user=SimpleNamespace(id=5))
        self.ns = {
            "discord": discord, "_HRSVP_DAYS": DAYS,
            "_asched_load": lambda: copy.deepcopy(self.schedule),
            "_asched_save": Mock(side_effect=self.save),
            "_asched_get_console_ids": lambda schedule: schedule["console_message_ids"],
            "_asched_resolve_console_channel": AsyncMock(return_value=self.channel),
            "_asched_build_console_header_embed": lambda: "header",
            "_asched_build_console_meet_embed": lambda idx, day: day,
            "_asched_console_order": lambda: list(DAYS),
            "_asched_is_sched_msg": lambda *args: False,
            "AutoScheduleView": lambda client: "view",
        }
        nodes = [copy.deepcopy(n) for n in TREE.body if getattr(n, "name", None) in {
            "_asched_update_panel", "_asched_render_console",
        }]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "bot.py", "exec"), self.ns)

    def save(self, schedule):
        self.schedule = copy.deepcopy(schedule)

    async def test_successful_edit_reports_true_without_reposting_or_changing_ids(self):
        before = copy.deepcopy(self.schedule)
        self.assertTrue(await self.ns["_asched_update_panel"](self.client))
        self.assertEqual(self.schedule, before)
        self.channel.send.assert_not_awaited()
        for message in self.messages.values():
            message.edit.assert_awaited_once()
            message.delete.assert_not_awaited()

    async def test_missing_channel_reports_false(self):
        self.ns["_asched_resolve_console_channel"].return_value = None
        self.assertFalse(await self.ns["_asched_update_panel"](self.client))
        self.assertFalse(await self.ns["_asched_render_console"](self.client))
        self.channel.send.assert_not_awaited()

    async def test_embed_failure_reports_false(self):
        self.ns["_asched_build_console_header_embed"] = Mock(side_effect=ValueError("bad embed"))
        self.assertFalse(await self.ns["_asched_update_panel"](self.client))
        self.channel.fetch_message.assert_not_awaited()

    async def test_header_edit_failure_is_not_silently_successful(self):
        self.messages[10].edit.side_effect = RuntimeError("permission denied")
        self.assertFalse(await self.ns["_asched_update_panel"](self.client))
        self.channel.send.assert_not_awaited()

    async def test_meet_edit_failure_does_not_persist_partial_id_remap(self):
        before = copy.deepcopy(self.schedule)
        self.messages[12].edit.side_effect = RuntimeError("permission denied")
        self.assertFalse(await self.ns["_asched_update_panel"](self.client))
        self.ns["_asched_save"].assert_not_called()
        self.assertEqual(self.schedule, before)

    async def test_missing_message_repair_failure_propagates_false(self):
        self.schedule["console_message_ids"] = {"header": 10}
        before = copy.deepcopy(self.schedule)
        self.channel.send.side_effect = RuntimeError("permission denied")
        self.assertFalse(await self.ns["_asched_update_panel"](self.client))
        self.ns["_asched_save"].assert_not_called()
        self.assertEqual(self.schedule, before)

    async def test_existing_missing_message_repair_reports_success(self):
        self.schedule["console_message_ids"] = {"header": 10}
        self.assertTrue(await self.ns["_asched_update_panel"](self.client))
        self.assertEqual(self.schedule["console_message_ids"],
                         {"header": 20, "Meet 1": 21, "Meet 2": 22, "Meet 3": 23})
        self.assertEqual(self.channel.send.await_count, 4)


if __name__ == "__main__":
    unittest.main()
