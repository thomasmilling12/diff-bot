#!/bin/bash
# DIFF Bot deploy script
# Run this INSTEAD of the manual git/restart commands.
# It backs up live data, pulls the latest code, then restores data.

set -e
cd ~/diff-bot

echo "[deploy] Backing up live data..."
cp -r diff_data/ /tmp/diff_data_backup/

echo "[deploy] Pulling latest code..."
git fetch origin
git reset --hard origin/main

echo "[deploy] Restoring live data..."
cp -r /tmp/diff_data_backup/. diff_data/
rm -rf /tmp/diff_data_backup

echo "[deploy] Restarting bot..."
sudo systemctl restart different-meets-v2

echo "[deploy] Done."
