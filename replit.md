# Different Meets V2 — Discord Bot

**Community:** DIFF Meets (PS5 GTA car meet community)
**Runtime:** Python 3.11+ / discord.py 2.7.1 (Pi runs python3.13 venv)
**Deployed on:** Raspberry Pi 5 at `~/diff-bot/` (venv `.venv/`, systemd `different-meets-v2`)
**Deploy:** `cd ~/diff-bot && bash deploy.sh` → `git fetch && git reset --hard origin/main && pip install -q -r requirements.txt && systemctl restart`. Data files are git-untracked, hard reset is safe.

**Agent push workflow:** edit `/home/runner/workspace/bot.py` → `py_compile` → push via GitHub Git Data API (blob → tree → commit → PATCH ref) with `python3 + urllib` (`/tmp/push.py`; recreate if /tmp resets). Repo: `thomasmilling12/diff-bot`, branch `main`. Secrets: `DISCORD_TOKEN`, `GITHUB_TOKEN`, `OPENAI_API_KEY`. Bot runs on Pi only — never start it here.

## Critical Rules
- Timezone: always `ZoneInfo("America/New_York")` — never `"US/Eastern"`
- Global slash commands at cap (100) → all new commands must be **prefix (`!`) or guild-scoped**
- Never mass-DM guild members from a task loop (Discord Developer Policy)
- `sqlite3.Row`: use `row["key"]`, never `.get()`
- In cogs: never `import bot` — use `sys.modules.get("__main__")`
- PS5 only — never mention PS4 in user-facing embeds
- `on_ready` is NOT single-shot (reconnects re-fire it). Any `bot.loop.create_task(...)` in `on_ready` needs a module-level task-handle guard. Ref: `_popup_auto_end_task`.
- `@tasks.loop` "at most every N hours" gating timestamps MUST persist to disk, else every redeploy re-fires them. Ref: `diff_backup_state.json`.
- Long-running/external calls (PSN, OCR, OpenAI) MUST use `asyncio.to_thread()` — Sony PSN API hang on May 22 2026 froze the event loop unrecoverably.
- Interaction handlers: `defer()` BEFORE any lock acquire or slow operation (3s ack window). Ref: `_supp_open_ticket_flow`.
- Requirements: keep pins as `>=` not `==` (`discord.py==2.3.2` once silently downgraded Pi's 2.7.1).

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
| LOBBY_PICTURES_CHANNEL_ID | 1089579004517953546 |
| _POSTMEET_HOST_POSTERS_ID | 1091157191895023626 |

## Architecture
- `bot.py` — ~44,600 lines. All core logic, prefix commands, event handlers. Single source of truth.
- `cogs/` — auxiliary loaders: `diff_color_lab`, `diff_automod`, `diff_meet_host_system`, `diff_mod_hub`, `diff_full_moderation`, `diff_next_level_moderation`, `cleanup`.
- **Disabled cog command stubs** (bot.py owns the richer version — stub stays commented so cog loads): `diff_full_moderation` → `hostprofile` • `diff_next_level_moderation` → `weeklyreport` • `diff_host_posters.py` DELETED (duplicate `postmeet`).
- Logs: `logs/bot.log`. Loop health: `_loop_fail_counts` + `run_with_timeout()` + `trigger_system_restart()` (5 unique loops failing in 60s → `os._exit(1)`). Cmds: `!bothealth`, `!loopstatus`.
- Staff-logs decluttered (Jul 2026): automod "Member Left" card only posts for kicks/bans (fail-open if audit-log read errors) — plain leaves covered by the Leave Analytics embed; Daily Retention Report uses plain display names + exclusive 7+/3–7d buckets; Auto Cleanup posts ONE `🧹 Auto Cleanup Scan` embed per scan.

## Data Files (all in `diff_data/`)
| File | Purpose |
|---|---|
| `diff_activity.db` | SQLite — member_activity, member_leaves, leave_surveys, health_score_history |
| `diff_popup_meets.db` | SQLite — Pop-Up Meets (meets, RSVPs, threads) |
| `diff_xp.db` | SQLite — XP: `xp` totals • `xp_awards` PK-dedup • `xp_week` per-ISO-week (MOTW source of truth) • `xp_badges` |
| `diff_host_performance.json` | HP sessions + host_stats |
| `diff_host_posters.json` | Host Posters embed state |
| `diff_host_notes.json` | Leadership notes per host |
| `diff_warnings.json` | Formal warnings per member (the store `!warnings` reads) |
| `diff_rc_streaks.json` | Roll-call streaks (keys `streak`/`best` — NOT `current_streak`) |
| `diff_rc_week_snapshot.json` | Pre-wipe snapshot of week's roll-call responses (Mon-00:00 reset writes; Mon-00:15 pruning report reads) |
| `diff_rc_reminder_state.json` | Roll-call weekly-reset + Sunday-reminder once-per-week guards |
| `diff_rc_strike_state.json` | Consecutive no-response streaks + strike candidates |
| `diff_hp_session_archive.json` | Archived HP sessions (60d+) |
| `diff_partner_panel.json` + `diff_partnerships.json` | Partnership panels + records |
| `diff_csat.json` / `diff_ticket_history.json` / `diff_ticket_perf.json` / `diff_ticket_digest_state.json` / `diff_ticket_close_log.json` | Ticket CSAT • per-user closed history • SLA timestamps • 9 AM digest guard • rolling close log (7d ETA) |
| `diff_canned_replies.json` / `diff_faq.json` | Staff canned replies • FAQ deflection entries |
| `diff_anon_reports.json` | Anonymous tips (Leadership reveal only) |
| `diff_backup_state.json` | Idempotent weekly backup `_last_backup_ts` |
| `diff_lobby_pictures.json` / `diff_lobby_gallery_state.json` / `diff_lobby_wm_prefs.json` | Lobby pic state • weekly gallery guard • watermark prefs |
| `diff_psn_map.json` | PSN→user_id (Lobby Pictures OCR — DO NOT DELETE) |
| `diff_community_role.json` | ID of auto-created "Community Member" joiner role (≠ MEET_ATTENDER_ROLE_ID) |
| `diff_xp_roles.json` / `diff_xp_config.json` | XP ladder role IDs • XP channels + `last_motw_week` guard |
| `diff_recap_state.json` / `diff_meet_recap_state.json` | Weekly recap channel + week guard • per-meet recap channel + `seeded` + posted map |
| `diff_aimod_state.json` | AI Mod Assist `{enabled, channel_id}` — cached in `_aimod_state_cache`, hot-path never reads disk |

## Feature Systems (one-line map)
Host activity & hierarchy • Announcements & roll calls • Warnings & appeals • Crew recruitment • Reputation • Meet attendance + no-show dispute • Support + Join tickets • Moderation • Marketplace • Leaderboards • Partnerships • Color Lab • Loop health • Member Retention • Member Health Score • Smart Auto Cleanup • Pop-Up Meets • Host Posters • Lobby Pictures • AI Pre-Ticket Triage • XP/Levels/Badges/MOTW • Weekly AI Recap • Per-Meet Recaps • AI Moderation Assist • GitHub backups • Stats dashboard.

## XP / Levels / Badges / MOTW
All award sites try/except, silent on failure. `award_once` commits dedup marker + XP in ONE transaction. Curve: XP for level L = `50*L*(L+1)` (`_xp_level_for` inverse uses `** 0.5`). Week key `_xp_week_key()` = "YYYY-Wnn" ISO ET.
**Earning:** message +5 (60s cd) • RSVP-yes +10 • lobby-pic +15 (3/day) • meet-attend +50 (all finalizes) • voice +5/10min (≥2 non-deaf non-bot). **Ladder:** L5 Regular • L10 Veteran • L20 Elite • L35 Legend (keep highest only).
**Badges (`_XP_BADGES`, 13):** attendance 1/5/15/30 • RC streak 4/8/16 • pics 5/20 • level 5/10/20/35. `_xp_compute_earned` → `_xp_check_badges` (idempotent insert, DM on fresh only). Lazy backfill on `!badges`.
**MOTW:** `xp_week` bucket written in same transaction as XP. `_xp_motw_loop` (10 min) keys off most recently COMPLETED ISO week; seeds on first run; marks guard only AFTER successful post; prunes >8 weeks.
**Cmds:** `!rank` `!xpboard` `!xpinfo` `!badges` `!badgeboard` `!motw` (members) • `!givexp` `!takexp` `!setlevelchannel` `!setmotwchannel` (Leadership).
**Known edge (deferred):** RSVP/attend dedup key is week-at-award-time, not immutable meet id — rare post-rollover re-finalize could re-grant.

## Member Health Score
Tiers: 💚 80–100 • 🔵 60–79 • 🟡 40–59 • 🔴 0–39. Weights in `_HEALTH_W`. Loop `_health_score_update_loop` 4h. Cmds (staff): `!healthscore` `!healthleaderboard` `!healthstats` `!ghostmembers`.

## Smart Auto Cleanup + Recovery
`cogs/cleanup.py` + `utils/cleanup_logic.py` + `utils/recovery_tracker.py` + `database/retention.db`. Lifecycle: Safe → flagged (At Risk|Ghost) → grace → Cleanup Review → staff decision; recovery resets to Safe. Exempt: all staff/host roles + joins <7d. One summary embed per 6h scan. Cmds: `!cleanupscan` `!cleanupqueue` `!recoveries` `!flagmember` `!clearflag` `!cleanupstats`.

## Pop-Up Meets / Host Posters
**Pop-Up:** `cogs/diff_meet_host_system.py` panel + bot.py `_popup_*` • `diff_popup_meets.db`. Auto-close: live 3h from start, never-started 24h from create. Last-call DM only for live meets. Views re-hydrate on startup.
**Host Posters:** image in `#hosts-posters`, caption `<date> | <time> [| <theme>]`, hosts = mentions (fallback author). Reply embed + role-gated `_HostPosterActionsView`: single 📩 Received (`diff_hp_received`) + 📸 Upload. Hosts DM'd "poster ready to download" (skips self-uploaders). Reminder loop 5 min: T-2h DM non-received, T-30m zero-received → ping staff+hosts. `!editposter` (reply to embed) re-parses. Legacy custom_ids (`diff_postmeet_received`, old attending/decline/help) all route to "received" via `_PostmeetReceivedView`.

## Support Ticket System
Panel: My Tickets / Ask Q / Report / Apply / Urgent + Anonymous Tip. Single close entry point `_perform_ticket_close(channel, closer, reason_key)`; `_CSAT_SKIP_REASONS = {"spam","no_response"}`. Claim via topic `ticket_claimed_by=`. 48h warn → 72h auto-close. Urgent unclaimed 5min → pings support+leadership. Daily 9 AM digest (idempotent). Per-user open lock — `defer()` before acquire. 7-day reopen from CSAT DM. Anonymous tips: Leadership-only reveal, audit-logged. `_ti_*` helpers: close-log ETA, least-busy staff, keyword auto-tag (AI overrides). Join tickets: `JoinTicketView` + Quick Reply presets + micro-bump DM.
**Staff cmds:** `!ticketstats` • `!canned*` • `!faq*` • `!staffload`.

## AI Features (all silent-fallback, `gpt-4o-mini`, JSON mode, `asyncio.to_thread`)
Shared helpers: `_ai_enabled()` `_ai_chat()` `_AI_BASE_CTX`. If AI off/unparseable → exact pre-AI behavior. Pi needs `OPENAI_API_KEY` in the systemd unit.
- **Pre-Ticket Triage:** `_AiAskQuestionModal` FAQ deflection (grounded in `_FAQ_DEFLECT_ENTRIES[:12]`) • `_AiUrgentDescribeModal` severity check (`_ai_check_urgent` defaults true on failure) • AI routing note + tag on ticket open.
- **Weekly Recap (P3a):** `_community_recap_loop` — exact ISO-week bounds via `fromisocalendar`, all sources bounded to that week, no warnings shown. `!recap` preview • `!setrecapchannel`.
- **Per-Meet Recaps (P3b):** `_meet_recap_loop` — groups lobby pics by meet_key, per-record try/except, eligible 8h–7d with ≥1 pic, hero = most-reacted. `!meetrecap` preview • `!setmeetrecap`.
- **Mod Assist (P3c):** ADVISORY ONLY. Auto-scan default OFF; cheap prefilter before AI; cost gates: 120s/user + 40 calls/hr global. `!modcheck` on-demand • `!aimod on/off/channel`. Complementary to `cogs/diff_automod` (which owns real auto-actions).
- Loop discipline (recaps + MOTW): completed-period keying • first-run seed (no backfill) • mark-after-success.

## Lobby Pictures
Non-image/non-Verified posts auto-deleted with DM (`process_commands` runs first). Auto-match to closest meet within `_LP_MATCH_WINDOW_HOURS=6`. HP 📸 button arms `_lp_pending_uploads` 600s fast-path. OCR (pytesseract, best-effort) → PSN tokens cross-ref `diff_psn_map.json` → grants MEET_ATTENDER role. Opt-in watermark (`!lobbywatermark`). Auto-pin top-reacted (6–30h window). Weekly gallery Monday 10 AM. 30d metadata retention. Cmds: `!setlobbypics` `!lobbystats` `!crewboard`. Gotcha: `_LobbyPicUploadBtn` added in `__init__` via try/except; `custom_id="diff_lp_upload"`.

## Roll Call: Reminders, Leaderboards, Auto-Strike
- **Weekly auto-reset:** `_rc_weekly_reset_loop` Monday 00:00 ET — snapshots to `diff_rc_week_snapshot.json` BEFORE wiping, then fresh panel + crew ping. Guard `last_weekly_reset` in `diff_rc_reminder_state.json`; first-run SEEDED (no wipe) so mid-week deploys can't erase a live week.
- **Pruning report** (Mon 00:15) prefers the snapshot when same-Monday + guild matches + `reset_completed` — else reads live DB.
- **Reminders:** Sat noon DM loop • Sunday 6 PM public channel nudge (disk-guarded) • `!rcremind [tag]` on-demand • T-5h crew-chat ping of yes responders (`_rc_t5h_reminder_loop`, guard `t5h_sent` keyed `meet:start_ts` in `diff_rc_reminder_state.json`; maybe-list as display names in embed).
- **Leaderboards:** `!attendanceboard` (persistent `attendance_stats` + show-up %) • `!streakboard` • `!mystats`.
- **`!autoattend`:** cross-refs lobby-pic OCR with RSVPs → preview embed → Leadership "Apply & Finalize" → standard finalize pipeline (DMs no-shows w/ dispute view). Never auto-punishes. Finalized source of truth: `meet_state.attendance_finalized`, NOT `rollcall_meets.is_finalized`.
- **Auto-strike:** `_rc_pruning_report_loop` tracks miss streaks (`diff_rc_strike_state.json`); ≥2 weeks → candidates embed w/ persistent confirm view; Leadership click issues formal warning into `diff_warnings.json` + DM. Exempt: Leadership + Host; all-"no" responders never struck.

## Infrastructure / Backups
- **Discord zip backup** (weekly, JSON-only → STAFF_LOGS) + **GitHub backup**: `_run_github_backup_once` pushes `diff_data/` (json raw + sqlite `.backup()` snapshots) to dedicated **`backups` branch** (deploy.sh only resets `main`). No force-push (retry-once on non-FF); `_gh_backup_lock`; all network in `to_thread`. `!githubbackup`. ⚠️ Repo must stay private. Restore: checkout `backups` → copy `diff_data/` to Pi.
- **Stats dashboard** (`stats_web.py`): Flask daemon thread, starts from `on_ready` only if `STATS_WEB_PASSWORD` env set. Binds 127.0.0.1 (expose via cloudflared tunnel). Basic Auth, read-only, own `?mode=ro` sqlite conns per request, `html.escape` everywhere. Env: `STATS_WEB_PASSWORD` / `STATS_WEB_USER` (staff) / `STATS_WEB_PORT` (8081).

## Extra Staff Commands
`!deletewarn @u <id>` • `!clearnotes @u` • `!remindhost @u` • `!exportstats` • `!hostsummary` • `!weeklydigest` • `!mystats` (Host+Crew self-lookup).

## Removed Systems
- **PSN Host Status Board** (May 22 2026): `psnawp` + `_psn_*` removed — Sony API hang froze the event loop. Host board renders static embed. `diff_psn_map.json` KEPT (Lobby Pictures OCR).
