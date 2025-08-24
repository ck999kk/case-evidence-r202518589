#!/bin/bash
# Repository Status Script - Health check and information
# For: case-evidence-r202518589

echo "📊 Repository Health Check"
echo "=========================="
echo "Generated: $(date)"
echo ""

# Get current directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Repository Information
echo "🏛️  Repository Information:"
echo "   Location: $REPO_DIR"
echo "   Remote: $(git remote get-url origin 2>/dev/null || echo 'Not configured')"
echo "   Branch: $(git branch --show-current 2>/dev/null || echo 'Not a git repo')"
echo ""

# Git Status
echo "📋 Git Status:"
if [ -d ".git" ]; then
    git status
    echo ""
    
    # Commit History
    echo "📚 Recent Commits:"
    git log --oneline -5
    echo ""
    
    # File Count
    echo "📁 Repository Contents:"
    echo "   Total files: $(git ls-files | wc -l | tr -d ' ')"
    echo "   Total size: $(du -sh . | cut -f1)"
    echo ""
    
    # Branch Tracking
    echo "🌿 Branch Information:"
    git branch -vv
    echo ""
    
else
    echo "❌ Not a git repository"
fi

# Repository URLs
echo "🔗 Access URLs:"
echo "   GitHub Repository: https://github.com/ck999kk/case-evidence-r202518589"
echo "   GitHub Pages: https://ck999kk.github.io/case-evidence-r202518589"
echo "   Raw Files: https://raw.githubusercontent.com/ck999kk/case-evidence-r202518589/main/"
echo ""

# Evidence Categories
echo "📂 Evidence Categories:"
if [ -d "All_Case_Parties_EML" ]; then
    echo "   ✅ Email Evidence: $(ls All_Case_Parties_EML/ | wc -l | tr -d ' ') files"
fi
if [ -d "ATTACHMENT" ]; then
    echo "   ✅ Attachments: $(find ATTACHMENT -type f | wc -l | tr -d ' ') files"  
fi
if [ -d "Additional_Documents" ]; then
    echo "   ✅ Additional Documents: $(find Additional_Documents -type f | wc -l | tr -d ' ') files"
fi
echo ""

# Quick Access Links
echo "🎯 Quick Access (Government Agencies):"
echo "   Email Communications: https://ck999kk.github.io/case-evidence-r202518589/All_Case_Parties_EML/"
echo "   Evidence Attachments: https://ck999kk.github.io/case-evidence-r202518589/ATTACHMENT/"
echo "   Supporting Documents: https://ck999kk.github.io/case-evidence-r202518589/Additional_Documents/"
echo ""

# System Health
echo "🔧 System Health:"
echo "   Working tree: $(git status --porcelain | wc -l | tr -d ' ') changes"
echo "   Last sync: $(git log -1 --format=%cd --date=relative)"
echo "   Repository size: $(du -sh . | cut -f1)"
echo ""

echo "✅ Health check complete!"