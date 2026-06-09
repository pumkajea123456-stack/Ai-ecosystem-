#!/bin/bash
# SmartBot Cache Multi-API Setup Script
# ตั้งค่า Gemini + DeepSeek + Claude พร้อมใช้งาน

set -e

clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║   SmartBot Cache v4.0 - Multi-API Setup               ║"
echo "║   (Gemini + DeepSeek + Claude)                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check Node.js
echo "📋 Checking system requirements..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install from https://nodejs.org (v18+)"
    exit 1
fi
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js 18+ required. Current: $(node -v)"
    exit 1
fi
echo "✅ Node.js $(node -v)"
echo ""

# Step 2: Install dependencies
echo "📦 Installing dependencies..."
if [ ! -d "node_modules" ]; then
    npm install 2>/dev/null || true
fi
echo "✅ Dependencies ready"
echo ""

# Step 3: API Keys Configuration
echo "🔑 API Keys Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Gemini
echo "1️⃣  GEMINI (ฟรี - 1,500 requests/วัน)"
echo "   📝 ไปที่: https://aistudio.google.com/app/apikeys"
echo "   👉 Copy API Key แล้ววาง:"
read -p "   GEMINI_API_KEY: " GEMINI_KEY

# DeepSeek
echo ""
echo "2️⃣  DEEPSEEK ($0.28/M tokens)"
echo "   📝 ไปที่: https://platform.deepseek.com/api_keys"
echo "   👉 Copy API Key แล้ววาง:"
read -p "   DEEPSEEK_API_KEY: " DEEPSEEK_KEY

# Claude
echo ""
echo "3️⃣  CLAUDE ($3/M tokens)"
echo "   📝 ไปที่: https://console.anthropic.com/account/keys"
echo "   👉 Copy API Key แล้ววาง:"
read -p "   ANTHROPIC_API_KEY: " CLAUDE_KEY

echo ""
echo "🔄 Updating .env file..."

# Create/Update .env with all keys
cat > .env << EOF
# SmartBot Cache v4.0 — Multi-API Configuration
# Updated: $(date)

# ── API Keys (ทั้ง 3 ตัว - Multi-Model Fallback) ─────────────────
GEMINI_API_KEY=$GEMINI_KEY
DEEPSEEK_API_KEY=$DEEPSEEK_KEY
ANTHROPIC_API_KEY=$CLAUDE_KEY

# ── Server ────────────────────────────────────────────────────────
PORT=3000

# ── Cache Configuration ───────────────────────────────────────────
CACHE_TTL_MS=3600000
MAX_CACHE=10000
SEM_THRESH=0.72

# ── Security ──────────────────────────────────────────────────────
MAX_BODY_KB=32
RATE_LIMIT=300
RATE_WINDOW=60000

# ── Performance ───────────────────────────────────────────────────
MODEL_TIMEOUT=15000
LOG_LEVEL=info
EOF

echo "✅ .env file updated with all 3 API keys"
echo ""

# Step 4: Start server
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Starting SmartBot Cache Server..."
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Server Information:                                   ║"
echo "║  ✅ URL: http://localhost:3000                         ║"
echo "║  ✅ Models: Gemini | DeepSeek | Claude                ║"
echo "║  ✅ Cache: Smart fallback routing enabled             ║"
echo "║                                                        ║"
echo "║  Quick Test:                                           ║"
echo "║  $ curl http://localhost:3000/health                  ║"
echo "║  $ curl http://localhost:3000/stats                   ║"
echo "║                                                        ║"
echo "║  Ask Question:                                         ║"
echo "║  $ curl -X POST http://localhost:3000/query \\        ║"
echo "║    -H 'Content-Type: application/json' \\             ║"
echo "║    -d '{\"query\": \"What is AI?\"}'                   ║"
echo "║                                                        ║"
echo "║  Stop Server: Press Ctrl+C                            ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Load environment and start
source .env 2>/dev/null || true
export $(cat .env | grep -v '^#' | xargs)

node server.js
