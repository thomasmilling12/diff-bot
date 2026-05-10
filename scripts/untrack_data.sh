#!/bin/bash
# Run this ONCE on the Pi to permanently stop git from tracking live data files.
# After this, plain `git reset --hard origin/main` is safe — data files are never touched.
#
# Usage:  bash ~/diff-bot/scripts/untrack_data.sh

set -e
cd ~/diff-bot

echo "Removing live data files from git index (files stay on disk)..."

git rm -r --cached diff_data/ 2>/dev/null || true

echo "Committing removal from index..."
git add .gitignore scripts/untrack_data.sh
git commit -m "Stop tracking live data files permanently" --allow-empty

echo "Pushing to origin so Replit also stops re-committing them..."
git push origin main

echo ""
echo "Done! Live data files are now permanently untracked on origin."
echo "You can now use the simple deploy command (no backup/restore needed):"
echo ""
echo "  cd ~/diff-bot && git fetch origin && git reset --hard origin/main && sudo systemctl restart different-meets-v2"
echo ""
