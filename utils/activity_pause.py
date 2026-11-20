"""Reversible, fail-closed pauses for meets and weekly crew-color activities.

Only the small pause-control file is written. Existing feature stores, IDs, and
timers are not migrated or reset. Checks on hot paths use cached state.
"""
import asyncio
import functools
import inspect
import json
import logging
import sys
from pathlib import Path

import discord
from discord.ext import commands, tasks

LABELS = {"meets": "Car meets", "colors": "Crew colors"}
NOTICE = "{} are temporarily paused. Saved data is being kept. Leadership will announce when they resume."

FEATURE_MODULES = {
    "diff_attendance": "meets",
    "diff_meet_host_system": "meets",
    "diff_meet_channel_panel": "meets",
    "diff_meetinfo_patch": "meets",
    "diff_host_team_panel": "meets",
    "diff_host_team_announcement_panel": "meets",
    "diff_host_posters": "meets",
    "diff_postmeet": "meets",
    "diff_rc_admin_patch": "meets",
    "diff_crew_events": "meets",
    "diff_color_team_scheduler": "colors",
    "diff_color_team_announcement_panel": "colors",
}
MEET_PREFIXES = (
    "_hrsvp_", "_asched_", "_rc_", "__rc_", "_om_", "_popup_",
    "_host_avail_", "_host_weekly_", "__host_weekly_", "_host_posters_",
    "_smart_meet_", "_lp_", "_lobby_", "_dm_rsvp_",
)
COLOR_PREFIXES = ("_cs_", "_cc_", "_weekly_color_", "_color_team_")
MEET_CLASSES = {
    "MeetAttendancePanelView", "MeetAttendanceModal", "HostRSVPView",
    "AutoScheduleView", "HostFlowView", "HostFeedbackRequestView",
    "MeetRSVPView", "WeeklyRollCallModal", "RSVPView", "StartMeetModal",
    "AttendanceRsvpView", "AttendanceCreateModal", "_RsvpView",
    "HostSessionView", "_HPAttendanceModal",
}
MEET_CLASS_PREFIXES = (
    "_Hrsvp", "_HostAvail", "_HostMaybe", "_HostRSVP", "_ASched",
    "_Rc", "_RC", "_Om", "_OfficialMeet", "_Popup", "_PlanMeet",
    "_HostPoster", "_Postmeet", "MeetRSVP", "AttendanceRsvp",
    "_HostHubLiveMeet",
)
COLOR_CLASSES = {"GtaColorPreviewView", "ColorSubmissionModal", "ColorSubmissionPanelView",
                 "SubmissionActionView", "ColorTeamPanelView"}
MEET_FUNCTIONS = {
    "_do_host_weekly_reminder", "_host_board_auto_refresh_loop_logic",
    "_unified_hosthub_post_or_refresh", "_host_spotlight_loop",
    "host_board_auto_refresh_loop", "_meet_recap_loop",
    "_hierarchy_attendance_loop_logic", "hierarchy_attendance_loop",
    "_host_onboard_loop", "record_meet_attendance", "post_or_refresh_live_attendance",
    "_re_engagement_logic", "_re_engagement_loop",
}
COLOR_FUNCTIONS = {"_color_schedule_loop_logic", "color_schedule_loop", "color_ops_refresh_loop",
                   "_post_or_refresh_color_team_panel"}
# These mixed-feature cogs also implement moderation, birthdays, and backups.
# Suspend only their meet jobs rather than unloading the cogs.
MIXED_JOBS = {
    ("diff_advanced_features", "_reminder_check"): "meets",
    ("diff_server_improvements", "_meet_reminder_check"): "meets",
    ("diff_server_improvements", "_inactive_member_check"): "meets",
    ("diff_server_improvements", "_crew_leaderboard_weekly"): "meets",
    ("diff_community_features", "_poll_check"): "meets",
}
MIXED_CONTROLS = {
    ("diff_community_features", "_PollView"): "meets",
    ("diff_community_features", "_FeedbackView"): "meets",
    ("diff_extras", "_VoteView"): "meets",
    ("diff_extras", "_RatingView"): "meets",
}
LIFECYCLE_METHODS = {"on_ready", "cog_load", "cog_unload", "cog_check",
                     "interaction_check", "_rebuild_session_views", "_rebuild_event_views",
                     "setup", "teardown"}


