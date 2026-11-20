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
- Moderation, blacklist tools, existing no-show appeals, applications,
  interviews, backups, and unrelated bot services remain enabled.
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
