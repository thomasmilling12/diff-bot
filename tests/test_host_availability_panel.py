"""Offline host-panel rendering, routing, authorization, and data-preservation checks."""
import ast
import asyncio
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

import discord
from utils import reminder_layouts

NAMES = {
    "_hrsvp_uid", "_hrsvp_reset", "_hrsvp_build_header_embed", "_hrsvp_build_meet_embed",
    "_hrsvp_week_key", "_hrsvp_is_staff", "_hrsvp_response_state", "_hrsvp_response_error",
    "_hrsvp_responded_uids",
    "_HrsvpHeaderView", "_HrsvpMeetView", "_HrsvpResponsesBtn", "_HrsvpResponsesPages",
    "_HrsvpStaffToolsBtn", "_HrsvpStaffActions", "_HrsvpResetConfirmModal",
    "_HrsvpResetBtn", "_HrsvpMyStatusBtn", "HostRSVPView", "_HostAvailModal",
    "_HostMaybeModal", "_HostRSVPBtn", "_hrsvp_days_sorted", "_hrsvp_update_panel",
    "_hrsvp_update_panel_inner",
}
tree = ast.parse(Path("bot.py").read_text())
module = ast.Module(body=[n for n in tree.body if getattr(n, "name", None) in NAMES],
                    type_ignores=[])


class HostAvailabilityTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.days = ["Meet 1", "Meet 2", "Meet 3"]
        self.data = {day: {"yes": [], "maybe": [], "no": []} for day in self.days}
        self.schedule = {"days": {
            "Meet 1": {"ts": 900, "class": "Past"},
            "Meet 2": {"ts": 2000, "class": "Sports", "host_id": 1, "host_status": "yes"},
            "Meet 3": {"class": "TBD"},
        }}
        self.ns = {
            "discord": discord, "asyncio": asyncio, "datetime": datetime,
            "timedelta": timedelta, "_EST_TZ": ZoneInfo("America/New_York"),
            "utc_now": lambda: datetime.now(timezone.utc), "time": SimpleNamespace(time=lambda: 1000),
            "_HRSVP_DAYS": self.days, "_LEADERSHIP_ROLE_IDS": {20}, "HOST_ROLE_ID": 10,
            "_reminder_ui": reminder_layouts, "_hrsvp_panel_lock": asyncio.Lock(),
            "_hrsvp_load": lambda: copy.deepcopy(self.data), "_hrsvp_save": Mock(side_effect=self.save),
            "_asched_load": lambda: copy.deepcopy(self.schedule),
            "_asched_slot_ts": lambda entry: entry.get("ts"),
            "_hrsvp_entry_ts": lambda entry: entry.get("ts"),
            "_this_week_weekday_ts": lambda *args: 2200, "_parse_meet_ts": lambda *args: 2200,
            "_hrel_track_rsvp": Mock(),
        }
        exec(compile(module, "bot.py", "exec"), self.ns)
        self.real_update = self.ns["_hrsvp_update_panel"]
        self.ns["_hrsvp_update_panel"] = AsyncMock()

    def save(self, data):
        self.data = copy.deepcopy(data)

    def interaction(self, roles=(10,), administrator=False):
        return SimpleNamespace(
            user=SimpleNamespace(id=1, roles=[SimpleNamespace(id=r) for r in roles],
                                 guild_permissions=SimpleNamespace(administrator=administrator)),
            client=object(), guild=SimpleNamespace(get_member=lambda uid: SimpleNamespace(display_name=f"Host {uid}")),
            response=SimpleNamespace(defer=AsyncMock(), send_message=AsyncMock(),
                                     send_modal=AsyncMock(), edit_message=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )

    async def test_compact_header_counts_assignment_not_volunteers(self):
        self.data["Meet 1"]["yes"] = [{"uid": "1"}]
        self.data["Meet 3"]["yes"] = [{"uid": "2"}]
        embed = self.ns["_hrsvp_build_header_embed"]()
        self.assertIn("1/3 hosts assigned", embed.description)
        self.assertIn("2 hosts responded", embed.description)
        self.assertLess(len(embed), 500)

    async def test_card_has_only_scheduled_time_and_response_totals(self):
        self.data["Meet 2"]["yes"] = [{"uid": "2", "ts": 3000, "theme": "Proposed theme"}]
        embed = self.ns["_hrsvp_build_meet_embed"]("Meet 2")
        self.assertIn("<t:2000:F>", embed.description)
        self.assertNotIn("3000", embed.description)
        self.assertIn("Assigned host:** <@1>", embed.description)
        self.assertIn("1 available", embed.description)
        self.assertNotIn("0 maybe", embed.description)
        self.schedule["days"]["Meet 2"]["host_status"] = "maybe"
        embed = self.ns["_hrsvp_build_meet_embed"]("Meet 2")
        self.assertIn("Needs assignment", embed.description)
        self.assertIn("Tentative", embed.description)

    async def test_order_preserves_slot_ids_upcoming_then_unscheduled_then_past(self):
        self.assertEqual(self.ns["_hrsvp_days_sorted"](), ["Meet 2", "Meet 3", "Meet 1"])

    async def test_view_layout_and_persistent_legacy_routing(self):
        aggregate = self.ns["HostRSVPView"]()
        self.assertTrue(aggregate.is_persistent())
        self.assertEqual(len(aggregate.to_components()), 5)
        ids = {c.custom_id for c in aggregate.children}
        self.assertIn("hrsvp_reset_all", ids)
        self.assertIn("hrsvp_Meet_1_yes", ids)
        header = self.ns["_HrsvpHeaderView"]()
        self.assertNotIn("hrsvp_reset_all", {c.custom_id for c in header.children})
        self.assertTrue({c.custom_id for c in header.children}.issubset(ids))
        for day in self.days:
            view = self.ns["_HrsvpMeetView"](day)
            self.assertTrue(view.is_persistent())
            self.assertTrue({c.custom_id for c in view.children}.issubset(ids))
            self.assertEqual([c.disabled for c in view.children[:3]], [day == "Meet 1"] * 3)
            self.assertFalse(view.children[3].disabled)
            self.assertEqual(len(view.to_components()), 2)

    async def test_old_buttons_cannot_change_closed_meet(self):
        before = copy.deepcopy(self.data)
        for choice in ("yes", "maybe", "no"):
            interaction = self.interaction()
            button = self.ns["_HostRSVPBtn"]("Meet 1", choice, "?", discord.ButtonStyle.secondary)
            await button.callback(interaction)
            interaction.response.send_message.assert_awaited_once()
            interaction.response.send_modal.assert_not_awaited()
        self.assertEqual(self.data, before)
        self.ns["_hrsvp_save"].assert_not_called()

    async def test_forms_recheck_role_week_and_meet_at_submit(self):
        for modal_name in ("_HostAvailModal", "_HostMaybeModal"):
            for scenario in ("past", "role", "week"):
                modal = self.ns[modal_name]("Meet 2")
                interaction = self.interaction(roles=() if scenario == "role" else (10,))
                if scenario == "past":
                    self.schedule["days"]["Meet 2"]["ts"] = 900
                if scenario == "week":
                    modal.week = "old-week"
                await modal.on_submit(interaction)
                interaction.followup.send.assert_awaited_once()
                self.ns["_hrsvp_save"].assert_not_called()
                self.schedule["days"]["Meet 2"]["ts"] = 2000

    async def test_available_maybe_unavailable_still_save_and_replace(self):
        interaction = self.interaction()
        modal = self.ns["_HostAvailModal"]("Meet 2")
        modal.day_time_input._value = "Thursday 8 PM"
        modal.theme_input._value = "Sports"
        await modal.on_submit(interaction)
        self.assertEqual(self.data["Meet 2"]["yes"][0]["uid"], "1")
        modal = self.ns["_HostMaybeModal"]("Meet 2")
        modal.day_pref._value = "Friday"
        await modal.on_submit(self.interaction())
        self.assertFalse(self.data["Meet 2"]["yes"])
        self.assertEqual(self.data["Meet 2"]["maybe"][0]["day"], "Friday")
        button = self.ns["_HostRSVPBtn"]("Meet 2", "no", "?", discord.ButtonStyle.secondary)
        await button.callback(self.interaction())
        self.assertEqual(self.data["Meet 2"]["no"], ["1"])
        self.assertFalse(self.data["Meet 2"]["maybe"])
        await button.callback(self.interaction())
        self.assertEqual(self.data["Meet 2"]["no"], ["1"])
        self.assertIn("1", self.ns["_hrsvp_responded_uids"]())

    async def test_response_confirmation_precedes_panel_refresh(self):
        for response_type in ("available", "maybe", "unavailable"):
            interaction = self.interaction()

            async def refresh_after_ack(_client):
                self.assertGreater(interaction.followup.send.await_count, 0)

            self.ns["_hrsvp_update_panel"].side_effect = refresh_after_ack
            if response_type == "available":
                modal = self.ns["_HostAvailModal"]("Meet 2")
                modal.day_time_input._value = "Thursday 8 PM"
                modal.theme_input._value = "Sports"
                await modal.on_submit(interaction)
            elif response_type == "maybe":
                modal = self.ns["_HostMaybeModal"]("Meet 2")
                modal.day_pref._value = "Friday"
                await modal.on_submit(interaction)
            else:
                button = self.ns["_HostRSVPBtn"]("Meet 2", "no", "?", discord.ButtonStyle.secondary)
                await button.callback(interaction)
            self.assertEqual(interaction.followup.send.await_count, 1)

    async def test_staff_reopen_close_preserves_data_and_schedule(self):
        self.data["Meet 1"]["yes"] = [{"uid": "3", "ts": 900}]
        before = copy.deepcopy(self.schedule)
        action = self.ns["_HrsvpStaffActions"]()
        action._values = ["reopen:Meet 1"]
        await action.callback(self.interaction(roles=(20,)))
        self.assertEqual(self.ns["_hrsvp_response_state"]("Meet 1"), (True, True, False))
        self.assertFalse(self.ns["_HrsvpMeetView"]("Meet 1").children[0].disabled)
        self.assertEqual(self.data["Meet 1"]["yes"], [{"uid": "3", "ts": 900}])
        self.assertEqual(self.schedule, before)
        self.schedule["days"]["Meet 1"]["ts"] = 800
        self.assertTrue(self.ns["_hrsvp_response_state"]("Meet 1")[2])
        self.schedule = before
        self.data["response_reopen"]["Meet 1"]["week"] = "old"
        self.assertTrue(self.ns["_hrsvp_response_state"]("Meet 1")[2])
        action._values = ["close:Meet 1"]
        await action.callback(self.interaction(roles=(20,)))
        self.assertNotIn("Meet 1", self.data["response_reopen"])

    async def test_staff_tools_and_reset_are_permission_checked(self):
        interaction = self.interaction()
        await self.ns["_HrsvpStaffToolsBtn"]().callback(interaction)
        self.assertNotIn("view", interaction.response.send_message.call_args.kwargs)
        for value in ("reset", "reopen:Meet 1", "refresh"):
            action = self.ns["_HrsvpStaffActions"]()
            action._values = [value]
            await action.callback(self.interaction())
        modal = self.ns["_HrsvpResetConfirmModal"]()
        modal.confirm._value = "RESET"
        await modal.on_submit(self.interaction())
        self.ns["_hrsvp_save"].assert_not_called()

    async def test_reset_requires_confirmation_and_preserves_panel_ids(self):
        self.data["panel_message_ids"] = {"header": 10, "Meet 1": 11, "Meet 2": 12, "Meet 3": 13}
        self.data["Meet 1"]["no"] = ["1"]
        modal = self.ns["_HrsvpResetConfirmModal"]()
        modal.confirm._value = "no"
        await modal.on_submit(self.interaction(roles=(20,)))
        self.ns["_hrsvp_save"].assert_not_called()
        modal.confirm._value = "RESET"
        await modal.on_submit(self.interaction(roles=(20,)))
        self.assertEqual(self.data["Meet 1"]["no"], [])
        self.assertEqual(self.data["panel_message_ids"]["header"], 10)

    async def test_private_details_paginate_without_losing_proposals(self):
        self.data["Meet 2"]["yes"] = [
            {"uid": str(i), "ts": 3000+i, "theme": "x"*100} for i in range(80)]
        interaction = self.interaction()
        await self.ns["_HrsvpResponsesBtn"]("Meet 2").callback(interaction)
        payload = interaction.response.send_message.call_args.kwargs
        view = payload["view"]
        self.assertTrue(payload["ephemeral"])
        self.assertGreater(len(view.pages), 1)
        self.assertEqual(sum(page.count("Proposed:") for page in view.pages), 80)
        self.assertTrue(all(len(page) <= 3500 for page in view.pages))
        self.assertTrue(view.previous.disabled)
        await view.next_page.callback(interaction)
        self.assertEqual(view.index, 1)
        self.assertFalse(view.previous.disabled)

    async def test_existing_panel_updates_in_place_and_remaps_only_message_positions(self):
        self.data["panel_message_ids"] = {"header": 10, "Meet 1": 11, "Meet 2": 12, "Meet 3": 13}
        self.data["Meet 1"]["no"] = ["1"]
        messages = {n: SimpleNamespace(edit=AsyncMock()) for n in range(10, 14)}
        channel = SimpleNamespace(fetch_message=AsyncMock(side_effect=lambda mid: messages[mid]),
                                  send=AsyncMock())
        self.ns["_hrsvp_resolve_channel"] = AsyncMock(return_value=channel)
        self.ns["_hrsvp_render_layout"] = AsyncMock()
        await self.real_update(object())
        channel.send.assert_not_awaited()
        self.ns["_hrsvp_render_layout"].assert_not_awaited()
        self.assertEqual(self.data["panel_message_ids"], {"header": 10, "Meet 2": 11, "Meet 3": 12, "Meet 1": 13})
        self.assertEqual(self.data["Meet 1"]["no"], ["1"])
        self.assertEqual(messages[11].edit.call_args.kwargs["view"].children[0].day, "Meet 2")


if __name__ == "__main__":
    unittest.main()
