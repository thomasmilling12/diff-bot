"""Offline checks: no bot startup, Discord token, live sends, or persistent data."""
import ast
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import time
import unittest
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

import discord
from utils import reminder_layouts as ui

FUNCTIONS = {
    "_cc_build_dm_embed", "_cc_mark_sent", "_cc_track_message", "_cc_message_matches",
    "_CcDoneView", "_cc_dm_changers", "_cc_open_task", "_rc_reminder_ts",
    "_host_nudge_targets", "_host_nudge_post_once", "_hrsvp_availability_slot",
    "_cmd_hostnudge", "_rc_t5h_reminder_loop", "_rc_notify_crew_of_schedule",
}
tree = ast.parse(Path("bot.py").read_text())
nodes = [copy.deepcopy(node) for node in tree.body
         if getattr(node, "name", None) in FUNCTIONS]
for node in nodes:
    if node.name == "_cmd_hostnudge":
        node.decorator_list = []
module = ast.Module(body=nodes, type_ignores=[])


class ReminderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.pending = {
            "opened_at": (self.now - timedelta(hours=2)).isoformat(), "done": False,
            "color_name": "Solar Orange", "hex_code": "#FFA400",
            "image_url": "https://example.com/car.png", "last_dm_ts": 0,
        }
        self.state = {"pending": copy.deepcopy(self.pending)}
        self.channel = Mock(spec=discord.TextChannel)
        self.channel.send = AsyncMock(return_value=SimpleNamespace(id=99))
        self.members = [
            SimpleNamespace(id=i, bot=False, display_name=f"Host {i}", send=AsyncMock(return_value=SimpleNamespace(id=i)))
            for i in (1, 2)
        ]
        self.role = SimpleNamespace(members=self.members, mention="<@&100>")
        self.guild = SimpleNamespace(
            id=5, get_role=lambda rid: self.role, get_channel=lambda cid: self.channel,
            get_member=lambda uid: next((m for m in self.members if m.id == uid), None),
        )
        def save(data):
            self.state = copy.deepcopy(data)
        self.ns = {
            "discord": discord, "datetime": datetime, "timezone": timezone, "time": time,
            "timedelta": timedelta, "_EST_TZ": ZoneInfo("America/New_York"),
            "commands": SimpleNamespace(Context=object),
            "Dict": dict, "Any": object, "_reminder_ui": ui,
            "_cc_load": lambda: copy.deepcopy(self.state), "_cc_save": save,
            "_cc_changer_ids": lambda: [1, 2],
            "_CC_TEAM_CHANNEL_ID": 20, "GUILD_ID": 5, "STAFF_LOGS_CHANNEL_ID": 30,
            "_is_staff_member": lambda member: False,
            "HOST_ROLE_ID": 100, "CREW_MEMBER_ROLE_ID": 101, "PS5_ROLE_ID": 102,
            "_HOST_TEAM_CHANNEL_ID": 21, "HOST_RSVP_CHANNEL_ID": 22, "_CREW_CHAT_CHANNEL_ID": 23,
            "ROLL_CALL_URL": "https://discord.com/channels/5/24", "ROLL_CALL_CHANNEL_ID": 24,
            "_HRSVP_DAYS": ("Meet 1", "Meet 2", "Meet 3"),
            "_hrsvp_uid": lambda entry: entry.get("uid", "") if isinstance(entry, dict) else entry,
            "_asched_slot_ts": lambda slot: slot.get("ts"),
            "_this_week_weekday_ts": lambda day, start: int(day),
            "_parse_meet_ts": Mock(return_value=None),
            "asyncio": SimpleNamespace(sleep=AsyncMock()),
            "bot": SimpleNamespace(get_guild=lambda gid: self.guild, get_channel=lambda cid: self.channel,
                                   wait_until_ready=AsyncMock(), is_closed=Mock(side_effect=[False, True])),
        }
        exec(compile(module, "bot.py", "exec"), self.ns)

    def test_cards_are_short_and_within_discord_limits(self):
        embeds = [
            ui.schedule_card([(1, "X" * 500, 2000000000, "Host")], 12),
            ui.meet_reminder(1, "X" * 500, 2000000000, "Host", 20, 3, 5),
            ui.host_reminder(3, ["Meet 2", "Meet 3"]),
            ui.color_card(self.pending, reminder=True),
        ]
        for embed in embeds:
            self.assertLessEqual(len(embed.title), 256)
            self.assertLess(len(embed), 1500)
            self.assertTrue(all(len(f.value) <= 1024 for f in embed.fields))
        self.assertNotIn("~5 hours", embeds[1].title)
        self.assertIn("<t:2000000000:R>", embeds[1].description)
        self.assertTrue(embeds[3].thumbnail.url)
        self.assertFalse(embeds[3].image.url)
        self.assertEqual(ui.open_panel("Open roll call", self.ns["ROLL_CALL_URL"]).children[0].url,
                         self.ns["ROLL_CALL_URL"])

    def test_host_name_is_not_duplicated(self):
        self.assertEqual(ui.host_name(self.guild, 1), "Host 1")
        self.assertEqual(ui.host_name(self.guild, None), "Host to be confirmed")

    def test_weekday_resolution_does_not_reparse_into_next_week(self):
        past = int(time.time()) - 3600
        self.assertEqual(self.ns["_rc_reminder_ts"]({"date_text": str(past), "start_time": "8PM"}), past)
        self.ns["_parse_meet_ts"].assert_not_called()
        self.assertIsNone(self.ns["_rc_reminder_ts"]({}))

    async def test_schedule_omits_past_and_finalized_meets(self):
        now = int(time.time())
        meets = [
            dict(meet_number=n, date_text=str(ts), start_time="8PM",
                 host_id=1, class_name="Sports", is_finalized=finalized)
            for n, ts, finalized in [(1, now-3600, False), (2, now+3600, False), (3, now+7200, True)]
        ]
        self.ns["_rc_db"] = SimpleNamespace(get_all_responses=lambda gid: {2: {"yes": [1]}})
        await self.ns["_rc_notify_crew_of_schedule"](self.guild, meets)
        embed = self.channel.send.call_args.kwargs["embed"]
        self.assertEqual(embed.fields[0].name, "Meet 2 · Sports")
        self.assertEqual(len(embed.fields), 2)
        self.members[0].send.assert_not_awaited()
        self.members[1].send.assert_awaited_once()

    async def test_host_partial_responses_and_assigned_coverage(self):
        self.ns["_hrsvp_load"] = lambda: {
            "Meet 1": {"no": [1, 2]}, "Meet 2": {"yes": [2]}, "Meet 3": {"no": [1, 2]},
        }
        self.ns["_asched_load"] = lambda: {"days": {
            "Meet 1": {"ts": time.time()-100}, "Meet 2": {},
            "Meet 3": {"host_id": 2, "host_status": "yes"},
        }}
        await self.ns["_host_nudge_post_once"](self.guild)
        sent = self.channel.send.call_args.kwargs
        self.assertEqual(sent["content"], "<@1>")
        self.assertNotIn("Needs coverage", sent["embed"].description)
        self.assertIn("1", sent["embed"].description)
        self.assertEqual(sent["view"].children[0].label, "Update availability")

    async def test_host_all_complete_and_covered_stays_quiet(self):
        self.ns["_hrsvp_load"] = lambda: {day: {"yes": [1], "no": [2]} for day in self.ns["_HRSVP_DAYS"]}
        self.ns["_asched_load"] = lambda: {"days": {}}
        self.assertTrue(await self.ns["_host_nudge_post_once"](self.guild))
        self.channel.send.assert_not_awaited()

    async def test_host_all_past_stays_quiet(self):
        now = datetime(2026, 10, 28, 12, tzinfo=ZoneInfo("America/New_York")).timestamp()
        self.ns["time"] = SimpleNamespace(time=lambda: now)
        self.ns["_hrsvp_load"] = lambda: {}
        self.ns["_asched_load"] = lambda: {"days": {day: {"ts": now-60} for day in self.ns["_HRSVP_DAYS"]}}
        await self.ns["_host_nudge_post_once"](self.guild)
        self.channel.send.assert_not_awaited()

    def host_schedule(self):
        return {"days": {day: {"host_id": 2, "host_status": "yes"}
                         for day in self.ns["_HRSVP_DAYS"]}}

    async def test_all_confirmed_stops_repeated_pings_even_without_any_responses(self):
        schedule = self.host_schedule()
        before = copy.deepcopy(schedule)
        self.ns["_hrsvp_load"] = lambda: {}
        self.ns["_asched_load"] = lambda: schedule
        for _ in range(3):
            self.assertTrue(await self.ns["_host_nudge_post_once"](self.guild))
        self.channel.send.assert_not_awaited()
        self.assertEqual(schedule, before)

    async def test_missing_responses_for_confirmed_slots_do_not_count(self):
        schedule = self.host_schedule()
        schedule["days"]["Meet 2"] = {}
        self.ns["_asched_load"] = lambda: schedule
        self.ns["_hrsvp_load"] = lambda: {"Meet 2": {"yes": [{"uid": "2"}], "no": ["1"]}}
        await self.ns["_host_nudge_post_once"](self.guild)
        self.channel.send.assert_not_awaited()

    async def test_only_missing_response_for_unconfirmed_slot_is_pinged(self):
        schedule = self.host_schedule()
        schedule["days"]["Meet 2"] = {}
        self.ns["_asched_load"] = lambda: schedule
        self.ns["_hrsvp_load"] = lambda: {"Meet 2": {"no": [{"uid": "1"}]}}
        await self.ns["_host_nudge_post_once"](self.guild)
        sent = self.channel.send.call_args.kwargs
        self.assertEqual(sent["content"], "<@2>")
        self.assertIn("Meet 2", sent["embed"].description)
        self.assertNotIn("Meet 1", sent["embed"].description)
        self.assertNotIn("Meet 3", sent["embed"].description)
        self.assertIn("slots still needing a confirmed host", sent["embed"].description)

    async def test_tentative_missing_or_former_host_is_not_confirmed_coverage(self):
        for slot in (
            {"host_id": 2, "host_status": "maybe"},
            {"host_id": 2},
            {"host_id": 999, "host_status": "yes"},
        ):
            self.channel.send.reset_mock()
            schedule = self.host_schedule()
            schedule["days"]["Meet 2"] = slot
            self.ns["_asched_load"] = lambda: schedule
            self.ns["_hrsvp_load"] = lambda: {}
            await self.ns["_host_nudge_post_once"](self.guild)
            sent = self.channel.send.call_args.kwargs
            self.assertEqual(sent["content"], "<@1> <@2>")
            self.assertIn("Meet 2", sent["embed"].description)

    async def test_unavailable_and_maybe_responses_count_for_pending_slots(self):
        schedule = self.host_schedule()
        schedule["days"]["Meet 2"] = {"host_id": 2, "host_status": "maybe"}
        self.ns["_asched_load"] = lambda: schedule
        self.ns["_hrsvp_load"] = lambda: {
            "Meet 2": {"no": ["1"], "maybe": [{"uid": "2"}]},
        }
        await self.ns["_host_nudge_post_once"](self.guild)
        sent = self.channel.send.call_args.kwargs
        self.assertEqual(sent["content"], self.role.mention)
        self.assertNotIn("still need to complete", sent["embed"].description)
        self.assertIn("Needs coverage", sent["embed"].description)

    async def test_prior_week_assignment_does_not_suppress_new_week_reminders(self):
        tz = ZoneInfo("America/New_York")
        now = datetime(2026, 10, 26, 12, tzinfo=tz).timestamp()
        previous = datetime(2026, 10, 23, 20, tzinfo=tz).timestamp()
        self.ns["time"] = SimpleNamespace(time=lambda: now)
        schedule = self.host_schedule()
        schedule["days"]["Meet 2"]["ts"] = previous
        self.ns["_asched_load"] = lambda: schedule
        self.ns["_hrsvp_load"] = lambda: {}
        await self.ns["_host_nudge_post_once"](self.guild)
        self.assertIn("Meet 2", self.channel.send.call_args.kwargs["embed"].description)

    async def test_missing_host_role_and_failed_delivery_are_not_successful(self):
        self.ns["_hrsvp_load"] = lambda: {}
        self.ns["_asched_load"] = lambda: {"days": {}}
        self.guild.get_role = lambda rid: None
        self.assertFalse(await self.ns["_host_nudge_post_once"](self.guild))
        self.channel.send.assert_not_awaited()
        self.guild.get_role = lambda rid: self.role
        self.channel.send.side_effect = RuntimeError("offline simulated failure")
        with self.assertRaises(RuntimeError):
            await self.ns["_host_nudge_post_once"](self.guild)

    async def test_manual_nudge_reports_quiet_instead_of_claiming_a_post(self):
        self.ns["_hrsvp_load"] = lambda: {}
        self.ns["_asched_load"] = self.host_schedule
        self.ns["_is_staff_member"] = lambda member: True
        ctx = SimpleNamespace(author=Mock(spec=discord.Member), guild=self.guild,
                              message=SimpleNamespace(delete=AsyncMock()), send=AsyncMock())
        await self.ns["_cmd_hostnudge"](ctx)
        self.channel.send.assert_not_awaited()
        self.assertIn("No availability reminders needed", ctx.send.call_args.args[0])

    async def test_manual_nudge_keeps_staff_permission_check(self):
        ctx = SimpleNamespace(author=Mock(spec=discord.Member),
                              message=SimpleNamespace(delete=AsyncMock()), send=AsyncMock())
        await self.ns["_cmd_hostnudge"](ctx)
        ctx.message.delete.assert_not_awaited()
        self.channel.send.assert_not_awaited()
        self.assertEqual(ctx.send.call_args.args[0], "Staff only.")

    def test_color_success_marker_preserves_done_and_replaced_task(self):
        self.state["pending"]["done"] = True
        self.ns["_cc_mark_sent"](self.pending["opened_at"])
        self.assertTrue(self.state["pending"]["done"])
        self.assertEqual(self.state["pending"]["last_dm_ts"], 0)
        self.state["pending"]["done"] = False
        self.state["pending"]["opened_at"] = "new task"
        self.ns["_cc_mark_sent"](self.pending["opened_at"])
        self.assertEqual(self.state["pending"]["last_dm_ts"], 0)

    def test_old_color_button_does_not_complete_new_task(self):
        message = SimpleNamespace(id=200, created_at=self.now-timedelta(days=7),
                                  embeds=[SimpleNamespace(description="Solar Orange #FFA400")])
        self.assertFalse(self.ns["_cc_message_matches"](message, self.pending))
        message.created_at = self.now
        self.assertTrue(self.ns["_cc_message_matches"](message, self.pending))
        self.ns["_cc_track_message"](self.pending["opened_at"], message)
        self.assertIn("200", self.state["pending"]["message_ids"])

    async def test_color_stops_sending_when_completed_during_delivery(self):
        async def complete(**kwargs):
            self.state["pending"]["done"] = True
            return SimpleNamespace(id=88)
        self.members[0].send.side_effect = complete
        self.assertEqual(await self.ns["_cc_dm_changers"](self.guild, self.pending), 1)
        self.members[1].send.assert_not_awaited()
        self.channel.send.assert_not_awaited()
        self.assertTrue(self.state["pending"]["done"])

    async def test_failed_initial_color_send_leaves_retry_open(self):
        self.ns["_cc_dm_changers"] = AsyncMock(return_value=0)
        await self.ns["_cc_open_task"](self.guild, self.pending)
        self.assertEqual(self.state["pending"]["last_dm_ts"], 0)

    async def test_done_updates_card_and_requires_authorization(self):
        interaction = SimpleNamespace(
            user=SimpleNamespace(id=1, display_name="Host 1"),
            message=SimpleNamespace(id=999, created_at=self.now, edit=AsyncMock(),
                                    embeds=[SimpleNamespace(description="Solar Orange #FFA400")]),
            response=SimpleNamespace(send_message=AsyncMock(), defer=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        view = self.ns["_CcDoneView"]()
        self.assertTrue(view.is_persistent())
        await view.children[0].callback(interaction)
        self.assertTrue(self.state["pending"]["done"])
        self.assertIsNone(interaction.message.edit.call_args.kwargs["view"])
        self.assertEqual(interaction.message.edit.call_args.kwargs["embed"].title, "Crew color • Updated")
        self.state["pending"]["done"] = False
        interaction.user.id = 1234
        await view.children[0].callback(interaction)
        self.assertFalse(self.state["pending"]["done"])

    async def run_t5h(self, *, fail=False):
        now = int(time.time())
        cursor = Mock()
        cursor.fetchall.return_value = [{"user_id": 1, "status": "yes"}, {"user_id": 888, "status": "yes"}]
        self.ns["_rc_db"] = SimpleNamespace(
            get_meets=lambda gid: [
                {"meet_number": 1, "class_name": "Sports", "start_time": "8PM",
                 "date_text": str(now+1800), "is_finalized": False, "host_id": 1}],
            conn=SimpleNamespace(cursor=lambda: cursor),
        )
        self.ns["_rc_reminder_state_load"] = lambda: {}
        self.ns["_rc_reminder_state_save"] = Mock()
        if fail:
            self.channel.send.side_effect = RuntimeError("send failed")
        await self.ns["_rc_t5h_reminder_loop"]()

    async def test_t5h_late_delivery_uses_relative_time_and_current_members(self):
        await self.run_t5h()
        kwargs = self.channel.send.call_args.kwargs
        self.assertNotIn("5 hours", kwargs["embed"].title)
        self.assertIn(":R>", kwargs["embed"].description)
        self.assertEqual(kwargs["content"], "<@1> <@2>")
        self.ns["_rc_reminder_state_save"].assert_called_once()

    async def test_t5h_send_failure_does_not_mark_sent(self):
        await self.run_t5h(fail=True)
        self.ns["_rc_reminder_state_save"].assert_not_called()


if __name__ == "__main__":
    unittest.main()
