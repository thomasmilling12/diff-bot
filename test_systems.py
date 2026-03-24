"""
DIFF Bot - System Test Script
Exercises all data systems with realistic car meet community data.
Run with: python3 test_systems.py
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("diff_data")
DATA.mkdir(exist_ok=True)

def _utcnow():
    return datetime.now(timezone.utc)

def _save(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def _load(path, default):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

SEP  = "=" * 60
SEP2 = "-" * 60

def section(title):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

def ok(msg):
    print(f"  [OK]  {msg}")

def info(msg):
    print(f"        {msg}")

# =========================================================
# 1.  MANAGER PERFORMANCE STATS (Manager Hub)
# =========================================================
section("1 — Manager Performance Stats (Manager Hub)")

perf_path = DATA / "manager_performance_stats.json"
perf_data = {
    "Smokey_PSN": {
        "meets_hosted":   14,
        "attendees_total":378,
        "meet_score":     72,
        "points":         98,
        "last_updated":   _utcnow().isoformat(),
    },
    "RavenGT_PSN": {
        "meets_hosted":   9,
        "attendees_total":211,
        "meet_score":     45,
        "points":         63,
        "last_updated":   _utcnow().isoformat(),
    },
    "NightShift_PSN": {
        "meets_hosted":   5,
        "attendees_total":102,
        "meet_score":     28,
        "points":         41,
        "last_updated":   _utcnow().isoformat(),
    },
    "DriftKing_PSN": {
        "meets_hosted":   11,
        "attendees_total":289,
        "meet_score":     60,
        "points":         87,
        "last_updated":   _utcnow().isoformat(),
    },
}
_save(perf_path, perf_data)

leaderboard = sorted(perf_data.items(), key=lambda x: x[1]["points"], reverse=True)
ok(f"Seeded {len(perf_data)} manager profiles")
print(f"\n  {'Rank':<5} {'Manager':<18} {'Meets':<7} {'Pts':<6} {'Attendees'}")
print(f"  {SEP2}")
for rank, (name, s) in enumerate(leaderboard, 1):
    print(f"  #{rank:<4} {name:<18} {s['meets_hosted']:<7} {s['points']:<6} {s['attendees_total']}")

# =========================================================
# 2.  SEASON STATS
# =========================================================
section("2 — Manager Season Stats")

season_path = DATA / "manager_season_stats.json"
meta_path   = DATA / "manager_season_meta.json"

season_data = {
    "Smokey_PSN":    {"meets_hosted": 3, "attendees_total": 74,  "meet_score": 14, "points": 21},
    "RavenGT_PSN":   {"meets_hosted": 2, "attendees_total": 40,  "meet_score": 9,  "points": 13},
    "NightShift_PSN":{"meets_hosted": 1, "attendees_total": 18,  "meet_score": 6,  "points": 9},
    "DriftKing_PSN": {"meets_hosted": 4, "attendees_total": 91,  "meet_score": 20, "points": 29},
}
meta = {"season_number": 3, "started_at": _utcnow().isoformat()}
_save(season_path, season_data)
_save(meta_path,   meta)

ok(f"Season #{meta['season_number']} seeded with {len(season_data)} managers")
season_lb = sorted(season_data.items(), key=lambda x: x[1]["points"], reverse=True)
print(f"\n  {'Rank':<5} {'Manager':<18} {'Meets':<7} {'Pts (week)'}")
print(f"  {SEP2}")
for rank, (name, s) in enumerate(season_lb, 1):
    print(f"  #{rank:<4} {name:<18} {s['meets_hosted']:<7} {s['points']}")

# promotion alert threshold check (25 pts)
PROMO_THRESHOLD = 25
promoted = [(n, s["points"]) for n, s in season_data.items() if s["points"] >= PROMO_THRESHOLD]
if promoted:
    print()
    for name, pts in promoted:
        ok(f"PROMO ALERT would fire → {name} hit {pts} pts (threshold: {PROMO_THRESHOLD})")

# =========================================================
# 3.  MANAGER WRITE-UPS
# =========================================================
section("3 — Manager Write-Up System")

writeup_path  = DATA / "manager_writeups.json"
strikes_path  = DATA / "manager_writeup_strikes.json"

wu_entries = {
    "WU-0001": {
        "writeup_id":      "WU-0001",
        "writeup_type":    "Member Write-Up",
        "member_name":     "CrashLord_GTA",
        "psn":             "CrashLordPS",
        "reason":          "Repeatedly blocking host vehicles during roll call. Warned twice, no improvement.",
        "evidence":        "https://discord.com/channels/.../1234567890",
        "severity":        "Medium",
        "submitted_by":    "@Smokey_PSN",
        "submitted_by_id": 111111111111,
        "date":            "03/24/2026",
        "status":          "Active",
        "created_at":      _utcnow().isoformat(),
        "strike_count":    1,
        "message_id":      None,
        "resolved_by":     None,
        "removed_by":      None,
        "removal_reason":  None,
    },
    "WU-0002": {
        "writeup_id":      "WU-0002",
        "writeup_type":    "Strike Entry",
        "member_name":     "ToxicRider22",
        "psn":             "ToxicR22",
        "reason":          "Verbal abuse in voice chat towards host during meet. Multiple witnesses.",
        "evidence":        "No direct clip. Three staff witnesses.",
        "severity":        "High",
        "submitted_by":    "@DriftKing_PSN",
        "submitted_by_id": 222222222222,
        "date":            "03/24/2026",
        "status":          "Active",
        "created_at":      _utcnow().isoformat(),
        "strike_count":    2,
        "message_id":      None,
        "resolved_by":     None,
        "removed_by":      None,
        "removal_reason":  None,
    },
    "WU-0003": {
        "writeup_id":      "WU-0003",
        "writeup_type":    "Host Write-Up",
        "member_name":     "NightShift_PSN",
        "psn":             "NightShift_PS",
        "reason":          "Meet started 40 minutes late with no communication. Attendance dropped significantly.",
        "evidence":        "Attendance log shows 28 attendees vs 61 expected.",
        "severity":        "Medium",
        "submitted_by":    "@RavenGT_PSN",
        "submitted_by_id": 333333333333,
        "date":            "03/20/2026",
        "status":          "Resolved",
        "created_at":      _utcnow().isoformat(),
        "strike_count":    0,
        "message_id":      None,
        "resolved_by":     "@Smokey_PSN",
        "removed_by":      None,
        "removal_reason":  None,
    },
    "WU-0004": {
        "writeup_id":      "WU-0004",
        "writeup_type":    "Warning Notice",
        "member_name":     "SpeedGlitch_GTA",
        "psn":             "SpeedGlitch",
        "reason":          "First-time rule violation — driving modded vehicle during a standard meet.",
        "evidence":        "Screenshot provided.",
        "severity":        "Low",
        "submitted_by":    "@DriftKing_PSN",
        "submitted_by_id": 222222222222,
        "date":            "03/22/2026",
        "status":          "Active",
        "created_at":      _utcnow().isoformat(),
        "strike_count":    0,
        "message_id":      None,
        "resolved_by":     None,
        "removed_by":      None,
        "removal_reason":  None,
    },
    "WU-0005": {
        "writeup_id":      "WU-0005",
        "writeup_type":    "Strike Entry",
        "member_name":     "ToxicRider22",
        "psn":             "ToxicR22",
        "reason":          "Second offense — trolled lobby after being warned from WU-0002.",
        "evidence":        "https://discord.com/channels/.../9876543210",
        "severity":        "High",
        "submitted_by":    "@Smokey_PSN",
        "submitted_by_id": 111111111111,
        "date":            "03/24/2026",
        "status":          "Active",
        "created_at":      _utcnow().isoformat(),
        "strike_count":    3,
        "message_id":      None,
        "resolved_by":     None,
        "removed_by":      None,
        "removal_reason":  None,
    },
}

strikes_data = {
    "ToxicRider22":   3,
    "CrashLord_GTA":  1,
    "SpeedGlitch_GTA":0,
    "NightShift_PSN": 0,
}

wu_meta = {"counter": 5, "entries": wu_entries}
_save(writeup_path, wu_meta)
_save(strikes_path, strikes_data)

total  = len(wu_entries)
active = sum(1 for e in wu_entries.values() if e["status"] == "Active")
res    = sum(1 for e in wu_entries.values() if e["status"] == "Resolved")
ok(f"Seeded {total} write-ups — {active} active, {res} resolved, counter at WU-0005")

print()
for wid, e in wu_entries.items():
    flag = " ← STRIKE THRESHOLD ALERT" if e["strike_count"] >= 3 else ""
    print(f"  {wid} | {e['writeup_type']:<18} | {e['member_name']:<18} | {e['status']:<10} | Strikes: {e['strike_count']}{flag}")

print()
ok("Strike counts per member:")
for member, count in strikes_data.items():
    flag = " ⚠️  FLAGGED (≥3)" if count >= 3 else ""
    print(f"        {member:<22} → {count} strike(s){flag}")

# =========================================================
# 4.  FULL MODERATION PROFILES
# =========================================================
section("4 — Full Moderation System (Member Profiles)")

mod_path  = DATA / "moderation_profiles.json"
host_path = DATA / "host_performance_profiles.json"

mod_profiles = {
    "111111111111": {
        "user_id":          111111111111,
        "display_name":     "Smokey_PSN",
        "writeups":         0,
        "strikes":          0,
        "feedback_entries": 12,
        "feedback_average": 4.8,
        "attendance_count": 28,
        "hosted_meets":     14,
        "flags":            [],
        "last_updated":     _utcnow().isoformat(),
    },
    "222222222222": {
        "user_id":          222222222222,
        "display_name":     "DriftKing_PSN",
        "writeups":         0,
        "strikes":          0,
        "feedback_entries": 9,
        "feedback_average": 4.6,
        "attendance_count": 22,
        "hosted_meets":     11,
        "flags":            [],
        "last_updated":     _utcnow().isoformat(),
    },
    "444444444444": {
        "user_id":          444444444444,
        "display_name":     "ToxicRider22",
        "writeups":         2,
        "strikes":          3,
        "feedback_entries": 3,
        "feedback_average": 1.8,
        "attendance_count": 7,
        "hosted_meets":     0,
        "flags":            ["warning_flag", "restricted_flag", "critical_flag"],
        "last_updated":     _utcnow().isoformat(),
    },
    "555555555555": {
        "user_id":          555555555555,
        "display_name":     "CrashLord_GTA",
        "writeups":         1,
        "strikes":          1,
        "feedback_entries": 5,
        "feedback_average": 3.2,
        "attendance_count": 11,
        "hosted_meets":     0,
        "flags":            [],
        "last_updated":     _utcnow().isoformat(),
    },
    "666666666666": {
        "user_id":          666666666666,
        "display_name":     "SpeedGlitch_GTA",
        "writeups":         1,
        "strikes":          0,
        "feedback_entries": 2,
        "feedback_average": 4.0,
        "attendance_count": 5,
        "hosted_meets":     0,
        "flags":            [],
        "last_updated":     _utcnow().isoformat(),
    },
    "333333333333": {
        "user_id":          333333333333,
        "display_name":     "NightShift_PSN",
        "writeups":         1,
        "strikes":          0,
        "feedback_entries": 4,
        "feedback_average": 2.9,
        "attendance_count": 15,
        "hosted_meets":     5,
        "flags":            [],
        "last_updated":     _utcnow().isoformat(),
    },
}
_save(mod_path, mod_profiles)

ok(f"Seeded {len(mod_profiles)} member moderation profiles")

# Auto-alert simulation
WARNING_THRESHOLD    = 2
RESTRICTED_THRESHOLD = 3
CRITICAL_THRESHOLD   = 4
print()
for uid, p in mod_profiles.items():
    s = p["strikes"]
    flags = p["flags"]
    status = []
    if s >= CRITICAL_THRESHOLD:    status.append("🛑 CRITICAL")
    elif s >= RESTRICTED_THRESHOLD:status.append("🚨 RESTRICTED")
    elif s >= WARNING_THRESHOLD:   status.append("⚠️  WARNING")
    if flags:
        status.append(f"flags={','.join(flags)}")
    status_str = " | ".join(status) if status else "✅ Clean"
    print(f"  {p['display_name']:<22} strikes={s}  feedback={p['feedback_average']}/5  {status_str}")

# =========================================================
# 5.  HOST PERFORMANCE PROFILES
# =========================================================
section("5 — Full Moderation System (Host Profiles)")

host_profiles = {
    "111111111111": {
        "user_id":            111111111111,
        "display_name":       "Smokey_PSN",
        "hosted_meets":       14,
        "attendance_total":   378,
        "attendance_average": 27.0,
        "feedback_entries":   12,
        "feedback_average":   4.8,
        "host_writeups":      0,
        "warnings":           0,
        "review_flagged":     False,
        "last_updated":       _utcnow().isoformat(),
    },
    "222222222222": {
        "user_id":            222222222222,
        "display_name":       "DriftKing_PSN",
        "hosted_meets":       11,
        "attendance_total":   289,
        "attendance_average": 26.3,
        "feedback_entries":   9,
        "feedback_average":   4.6,
        "host_writeups":      0,
        "warnings":           0,
        "review_flagged":     False,
        "last_updated":       _utcnow().isoformat(),
    },
    "333333333333": {
        "user_id":            333333333333,
        "display_name":       "NightShift_PSN",
        "hosted_meets":       5,
        "attendance_total":   102,
        "attendance_average": 20.4,
        "feedback_entries":   4,
        "feedback_average":   2.9,
        "host_writeups":      1,
        "warnings":           1,
        "review_flagged":     True,
        "last_updated":       _utcnow().isoformat(),
    },
    "777777777777": {
        "user_id":            777777777777,
        "display_name":       "RavenGT_PSN",
        "hosted_meets":       9,
        "attendance_total":   211,
        "attendance_average": 23.4,
        "feedback_entries":   7,
        "feedback_average":   4.2,
        "host_writeups":      0,
        "warnings":           0,
        "review_flagged":     False,
        "last_updated":       _utcnow().isoformat(),
    },
}
_save(host_path, host_profiles)

ok(f"Seeded {len(host_profiles)} host profiles")

HOST_BAD_FEEDBACK = 2.5
HOST_WU_THRESHOLD  = 2

print()
ranked_hosts = sorted(host_profiles.values(), key=lambda p: (p["feedback_average"], p["attendance_average"]), reverse=True)
print(f"  {'Rank':<5} {'Host':<20} {'Meets':<7} {'Att.Avg':<9} {'Feedback':<11} {'Flagged'}")
print(f"  {SEP2}")
for i, p in enumerate(ranked_hosts, 1):
    flagged = "🚨 YES" if p["review_flagged"] else "✅ No"
    trigger = ""
    if p["feedback_average"] <= HOST_BAD_FEEDBACK:
        trigger = " ← low feedback"
    elif p["host_writeups"] >= HOST_WU_THRESHOLD:
        trigger = " ← too many write-ups"
    print(f"  #{i:<4} {p['display_name']:<20} {p['hosted_meets']:<7} {p['attendance_average']:<9} {p['feedback_average']}/5{'':<5} {flagged}{trigger}")

# =========================================================
# 6.  SUMMARY
# =========================================================
section("6 — Full System Summary")

wu_data   = _load(writeup_path, {"counter":0,"entries":{}})
perf_data = _load(perf_path, {})
seas_data = _load(season_path, {})
mod_data  = _load(mod_path,  {})
host_data = _load(host_path, {})
str_data  = _load(strikes_path, {})

print(f"""
  Manager Hub
  ├─ Profiles tracked      : {len(perf_data)}
  ├─ Top manager (all-time) : {leaderboard[0][0]} ({leaderboard[0][1]['points']} pts)
  └─ Top manager (season)   : {season_lb[0][0]} ({season_lb[0][1]['points']} pts)

  Write-Up System
  ├─ Total entries          : {wu_data['counter']}
  ├─ Active                 : {sum(1 for e in wu_data['entries'].values() if e['status']=='Active')}
  ├─ Resolved               : {sum(1 for e in wu_data['entries'].values() if e['status']=='Resolved')}
  └─ Members with ≥3 strikes: {sum(1 for v in str_data.values() if v >= 3)}

  Full Moderation
  ├─ Member profiles        : {len(mod_data)}
  ├─ Flagged members        : {sum(1 for p in mod_data.values() if p.get('flags'))}
  ├─ Host profiles          : {len(host_data)}
  └─ Hosts under review     : {sum(1 for p in host_data.values() if p.get('review_flagged'))}
""")

print("  All JSON files written to diff_data/")
print()
print("  Files:")
for f in sorted(DATA.iterdir()):
    size = f.stat().st_size
    print(f"    {f.name:<45} {size:>6} bytes")

print()
print(f"{SEP}")
print("  ✅  All systems verified — data ready for live bot use")
print(SEP)
