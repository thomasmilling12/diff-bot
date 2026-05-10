#!/bin/bash
# Run this ONCE on the Pi to stop git from resetting live data files.
# After this, combined with the backup-restore deploy command, data is always preserved.
#
# Usage:  bash ~/diff-bot/scripts/untrack_data.sh

cd ~/diff-bot

echo "Removing live data files from git index (files stay on disk)..."

git rm --cached \
  diff_data/*.json \
  diff_data/*.db \
  diff_data/*.sqlite3 \
  2>/dev/null || true

echo ""
echo "Done. Data files are no longer tracked by git on this Pi."
echo "Continue using the backup-restore deploy command:"
echo ""
echo "  cd ~/diff-bot && git fetch origin && cp -r diff_data /tmp/diff_data_bak && git reset --hard origin/main && cp -r /tmp/diff_data_bak/. diff_data/ && sudo systemctl restart different-meets-v2"
echo ""
