#!/bin/bash
# Run this ONCE on the Pi to permanently stop git from tracking live data files.
# After running this, `git reset --hard` will never wipe your bot's data again.
#
# Usage:  bash ~/diff-bot/scripts/untrack_data.sh

set -e
cd ~/diff-bot

echo "Removing live data files from git tracking (files stay on disk)..."

git rm --cached \
  diff_data/*.json \
  diff_data/*.db \
  diff_data/*.sqlite3 \
  2>/dev/null || true

echo "Committing the untrack change..."
git add .gitignore
git commit -m "chore: stop tracking live data files (already in .gitignore)" || echo "(nothing to commit — already untracked)"

echo "Pushing to GitHub..."
git push origin main

echo ""
echo "Done! Live data files will no longer be touched by future git reset --hard deploys."
