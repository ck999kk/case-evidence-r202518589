#!/bin/bash
# Repository Sync Script - Automated GitHub synchronization
# For: case-evidence-r202518589

echo "🔄 Repository Sync Starting..."
echo "==============================="

# Get current directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check remote connection
echo "📡 Checking remote connection..."
git remote -v

# Fetch latest changes
echo ""
echo "📥 Fetching latest changes..."
if git fetch origin; then
    echo "✅ Fetch successful"
else
    echo "❌ Fetch failed"
    exit 1
fi

# Check for local changes
echo ""
echo "🔍 Checking for local changes..."
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Local changes detected:"
    git status --short
    
    read -p "Commit local changes? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "💾 Committing local changes..."
        git add .
        git commit -m "Auto-sync: Update evidence repository

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
    else
        echo "⚠️  Skipping commit - local changes remain"
    fi
else
    echo "✅ No local changes"
fi

# Check if remote has updates
echo ""
echo "🔄 Checking for remote updates..."
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "📥 Remote updates available"
    
    # Pull changes
    echo "⬇️  Pulling remote changes..."
    if git pull origin main; then
        echo "✅ Pull successful"
    else
        echo "❌ Pull failed - may need manual intervention"
        exit 1
    fi
else
    echo "✅ Repository up to date"
fi

# Push any local commits
echo ""
echo "⬆️  Pushing to remote..."
if git push origin main; then
    echo "✅ Push successful"
else
    echo "⚠️  Push failed or nothing to push"
fi

# Final status
echo ""
echo "📊 Final Repository Status:"
echo "============================="
git status
echo ""
echo "🔗 Repository URL: https://github.com/ck999kk/case-evidence-r202518589"
echo "🌐 GitHub Pages: https://ck999kk.github.io/case-evidence-r202518589"
echo ""
echo "✅ Sync complete!"