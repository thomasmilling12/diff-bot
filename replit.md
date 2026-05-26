# Different Meets V2 — Discord Bot

**Community:** DIFF Meets (PlayStation GTA car meet community)
**Runtime:** Python 3.11 / discord.py 2.7.1
**Deployed on:** Raspberry Pi 5 at `~/diff-bot/`  
**Venv:** `/home/thomas/diff-bot/.venv/bin/python`  
**Service:** `different-meets-v2` (systemd)  
**Deploy (preferred):**
```bash
cd ~/diff-bot && bash deploy.sh
```
…which runs the equivalent of `git fetch origin && git reset --hard origin/main && sudo systemctl restart different-meets-v2`.

Data files are permanently untracked — `git reset --hard` is safe and never touches live data.

**Agent push workflow:** local working copy lives at `/tmp/bot.py` (re-fetch via `curl` + `GITHUB_TOKEN` from raw GitHub if sandbox resets). Pushes are made via GitHub Git Data API (blob → tree → commit → PATCH ref) using `python3 + urllib`. Always `py_compile` before push. Repo: `thomasmilling12/diff-bot`. Secrets in env: `DISCORD_TOKEN`, `GITHUB_TOKEN`.

## Critical Rules
- Timezone: always `ZoneInfo("America/New_York")` — never `"US/Eastern"`
- Global slash commands are at cap (100). All new commands must be **prefix (`!`) or guild-scoped**
- Never mass-DM guild members from a task loop (Discord Developer Policy)
- `sqlite3.Row`: use `row["key"]`, never `.get()`
- `sys.modules`: never `import bot` in cog callbacks — use `sys.modules.get("__main__")`
- PS5 only — never mention PS4 in user-facing embeds

## Key IDs
| Name | ID |
|---|---|
| GUILD_ID | 850386896509337710 |
| VERIFIED_ROLE_ID | 1141424243616256032 |
| UNVERIFIED_ROLE_ID | 1486011550916411512 |
| MEET_ATTENDER_ROLE_ID | 850392317751066705 |
| HOST_RSVP | 1485830232270307410 |
| STAFF_LOGS | 1485265848099799163 |
| JOIN_TICKET_CATEGORY | 1328457973583839282 |

## Architecture

### Main file
`bot.py` — ~41,300 lines. All core logic, all prefix commands, all event handlers.

### Cogs (loaded via `_cogs` list in `_setup_hook`)
Many cogs under `cogs/`. Notable ones: `diff_color_lab`, `diff_automod`, `diff_meet_host_system`, `diff_mod_hub`, `diff_full_moderation`, `diff_next_level_moderation`, `diff_postmeet`, `cleanup`, etc.