def command_domain(command):
    name = getattr(command, "qualified_name", getattr(command, "name", "")).lower()
    if not name:
        return None
    if name in {"hosthub", "hostnote", "unflaghost", "hostnoshow",
                "modhostprofile", "modhostleaderboard", "hostperformance"}:
        return None  # Shared moderation/history tools are not an activity.
    module = getattr(getattr(command, "callback", None), "__module__", "").split(".")[-1]
    if module in FEATURE_MODULES:
        return FEATURE_MODULES[module]
    if "color" in name or "colour" in name:
        return "colors"
    if any(word in name for word in ("meet", "rollcall", "rsvp", "attendance", "popup")):
        return "meets"
    if "host" in name and name not in {"hosthub", "hostnote", "unflaghost"}:
        return "meets"
    if name.split()[0] in {
        "refreshschedule", "rebuildschedule", "overrideslot", "lockslot", "unlockslot",
        "recurmeet", "recurlist", "recurremove", "recurtoggle", "recuredit", "recurpost",
        "autoattend", "weeklyrollcall", "ghostmembers",
        "panel", "diff-reset-member",
    }:
        return "meets"
    return None


def symbol_domain(name, module=""):
    if name == "_RcNoShowDisputeView":
        return None  # Existing no-show appeals must remain accessible.
    if name == "_rc_collect_color_voters":
        return "colors"  # None means no active color obligation to pruning/reminders.
    owner = module.split(".")[-1]
    if (owner, name) in MIXED_CONTROLS:
        return MIXED_CONTROLS[(owner, name)]
    if owner in FEATURE_MODULES:
        return FEATURE_MODULES[owner]
    if name in COLOR_CLASSES or name in COLOR_FUNCTIONS or name.startswith(COLOR_PREFIXES):
        return "colors"
    if (name in MEET_CLASSES or name in MEET_FUNCTIONS
            or name.startswith(MEET_PREFIXES + MEET_CLASS_PREFIXES)):
        return "meets"
    return None


