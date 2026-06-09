#!/bin/bash
# SmartBot Cache - Complete Startup & Testing Script
# เริ่มการทำงาน - Start Everything

set -e

clear
cat << 'EOF'
╔════════════════════════════════════════════════════════╗
║   SmartBot Cache v4.0.0 - Complete Startup            ║
║   ตั้งค่าและเริ่มการทำงาน - Setup & Start             ║
╚════════════════════════════════════════════════════════╝

EOF

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================
# STEP 1: Check System Requirements
# ============================================================
echo -e "${BLUE}STEP 1: Checking System Requirements${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Node.js
echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    echo "Install from: https://nodejs.org (v18+)"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}❌ Node.js 18+ required. Current: $(node -v)${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js $(node -v)${NC}"

# Check npm
echo "Checking npm..."
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ npm $(npm -v)${NC}"

echo ""

# ============================================================
# STEP 2: Install Dependencies
# ============================================================
echo -e "${BLUE}STEP 2: Installing Dependencies${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install 2>&1 | tail -5
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

echo ""

# ============================================================
# STEP 3: Check/Setup API Keys
# ============================================================
echo -e "${BLUE}STEP 3: API Keys Configuration${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f ".env" ] && grep -q "GEMINI_API_KEY=" .env; then
    echo -e "${GREEN}✅ Found existing .env configuration${NC}"
    echo ""
    echo "Current API Keys:"
    grep "API_KEY=" .env | sed 's/=.*/=***/' || echo "No keys set"
    echo ""
    read -p "Use existing config? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo ""
        echo "Enter new API Keys..."
        read -p "GEMINI_API_KEY (free tier): " GEMINI_KEY
        read -p "DEEPSEEK_API_KEY (optional): " DEEPSEEK_KEY
        read -p "ANTHROPIC_API_KEY (optional): " CLAUDE_KEY
        
        cat > .env << EOF
# SmartBot Cache v4.0 — Multi-API Configuration
# Updated: $(date)

GEMINI_API_KEY=$GEMINI_KEY
DEEPSEEK_API_KEY=$DEEPSEEK_KEY
ANTHROPIC_API_KEY=$CLAUDE_KEY

PORT=3000
CACHE_TTL_MS=3600000
MAX_CACHE=10000
SEM_THRESH=0.72
MAX_BODY_KB=32
RATE_LIMIT=300
RATE_WINDOW=60000
MODEL_TIMEOUT=15000
LOG_LEVEL=info
EOF
        echo -e "${GREEN}✅ .env updated${NC}"
    fi
else
    echo "Creating new .env configuration..."
    echo ""
    
    echo -e "${YELLOW}Setup 3 API Providers (at least 1 required):${NC}"
    echo ""
    
    echo "1️⃣  GEMINI (ฟรี - 1,500 requests/day) ← RECOMMENDED"
    echo "   Sign up: https://aistudio.google.com/app/apikeys"
    read -p "   GEMINI_API_KEY: " GEMINI_KEY
    
    echo ""
    echo "2️⃣  DEEPSEEK ($0.28/M tokens) - optional"
    echo "   Sign up: https://platform.deepseek.com/api_keys"
    read -p "   DEEPSEEK_API_KEY: " DEEPSEEK_KEY
    
    echo ""
    echo "3️⃣  CLAUDE ($3/M tokens) - optional"
    echo "   Sign up: https://console.anthropic.com/account/keys"
    read -p "   ANTHROPIC_API_KEY: " CLAUDE_KEY
    
    cat > .env << EOF
# SmartBot Cache v4.0 — Multi-API Configuration
# Created: $(date)

GEMINI_API_KEY=$GEMINI_KEY
DEEPSEEK_API_KEY=$DEEPSEEK_KEY
ANTHROPIC_API_KEY=$CLAUDE_KEY

PORT=3000
CACHE_TTL_MS=3600000
MAX_CACHE=10000
SEM_THRESH=0.72
MAX_BODY_KB=32
RATE_LIMIT=300
RATE_WINDOW=60000
MODEL_TIMEOUT=15000
LOG_LEVEL=info
EOF
    echo -e "${GREEN}✅ .env created${NC}"
fi

echo ""

# ============================================================
# STEP 4: Verify Configuration
# ============================================================
echo -e "${BLUE}STEP 4: Verifying Configuration${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

source .env 2>/dev/null || true

GEMINI_OK=""
DEEPSEEK_OK=""
CLAUDE_OK=""

[ -n "$GEMINI_API_KEY" ] && GEMINI_OK="✅" || GEMINI_OK="❌"
[ -n "$DEEPSEEK_API_KEY" ] && DEEPSEEK_OK="✅" || DEEPSEEK_OK="❌"
[ -n "$ANTHROPIC_API_KEY" ] && CLAUDE_OK="✅" || CLAUDE_OK="❌"

echo "API Keys Status:"
echo "  $GEMINI_OK Gemini"
echo "  $DEEPSEEK_OK DeepSeek"
echo "  $CLAUDE_OK Claude"
echo ""

if [[ $GEMINI_OK != "✅" ]] && [[ $DEEPSEEK_OK != "✅" ]] && [[ $CLAUDE_OK != "✅" ]]; then
    echo -e "${RED}❌ At least 1 API Key required!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration verified - Ready to start!${NC}"
echo ""

# ============================================================
# STEP 5: Start Server
# ============================================================
echo -e "${BLUE}STEP 5: Starting Server${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Loading environment variables..."
export $(cat .env | grep -v '^#' | xargs)

PORT=${PORT:-3000}

sleep 1

cat << 'EOF'

╔════════════════════════════════════════════════════════╗
║                                                        ║
║         🚀 SmartBot Cache Server Started! 🚀          ║
║                                                        ║
║  ✅ Version: v4.0.0                                   ║
║  ✅ URL: http://localhost:3000                        ║
║  ✅ Models: Gemini | DeepSeek | Claude                ║
║  ✅ Cache: Smart Multi-Model Routing                  ║
║  ✅ Status: Running & Ready                           ║
║                                                        ║
║  📊 Quick Test Commands (Open new terminal):          ║
║                                                        ║
║  Health Check:                                        ║
║  $ curl http://localhost:3000/health                 ║
║                                                        ║
║  Statistics:                                          ║
║  $ curl http://localhost:3000/stats                  ║
║                                                        ║
║  Send Query (Test #1 - Cache Miss):                   ║
║  $ curl -X POST http://localhost:3000/query \        ║
║    -H "Content-Type: application/json" \             ║
║    -d '{"query": "What is AI?"}'                      ║
║                                                        ║
║  Repeat Query (Test #2 - Cache Hit - ⚡FAST):         ║
║  $ curl -X POST http://localhost:3000/query \        ║
║    -H "Content-Type: application/json" \             ║
║    -d '{"query": "What is AI?"}'                      ║
║                                                        ║
║  View Cache Info:                                     ║
║  $ curl http://localhost:3000/cache/info             ║
║                                                        ║
║  📚 More Tests: See TESTING-GUIDE.md                  ║
║  📖 Integration: See INTEGRATION-GUIDE.md             ║
║  🐛 Troubleshooting: See SETUP.md                     ║
║                                                        ║
║  🛑 To Stop: Press Ctrl+C                             ║
║                                                        ║
╚════════════════════════════════════════════════════════╝

EOF

sleep 2

# Start server
node server.js
