# Pausing car meets and crew colors

This update starts **both activities paused** when the updated bot is installed
and started on the Pi. It does not connect to, update, or restart the Pi from
Replit.

## Controls

- `!activitystatus` — show both activity states.
- `!pauseactivities both` — pause both until further notice.
- `!resumeactivities meets confirm` — resume meets only.
- `!resumeactivities colors confirm` — resume crew colors only.
- `!resumeactivities both confirm` — resume both.

Pause/resume controls require Administrator or the bot's existing leadership
roles. Controls are server-only. Normal feature permission checks still apply
after resuming.

The pause state is saved separately in `diff_data/activity_pause.json` when a
setting is changed. The existing Pi deployment backup includes that directory.
A missing file defaults to both paused; a damaged file also holds both paused
and reports the problem instead of silently resuming.

## During the pause

- Meet scheduling, rebuilds, availability submissions, RSVP/check-in/finalize
  controls, recurring and pop-up meets, related announcements, host reminders,
  no-show/pruning reports, and weekly response resets are suspended.
- Weekly crew-color submissions, approvals, vote creation, winner selection,
  reminders, coordination announcements, automatic submission locking, and
  related scheduled posts are suspended.
- Existing panels and their IDs are preserved. Protected buttons, menus, and
  forms respond privately that the activity is paused.
- Existing schedules, assignments, responses, attendance, color submissions,
  and vote records are not cleared or migrated.
- Discord-managed emoji reactions on an already posted color vote remain
  visible and can still change on Discord. The bot does not tally them, close
  the vote, or choose a winner while paused. Review that outstanding vote before
  resuming; this change does not delete reactions or change channel permissions.
- Moderation, blacklist tools, existing no-show appeals, existing application
  reviews, crew applications/interviews, backups, and unrelated bot services remain enabled.
- A Discord request or operation already in progress when staff pause may
  finish. New work is held; pausing is not a rollback of completed actions.

`!bothealth` identifies intentionally paused activity loops separately from
failed loops. Background loops remain available for resumption without a
process restart.

## Resuming safely

Review the retained schedule and any outstanding crew-color vote first.
Omitting `confirm` shows a warning and leaves the activities paused.
Resuming restores the existing scheduler and its normal catch-up/weekly-reset
rules; this pause does not shift dates or extend deadlines. It does not replay
every reminder that would have occurred during the pause.

Do not use Reset Responses or delete panels to activate the pause.

## Offline checks

Run `python -m unittest discover -s tests -p 'test_activity_pause.py'`.
The tests do not start the bot or connect to Discord.

## Join hub and verification during the meet pause

New car-meet applications and car-meet notification toggles are also paused.
Old join-panel controls and an application form opened before the pause check
the current pause state before creating a ticket or assigning a role.
Media/announcement notification choices and existing meet-notification roles
are unchanged.

Rules verification remains available. Welcome messages, check-in help/progress,
and the unverified panel explain that server verification does not require a
car-meet application. The existing join hub and pinned unverified panel are
updated in place on paused startup; missing messages are not automatically
recreated or pinged. Other older welcome messages are not rewritten in bulk.
The existing staff refresh commands remain available.

Automatic unverified channel pings, unverified/check-in reminder DMs, and join
ticket escalation/auto-close work are held. Their reminder markers and application
records are not marked completed by the pause. Existing tickets and staff
review controls remain available, and staff can still send a manual verification
reminder with their existing permissions.

These checks follow the existing `meets` pause setting, not a separate timer.
Explicitly resuming meets restores the normal join/reminder behavior, including
existing overdue-job policies. After changing that setting, use
`/refresh-join-panel` and `!refresh_unverified_panel` to refresh the visible
panel text immediately. Pause guards always consult current state, even when
an older message is still displayed.