class ActivityPause:
    def __init__(self, path, writer):
        self.path = Path(path)
        self.writer = writer
        self.paused = {"meets": True, "colors": True}
        self.load_error = None
        self._running = {name: asyncio.Event() for name in LABELS}
        try:
            value = json.loads(self.path.read_text())
            if (not isinstance(value, dict) or value.get("version") != 1
                    or set(value.get("paused", {})) != set(LABELS)
                    or any(type(v) is not bool for v in value["paused"].values())):
                raise ValueError("Invalid activity pause control file")
            self.paused = dict(value["paused"])
        except FileNotFoundError:
            pass  # This approved update starts with both activities paused.
        except Exception as exc:
            self.load_error = type(exc).__name__
            logging.getLogger(__name__).error(
                "Activity pause controls could not be loaded (%s); both activities remain paused.",
                self.load_error)
        for name in LABELS:
            if not self.paused[name]:
                self._running[name].set()

    async def wait_until_running(self, domain):
        await self._running[domain].wait()

    def set_paused(self, domains, value):
        if type(value) is not bool or not domains or any(d not in LABELS for d in domains):
            raise ValueError("Invalid pause setting")
        updated = dict(self.paused)
        updated.update({d: value for d in domains})
        # Persist first. A write failure cannot silently change runtime state.
        self.writer(str(self.path), {"version": 1, "paused": updated})
        self.paused = updated
        self.load_error = None
        for name in domains:
            if value:
                self._running[name].clear()
            else:
                self._running[name].set()

    async def interaction_allowed(self, interaction, domain):
        if not self.paused[domain]:
            return True
        content = NOTICE.format(LABELS[domain])
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True,
                                             allowed_mentions=discord.AllowedMentions.none())
        else:
            await interaction.response.send_message(content, ephemeral=True,
                                                     allowed_mentions=discord.AllowedMentions.none())
        return False

    def wrap_action(self, fn, domain):
        if getattr(fn, "_activity_pause_wrapped", False):
            return fn

        @functools.wraps(fn)
        async def guarded(*args, **kwargs):
            if self.paused[domain]:
                return None
            return await fn(*args, **kwargs)
        guarded._activity_pause_wrapped = True
        return guarded

    def protect_view(self, cls, domain):
        if cls.__dict__.get("_activity_pause_wrapped", False):
            return
        original = cls.interaction_check
        state = self

        @functools.wraps(original)
        async def interaction_check(view, interaction):
            if not await state.interaction_allowed(interaction, domain):
                return False
            return await original(view, interaction)
        cls.interaction_check = interaction_check
        if hasattr(cls, "on_timeout"):
            cls.on_timeout = self.wrap_action(cls.on_timeout, domain)
        cls._activity_pause_wrapped = True

    def protect_namespace(self, namespace, module_name, *, main=False):
        """Use public view checks; leave moderation and general job loops alone."""
        for name, obj in list(namespace.items()):
            domain = symbol_domain(name, "" if main else module_name)
            if not domain:
                continue
            if inspect.isclass(obj) and obj.__module__ == module_name:
                if issubclass(obj, (discord.ui.View, discord.ui.Modal, discord.ui.Item)):
                    self.protect_view(obj, domain)
            elif isinstance(obj, tasks.Loop):
                if obj.coro.__module__ == module_name:
                    obj.coro = self.wrap_action(obj.coro, domain)
            elif (inspect.iscoroutinefunction(obj) and obj.__module__ == module_name
                  and name not in LIFECYCLE_METHODS and not name.endswith("_loop")):
                namespace[name] = self.wrap_action(obj, domain)

    def protect_cogs(self, bot):
        """Called after loading cogs, before the Discord gateway becomes ready."""
        for module_name, module in list(bot.extensions.items()):
            self.protect_namespace(vars(module), module_name)
        for cog in bot.cogs.values():
            self.protect_cog(cog)

    def protect_cog(self, cog):
        owner = type(cog).__module__.split(".")[-1]
        domain = FEATURE_MODULES.get(owner)
        for name in dir(type(cog)):
            obj = getattr(cog, name, None)
            job_domain = domain or MIXED_JOBS.get((owner, name))
            if isinstance(obj, tasks.Loop) and job_domain:
                obj.coro = self.wrap_action(obj.coro, job_domain)
            elif (domain and inspect.iscoroutinefunction(obj)
                  and name not in LIFECYCLE_METHODS and not name.endswith("_loop")
                  and not name.startswith("before_")):
                setattr(cog, name, self.wrap_action(obj, domain))

    def install_cog_loading(self, bot):
        # Protect constructors' scheduled tasks before add_cog first yields. This
        # also covers a staff-requested recovery/reload while the bot is online.
        previous_add_cog = bot.add_cog
        state = self

        async def add_cog(cog, *args, **kwargs):
            module_name = type(cog).__module__
            module = sys.modules.get(module_name)
            if module is not None:
                state.protect_namespace(vars(module), module_name)
            state.protect_cog(cog)
            return await previous_add_cog(cog, *args, **kwargs)
        bot.add_cog = add_cog

    def install_commands(self, bot, staff_roles):
        state = self

        async def prefix_check(ctx):
            domain = command_domain(ctx.command)
            if domain and state.paused[domain]:
                await ctx.send(NOTICE.format(LABELS[domain]),
                               allowed_mentions=discord.AllowedMentions.none())
                return False
            return True
        bot.add_check(prefix_check)
        previous_tree_check = bot.tree.interaction_check

        async def tree_check(interaction):
            domain = command_domain(interaction.command)
            if domain and not await state.interaction_allowed(interaction, domain):
                return False
            return await previous_tree_check(interaction)
        bot.tree.interaction_check = tree_check

        @bot.command(name="activitystatus")
        @commands.guild_only()
        async def status(ctx):
            """Show whether car meets and crew colors are paused."""
            lines = [f"**{LABELS[d]}:** {'PAUSED' if state.paused[d] else 'RUNNING'}" for d in LABELS]
            if state.load_error:
                lines.append("Pause controls need staff review; both activities are held safely.")
            lines.append("Saved schedules, responses, and votes are kept. "
                         "Leadership: `!pauseactivities both` / `!resumeactivities both confirm` "
                         "(or `meets` / `colors`). Resuming restores normal scheduled jobs and resets.")
            await ctx.send("\n".join(lines), allowed_mentions=discord.AllowedMentions.none())

        def is_leadership(ctx):
            member = ctx.author
            return (getattr(member.guild_permissions, "administrator", False)
                    or any(r.id in staff_roles for r in member.roles))

        async def change(ctx, target, paused):
            if not is_leadership(ctx):
                return await ctx.send("Leadership only.")
            target = target.lower()
            domains = list(LABELS) if target == "both" else [target]
            if any(d not in LABELS for d in domains):
                return await ctx.send("Choose `both`, `meets`, or `colors`.")
            try:
                state.set_paused(domains, paused)
            except Exception:
                logging.getLogger(__name__).exception("Could not save activity pause setting")
                return await ctx.send("Could not save the pause setting. The previous setting is unchanged.")
            message = "Paused" if paused else "Resumed"
            await ctx.send(f"{message}: {', '.join(LABELS[d] for d in domains)}. "
                           "Existing records are unchanged.",
                           allowed_mentions=discord.AllowedMentions.none())

        @bot.command(name="pauseactivities")
        @commands.guild_only()
        async def pause(ctx, target: str = "both"):
            """Leadership: pause meets, colors, or both without erasing records."""
            await change(ctx, target, True)

        @bot.command(name="resumeactivities")
        @commands.guild_only()
        async def resume(ctx, target: str = "both", confirmation: str = ""):
            """Leadership: resume normal jobs and resets for meets, colors, or both."""
            if not is_leadership(ctx):
                return await ctx.send("Leadership only.")
            if confirmation.lower() != "confirm":
                return await ctx.send(
                    "Review retained schedules and any outstanding color vote first. "
                    "Resuming restores normal weekly resets and catch-up jobs; overdue actions may run. "
                    "To confirm, use `!resumeactivities both confirm` "
                    "(or replace `both` with `meets` / `colors`).")
            await change(ctx, target, False)
