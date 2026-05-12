#!/bin/bash
# DIFF Bot deploy script
# Run this INSTEAD of the manual git/restart commands.
# It backs up live data, pulls the latest code, then restores data.

set -e
cd ~/diff-bot

echo "[deploy] Backing up live data..."
cp -r diff_data/ /tmp/diff_data_backup/
cp diff_data.json /tmp/diff_data_json_backup.json 2>/dev/null && echo "  diff_data.json backed up" || echo "  diff_data.json not found"

echo "[deploy] Pulling latest code..."
git fetch origin
git reset --hard origin/main

echo "[deploy] Restoring live data..."
cp -r /tmp/diff_data_backup/. diff_data/
rm -rf /tmp/diff_data_backup
[ -f /tmp/diff_data_json_backup.json ] && cp /tmp/diff_data_json_backup.json diff_data.json && echo "  diff_data.json restored"

echo "[deploy] Restarting bot..."
sudo systemctl restart different-meets-v2

echo "[deploy] Done."
