#!/bin/bash
# GitHub Pages Verification Script
# For: case-evidence-r202518589

echo "🌐 GitHub Pages Status Check"
echo "============================="
echo "Generated: $(date)"
echo ""

# Repository URLs
GITHUB_REPO="https://github.com/ck999kk/case-evidence-r202518589"
PAGES_URL="https://ck999kk.github.io/case-evidence-r202518589"
API_URL="https://api.github.com/repos/ck999kk/case-evidence-r202518589/pages"

echo "🔗 Repository Information:"
echo "   GitHub: $GITHUB_REPO"
echo "   Pages: $PAGES_URL"
echo "   API: $API_URL"
echo ""

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "❌ curl not available - cannot check Pages status"
    exit 1
fi

# Check GitHub Pages API (requires authentication for private repos)
echo "📡 Checking GitHub Pages API..."
PAGES_STATUS=$(curl -s -w "HTTP_CODE:%{http_code}" "$API_URL" 2>/dev/null)
HTTP_CODE=$(echo "$PAGES_STATUS" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)

case $HTTP_CODE in
    200)
        echo "✅ GitHub Pages API accessible"
        echo "$PAGES_STATUS" | sed 's/HTTP_CODE:[0-9]*//' | python3 -m json.tool 2>/dev/null || echo "   Raw response received"
        ;;
    404)
        echo "⚠️  GitHub Pages not configured or repository not found"
        echo "   To enable Pages:"
        echo "   1. Go to: $GITHUB_REPO/settings/pages"
        echo "   2. Select 'Deploy from a branch'"
        echo "   3. Choose 'main' branch"
        echo "   4. Click 'Save'"
        ;;
    403)
        echo "🔒 Access denied (may be private repository)"
        ;;
    *)
        echo "❓ Unexpected response code: $HTTP_CODE"
        ;;
esac

echo ""

# Check if Pages site is accessible
echo "🌍 Testing Pages URL accessibility..."
PAGES_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -I "$PAGES_URL" 2>/dev/null)
PAGES_HTTP_CODE=$(echo "$PAGES_RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)

case $PAGES_HTTP_CODE in
    200)
        echo "✅ GitHub Pages site is live and accessible"
        echo "   URL: $PAGES_URL"
        ;;
    404)
        echo "⚠️  GitHub Pages site not found"
        echo "   This could mean:"
        echo "   - Pages is not enabled"
        echo "   - Site is still building (can take a few minutes)"
        echo "   - Repository is private and Pages requires Pro plan"
        ;;
    *)
        echo "❓ Pages response code: $PAGES_HTTP_CODE"
        ;;
esac

echo ""

# Test key evidence URLs
echo "🎯 Testing Evidence Access URLs..."
EVIDENCE_URLS=(
    "$PAGES_URL/All_Case_Parties_EML/"
    "$PAGES_URL/ATTACHMENT/"
    "$PAGES_URL/Additional_Documents/"
    "$PAGES_URL/README.md"
)

for url in "${EVIDENCE_URLS[@]}"; do
    echo -n "   Testing $(basename "$url")... "
    RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -I "$url" 2>/dev/null)
    CODE=$(echo "$RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    
    case $CODE in
        200) echo "✅" ;;
        404) echo "❌ Not Found" ;;
        403) echo "🔒 Forbidden" ;;
        *) echo "❓ ($CODE)" ;;
    esac
done

echo ""

# Setup instructions
echo "📋 GitHub Pages Setup Instructions:"
echo "======================================"
if [ "$PAGES_HTTP_CODE" != "200" ]; then
    echo "⚠️  Pages not accessible - Manual setup required:"
    echo ""
    echo "1. 🌐 Go to GitHub repository settings:"
    echo "   $GITHUB_REPO/settings/pages"
    echo ""
    echo "2. 📄 Configure Pages source:"
    echo "   - Source: 'Deploy from a branch'"
    echo "   - Branch: 'main'"
    echo "   - Folder: '/ (root)'"
    echo ""
    echo "3. 💾 Click 'Save' and wait 2-3 minutes for deployment"
    echo ""
    echo "4. ✅ Verify access at:"
    echo "   $PAGES_URL"
else
    echo "✅ GitHub Pages is properly configured and accessible!"
    echo ""
    echo "🎯 Direct Evidence Access URLs:"
    echo "   Email Communications: $PAGES_URL/All_Case_Parties_EML/"
    echo "   Evidence Attachments: $PAGES_URL/ATTACHMENT/"
    echo "   Supporting Documents: $PAGES_URL/Additional_Documents/"
    echo "   Repository Information: $PAGES_URL/README.md"
fi

echo ""
echo "🔄 Run this script again to recheck Pages status"