**Known disabled command stubs (own name in bot.py, leave the stub commented in the cog so the cog still loads):**
- `cogs/diff_full_moderation.py` → `hostprofile` (bot.py owns the richer version)
- `cogs/diff_next_level_moderation.py` → `weeklyreport` (bot.py owns the richer version)
- `cogs/diff_host_posters.py` was DELETED in May 26 2026 (its only command, `postmeet`, was a duplicate of bot.py's 90-line version). Loader entry also removed from `_cogs`.

### Data files
- `diff_data/diff_activity.db` — SQLite (member_activity, member_leaves, leave_surveys, health_score_history)
- `diff_data/diff_partner_panel.json` — partnership panels
- `diff_data/diff_partnerships.json` — partnership records
- `diff_data/diff_csat.json` — ticket CSAT ratings (post-close DM survey)
- `diff_data/diff_ticket_history.json` — recently-closed tickets per user (for "My Tickets")
- `diff_data/diff_backup_state.json` — persists `_last_backup_ts` across restarts so the weekly backup loop is idempotent (prevents spam when bot is redeployed several times in a row)
- `diff_data/diff_popup_meets.db` — SQLite, Pop-Up Meet system (meets, RSVPs, threads)

### Logs
- `logs/bot.log`

## Feature Systems
- Host activity tracking & hierarchy
- Announcements & roll calls
- Warnings & appeals (with `!deletewarn` for false-positive removal)
- Crew recruitment
- Reputation system
- Meet attendance + no-show dispute button (DM crew on finalization)
- Ticket workflow
- Moderation
- Marketplace
- Leaderboards
- Partnership system
- Color Lab (`!color`, `!resetcolor`)
- Loop health system (`!bothealth`, `!loopstatus`) — 19 loops, all with `run_with_timeout` + error recovery
- **Member Retention System** — join/message/VC timestamps, leave analytics, drop-off stage detection, unverified DM reminders, re-engagement DMs, inactivity daily report
- **Member Health Score System** — 0–100 score per member, 4 tiers (Strong/Active/At Risk/Ghost), 4h batch recalc loop, per-member breakdown, trend tracking, history table
- **HP Session Cleanup** — hourly stale-session auto-close (24h+) with staff alert; daily 3 AM archive of sessions 60d+ old

## Extra Commands Added (batch 3)
| Command | Access | Description |
|---|---|---|
| `!deletewarn @user <id>` | Leadership | Remove a specific warning by ID |
| `!clearnotes @user` | Leadership | Wipe all leadership notes for a host |
| `!remindhost @user` | Leadership | DM a host their current week slot details |
| `!exportstats` | Leadership | Export all host_stats as a dated CSV file |
| `!hostsummary` | Leadership | Weekly host activity digest (sessions, scores, warnings) |
| `!weeklydigest` | Leadership | Full weekly digest posted to staff logs (RC + HP + warnings) |
| `!mystats` | Host + Crew | Self-lookup: HP score, streak, RC record, active warnings |

## Data Files
| File | Purpose |
|---|---|
| `diff_data/diff_host_performance.json` | HP sessions + host_stats |
| `diff_data/diff_warnings.json` | Formal warnings per member |
| `diff_data/diff_host_notes.json` | Leadership notes per host |
| `diff_data/diff_rc_streaks.json` | RC attendance streaks |
| `diff_data/diff_hp_session_archive.json` | Archived HP sessions (60d+) |

## Health Score System

### Schema (member_activity)
New columns: `last_health_score`, `prev_health_score`, `health_tier`, `score_updated_at`

New table: `health_score_history (id, user_id, score, tier, recorded_at)`

### Weights (`_HEALTH_W` dict — configurable)
**Positive:** verified +20, application +15, first meet +20, extra meets +5 (cap 10), recent msg 7d +10, recent VC 7d +10, join age 30d+ +5  
**Negative:** inactive 7d −10, 14d −20, 30d −30; unverified 24h −5, 72h −15 (stacks); ghost (no msg 48h+) −20

### Tiers
- 💚 Strong (80–100)
- 🔵 Active (60–79)
- 🟡 At Risk (40–59)
- 🔴 Ghost (0–39)

### Commands (staff prefix only)
| Command | Aliases | Description |
|---|---|---|
| `!healthscore [@user]` | `!score`, `!hs` | Full score breakdown with bar, factors, trend, recs |
| `!healthleaderboard` | `!healthtop`, `!scoreboard` | Top 15 members by score |
| `!healthstats` | `!tierstats`, `!scorestats` | Server-wide tier & trend breakdown |
| `!ghostmembers` | `!ghosts`, `!deadweight` | List Ghost-tier members (score < 40) |

### Loop
`_health_score_update_loop` — every 4h, calculates all tracked members; wired in `on_ready`

## Smart Auto Cleanup + Recovery System

### File layout
| File | Purpose |
|---|---|
| `cogs/cleanup.py` | Cog — background loop (6h), listeners, 6 prefix commands |
| `utils/cleanup_logic.py` | Config, DB helpers, flag CRUD, exemption checks |
| `utils/recovery_tracker.py` | Recovery event logging + status computation |
| `database/retention.db` | SQLite — auto-created on boot |

### Database tables (retention.db)
- `cleanup_flags` — one row per flagged member (flag_type, grace, reminders, review_state, recovered, reason, score snapshot)
- `recovery_events` — timestamped events per user (message, vc_join, meet_attend, verified, score_up)
- `action_history` — full audit log of staff and automatic actions

### Config (`CLEANUP_CONFIG` in `utils/cleanup_logic.py`)
All thresholds are editable at the top of the file:
- `dm_reminders_enabled`, `auto_kick_enabled`, `require_staff_review`
- `grace_period_at_risk` (3d) / `grace_period_ghost` (2d)
- `max_reminders` (2), `reminder_cooldown_days` (3)
- `min_join_age_days` (7), `inactivity_days_at_risk` (7), `inactivity_days_ghost` (14)
- `scan_score_at_risk_max` (59), `scan_score_ghost_max` (39)

### Flag types & lifecycle
`Safe` → flagged as `At Risk` or `Ghost` → grace period → `Cleanup Review` → staff decision  
Recovery at any stage (message / VC join) resets to `Safe` + logs to staff channel.

### Exempt roles (never flagged)
Leader, Co-Leader, Manager, Moderator, Admin, Host, Senior Host, Head Host, Junior Host, Staff, Bot + any members who joined within `min_join_age_days`.

### Commands (staff prefix only — all in `cogs/cleanup.py`)
| Command | Aliases | Description |
|---|---|---|
| `!cleanupscan` | `!runscan`, `!forcescan` | Manually trigger a full scan |
| `!cleanupqueue` | `!reviewqueue`, `!cqueue` | Show members in Cleanup Review |
| `!recoveries` | `!recovered`, `!recoveredmembers` | Show recently recovered members |
| `!flagmember @user` | `!manuallyflag`, `!addflag` | Manually flag for review |
| `!clearflag @user` | `!removeflag`, `!unflag` | Remove a member's flag |
| `!cleanupstats` | `!cstats`, `!flagstats` | Stats + current config overview |

### Deploy note
New files to copy on deploy:
```
scp -r utils/ thomas@192.168.1.211:/home/thomas/diff-bot/
scp cogs/cleanup.py thomas@192.168.1.211:/home/thomas/diff-bot/cogs/cleanup.py
scp bot.py thomas@192.168.1.211:/home/thomas/diff-bot/bot.py
sudo systemctl restart different-meets-v2
```

## Loop Health
All loops use:
- `_loop_fail_counts` / `_loop_alerted` / `_loop_last_run` tracking
- `run_with_timeout()` wrapper
- `trigger_system_restart()` global failsafe (5 unique loops failing in 60s → `os._exit(1)`)

### Restart-resilient state (important pattern)
Module-level timestamps used by `@tasks.loop` gating MUST be persisted to disk, otherwise every redeploy resets them to 0 and re-fires the loop body immediately. Reference impl: `diff_backup_state.json` + `_backup_state_load_ts()`/`_backup_state_save_ts()`. Same pattern should be used for any future "fire at most every N hours" loop.

### `on_ready` is not single-shot
Discord reconnects fire `on_ready` again. Any `bot.loop.create_task(_loop())` in `on_ready` must be guarded by a module-level task handle (`if _task is None or _task.done(): _task = bot.loop.create_task(...)`) — otherwise reconnects spawn duplicate workers (and duplicate DMs / actions). Reference impl: `_popup_auto_end_task` guard in `on_ready`.

## Pop-Up Meet System
- `cogs/diff_meet_host_system.py` panel + bot.py `_popup_*` core
- SQLite at `diff_data/diff_popup_meets.db` (table `popup_meets` with `is_started`, `started_at`, `is_ended`, etc.)
- Auto-close uses **two separate caps** (May 26 2026 fix):
  - **Live meets** (`is_started=1`) → `_POPUP_AUTO_END_HOURS` (3h) measured from `started_at`
  - **Never-started meets** → `_POPUP_ABANDON_HOURS` (24h) measured from `created_at`
  - Last-call DM (`~30 min before close`) only fires for live meets
- Pop-up views are re-hydrated on startup (`[Popup] Re-hydrated N active meet view(s)`)

## Support Ticket Panel UX (May 26 2026)
- Buttons order: **My Tickets / Ask Q / Report / Apply / Urgent**
- New tickets auto-post a context embed (member age, recent warning, etc.)
- **Ask a Question** runs FAQ deflection first (6 default entries, build-rules text is PS5-only)
- On close → CSAT DM to the ticket opener (rating saved to `diff_data/diff_csat.json`, reportable via `!csatreport`)
- **My Tickets** lists recently-closed tickets from `diff_data/diff_ticket_history.json`
- Appeal predictive suggestion when member has an active warning <30d old (`_FaqDeflectAppealButton` runs `_appeal_denial_check`, posts staff-logs, alerts mod-hub — parity with `AppealDropdown`)

## Removed: PSN Host Status Board (May 22 2026)
The PSN integration (psnawp + `_psn_*` helpers + `_psn_board_refresh_loop` + `!setpsn`/`!removepsn`/`!psnboard`/`!refreshpsnboard`/`!psntest`/`!psnlist` commands) was removed because Sony's PSN API was starving the default asyncio thread pool when it hung, freezing the entire event loop and causing silent bot offlines that required physical Pi reboots (systemd couldn't recover because the process was still alive). The `host_board_auto_refresh_loop` now always renders the static `build_status_embed()` instead of live PSN presence. The `psnawp` package was removed from `requirements.txt`. Data file `diff_data/diff_psn_map.json` is untouched and can be safely deleted on the Pi.
