# Different Meets V2 — Discord Bot

**Community:** DIFF Meets (PlayStation GTA car meet community)
**Runtime:** Python 3.11 / discord.py 2.7.1
**Deployed on:** Raspberry Pi 5 at `~/diff-bot/`  
**Venv:** `/home/thomas/diff-bot/.venv/bin/python`  
**Service:** `different-meets-v2` (systemd)  
**Deploy:** `scp bot.py thomas@192.168.1.211:/home/thomas/diff-bot/bot.py && ssh thomas@192.168.1.211 "sudo systemctl restart different-meets-v2"`

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
`bot.py` — ~30,400 lines. All core logic, all prefix commands, all event handlers.

### Cogs
- `cogs/diff_color_lab.py` — Color Lab
- `cogs/diff_automod.py` — AutoMod

### Data files
- `diff_data/diff_activity.db` — SQLite (member_activity, member_leaves, leave_surveys, health_score_history)
- `diff_data/diff_partner_panel.json` — partnership panels
- `diff_data/diff_partnerships.json` — partnership records

### Logs
- `logs/bot.log`

## Feature Systems
- Host activity tracking & hierarchy
- Announcements & roll calls
- Warnings & appeals
- Crew recruitment
- Reputation system
- Meet attendance
- Ticket workflow
- Moderation
- Marketplace
- Leaderboards
- Partnership system
- Color Lab (`!color`, `!resetcolor`)
- Loop health system (`!bothealth`, `!loopstatus`) — 19 loops, all with `run_with_timeout` + error recovery
- **Member Retention System** — join/message/VC timestamps, leave analytics, drop-off stage detection, unverified DM reminders, re-engagement DMs, inactivity daily report
- **Member Health Score System** — 0–100 score per member, 4 tiers (Strong/Active/At Risk/Ghost), 4h batch recalc loop, per-member breakdown, trend tracking, history table

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

## Loop Health
All 19 loops (plus new health score loop = 20) use:
- `_loop_fail_counts` / `_loop_alerted` / `_loop_last_run` tracking
- `run_with_timeout()` wrapper
- `trigger_system_restart()` global failsafe (5 unique loops failing in 60s → `os._exit(1)`)
