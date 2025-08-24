#!/bin/bash
# Repository Monitoring System
# For: case-evidence-r202518589

echo "🔍 Repository Monitoring System"
echo "==============================="
echo "Started: $(date)"
echo ""

# Configuration
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_LOG="$REPO_DIR/monitoring.log"
GITHUB_REPO="https://github.com/ck999kk/case-evidence-r202518589"
PAGES_URL="https://ck999kk.github.io/case-evidence-r202518589"

# Create monitoring log entry
log_entry() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MONITOR_LOG"
}

log_entry "=== Repository Monitoring Started ==="

cd "$REPO_DIR"

# 1. Repository Health Check
echo "🏥 Repository Health Check"
echo "=========================="

# Check git status
if [ -d ".git" ]; then
    log_entry "✅ Git repository structure intact"
    
    # Check for uncommitted changes
    CHANGES=$(git status --porcelain | wc -l | tr -d ' ')
    if [ "$CHANGES" -eq 0 ]; then
        log_entry "✅ Working tree clean"
        echo "✅ Working tree clean"
    else
        log_entry "⚠️  Uncommitted changes detected: $CHANGES files"
        echo "⚠️  Uncommitted changes detected: $CHANGES files"
        git status --short
    fi
    
    # Check remote connectivity
    if git ls-remote origin &>/dev/null; then
        log_entry "✅ Remote connectivity OK"
        echo "✅ Remote connectivity OK"
    else
        log_entry "❌ Remote connectivity failed"
        echo "❌ Remote connectivity failed"
    fi
    
else
    log_entry "❌ Git repository not found"
    echo "❌ Git repository not found"
fi

echo ""

# 2. File Integrity Check
echo "🔐 File Integrity Monitoring"
echo "============================="

# Count evidence files
EMAIL_COUNT=$(find All_Case_Parties_EML -name "*.eml" 2>/dev/null | wc -l | tr -d ' ')
ATTACHMENT_COUNT=$(find ATTACHMENT -type f 2>/dev/null | wc -l | tr -d ' ')
ADDITIONAL_COUNT=$(find Additional_Documents -type f 2>/dev/null | wc -l | tr -d ' ')
TOTAL_COUNT=$((EMAIL_COUNT + ATTACHMENT_COUNT + ADDITIONAL_COUNT))

log_entry "📊 File inventory: Total=$TOTAL_COUNT, Emails=$EMAIL_COUNT, Attachments=$ATTACHMENT_COUNT, Additional=$ADDITIONAL_COUNT"
echo "📊 File Inventory:"
echo "   Total Evidence: $TOTAL_COUNT files"
echo "   Email Files: $EMAIL_COUNT"
echo "   Attachments: $ATTACHMENT_COUNT"
echo "   Additional: $ADDITIONAL_COUNT"

# Check for missing critical files
CRITICAL_FILES=(
    "README.md"
    "DEPLOYMENT_INSTRUCTIONS.md" 
    "GOVERNMENT_ACCESS_GUIDE.md"
    "All_Case_Parties.mbox"
)

echo ""
echo "🎯 Critical Files Check:"
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
        log_entry "✅ Critical file present: $file"
    else
        echo "   ❌ $file"
        log_entry "❌ Critical file missing: $file"
    fi
done

echo ""

# 3. GitHub Pages Monitoring
echo "🌐 GitHub Pages Monitoring"
echo "==========================="

if command -v curl &> /dev/null; then
    # Test main Pages URL
    PAGES_STATUS=$(curl -s -w "HTTP_CODE:%{http_code}" -I "$PAGES_URL" 2>/dev/null)
    PAGES_CODE=$(echo "$PAGES_STATUS" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    
    case $PAGES_CODE in
        200)
            echo "✅ GitHub Pages accessible"
            log_entry "✅ GitHub Pages accessible ($PAGES_CODE)"
            ;;
        404)
            echo "❌ GitHub Pages not found"
            log_entry "❌ GitHub Pages not found ($PAGES_CODE)"
            ;;
        *)
            echo "⚠️  GitHub Pages response: $PAGES_CODE"
            log_entry "⚠️  GitHub Pages response: $PAGES_CODE"
            ;;
    esac
    
    # Test evidence URLs
    EVIDENCE_URLS=(
        "$PAGES_URL/All_Case_Parties_EML/"
        "$PAGES_URL/ATTACHMENT/" 
        "$PAGES_URL/Additional_Documents/"
    )
    
    echo ""
    echo "🎯 Evidence Access Test:"
    for url in "${EVIDENCE_URLS[@]}"; do
        RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -I "$url" 2>/dev/null)
        CODE=$(echo "$RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
        CATEGORY=$(basename "$url")
        
        case $CODE in
            200) 
                echo "   ✅ $CATEGORY"
                log_entry "✅ Evidence access OK: $CATEGORY ($CODE)"
                ;;
            404) 
                echo "   ❌ $CATEGORY" 
                log_entry "❌ Evidence access failed: $CATEGORY ($CODE)"
                ;;
            *) 
                echo "   ⚠️  $CATEGORY ($CODE)"
                log_entry "⚠️  Evidence access warning: $CATEGORY ($CODE)"
                ;;
        esac
    done
    
else
    echo "⚠️  curl not available - skipping web checks"
    log_entry "⚠️  curl not available for web monitoring"
fi

echo ""

# 4. System Resources
echo "💻 System Resources"
echo "==================="

REPO_SIZE=$(du -sh . | cut -f1)
DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}')

echo "📦 Repository size: $REPO_SIZE"
echo "💾 Disk usage: $DISK_USAGE"

log_entry "📊 System: Repository=$REPO_SIZE, Disk=$DISK_USAGE"

echo ""

# 5. Generate Summary Report
echo "📋 Monitoring Summary"
echo "===================="

# Count log entries by type
ERRORS=$(grep "❌" "$MONITOR_LOG" | tail -20 | wc -l | tr -d ' ')
WARNINGS=$(grep "⚠️" "$MONITOR_LOG" | tail -20 | wc -l | tr -d ' ')
SUCCESS=$(grep "✅" "$MONITOR_LOG" | tail -20 | wc -l | tr -d ' ')

echo "📊 Status Summary (last 20 entries):"
echo "   ✅ Success: $SUCCESS"
echo "   ⚠️  Warnings: $WARNINGS" 
echo "   ❌ Errors: $ERRORS"

if [ "$ERRORS" -eq 0 ]; then
    OVERALL_STATUS="HEALTHY"
    log_entry "🟢 Overall status: HEALTHY"
elif [ "$ERRORS" -le 2 ]; then
    OVERALL_STATUS="WARNING"
    log_entry "🟡 Overall status: WARNING"
else
    OVERALL_STATUS="CRITICAL"
    log_entry "🔴 Overall status: CRITICAL"
fi

echo ""
echo "🎯 Overall Status: $OVERALL_STATUS"
echo ""

# 6. Next Steps
echo "📋 Recommended Actions:"
if [ "$ERRORS" -gt 0 ]; then
    echo "   🔧 Review errors in monitoring.log"
fi
if [ "$WARNINGS" -gt 0 ]; then
    echo "   ⚠️  Check warnings for potential issues"
fi
if [ "$PAGES_CODE" != "200" ]; then
    echo "   🌐 Enable GitHub Pages if not accessible"
fi
echo "   🔄 Run monitoring regularly to track changes"
echo "   📊 Review monitoring.log for historical data"

log_entry "=== Repository Monitoring Completed: $OVERALL_STATUS ==="

echo ""
echo "✅ Monitoring complete! Check monitoring.log for full history."