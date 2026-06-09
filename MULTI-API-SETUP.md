# SmartBot Cache - Complete Multi-API Setup Guide

## 🚀 ตั้งค่าทั้ง 3 APIs (Gemini + DeepSeek + Claude)

### ⚡ Quick Setup (1 นาที)

```bash
chmod +x setup-multi-api.sh
./setup-multi-api.sh
```

ระบบจะขอให้วาง API Keys ทั้ง 3 ตัวแล้วเริ่มเซิร์ฟเวอร์ทันที

---

## 📋 Manual Setup (ขั้นตอนละเอียด)

### 1️⃣ ตั้ง GEMINI API (ฟรี)

```bash
# ขั้นที่ 1: ไปที่ https://aistudio.google.com/app/apikeys
# ขั้นที่ 2: Click "Create API Key"
# ขั้นที่ 3: Copy the key

# ขั้นที่ 4: Paste into .env
GEMINI_API_KEY=AIzaSyD...your_key_here...
```

✅ **สิทธิ์:**
- 1,500 requests/day (ฟรี)
- ไม่จำเป็นต้องจ่ายเงิน
- เหมาะสำหรับ dev/test

---

### 2️⃣ ตั้ง DEEPSEEK API (งบประมาณต่ำ)

```bash
# ขั้นที่ 1: ไปที่ https://platform.deepseek.com/api_keys
# ขั้นที่ 2: Login หรือ Sign up
# ขั้นที่ 3: Generate new API key
# ขั้นที่ 4: Copy the key

# ขั้นที่ 5: Add to .env
DEEPSEEK_API_KEY=sk-...your_key_here...
```

✅ **สิทธิ์:**
- $0.14 per 1M input tokens
- $0.28 per 1M output tokens
- ประมาณ $84/month สำหรับ 10,000 queries/day

---

### 3️⃣ ตั้ง CLAUDE API (ประสิทธิภาพสูง)

```bash
# ขั้นที่ 1: ไปที่ https://console.anthropic.com/account/keys
# ขั้นที่ 2: Create new API key
# ขั้นที่ 3: Copy the key

# ขั้นที่ 4: Add to .env
ANTHROPIC_API_KEY=sk-ant-...your_key_here...
```

✅ **สิทธิ์:**
- $3.00 per 1M input tokens
- $15.00 per 1M output tokens
- Premium quality fallback

---

## 🔧 Configuration (.env)

```env
# === MUST HAVE (ต้องตั้ง) ===
GEMINI_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# === OPTIONAL (ตั้งตามต้องการ) ===
PORT=3000                    # Server port
CACHE_TTL_MS=3600000        # Cache lifetime (1 hour)
MAX_CACHE=10000             # Max cache entries
SEM_THRESH=0.72             # Semantic similarity
MAX_BODY_KB=32              # Max request size
RATE_LIMIT=300              # Requests per minute
MODEL_TIMEOUT=15000         # Model timeout (15s)
LOG_LEVEL=info              # Logging: info/debug/error
```

---

## 🎯 Smart Routing Logic

### ระบบจะเลือก API แบบไหน?

```
Query Analysis:
├─ Word Count: count_words(query)
└─ Complexity: check for keywords (analyze, compare, etc)

Simple Question (≤12 words)?
├─ Step 1: Try GEMINI (FREE) ✅
│  └─ Success? Return response
│  └─ Fail? Continue...
├─ Step 2: Try DEEPSEEK ($0.28/M)
│  └─ Success? Return response
│  └─ Fail? Continue...
└─ Step 3: Use CLAUDE ($15/M)
   └─ Must succeed (premium quality)

Complex Question (>12 words or complex)?
├─ Step 1: Try DEEPSEEK ($0.28/M) ✅
│  └─ Success? Return response
│  └─ Fail? Continue...
└─ Step 2: Use CLAUDE ($15/M)
   └─ Must succeed (premium quality)

Analysis/Coding/Writing?
└─ Direct to CLAUDE ($15/M) ✅ Best quality
```

---

## 🚀 Running the Server

### Option 1: Interactive Setup (Recommended)
```bash
chmod +x setup-multi-api.sh
./setup-multi-api.sh
```

### Option 2: Manual Start
```bash
npm install
node server.js
```

### Option 3: Docker
```bash
docker build -t smartbot .
docker run -p 3000:3000 \
  -e GEMINI_API_KEY=AIza... \
  -e DEEPSEEK_API_KEY=sk-... \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  smartbot
```

---

## ✅ Testing the Setup

### Health Check
```bash
curl http://localhost:3000/health

# Expected Response:
{
  "status": "ok",
  "version": "4.0.0",
  "models": {
    "gemini": "✅ ready",
    "deepseek": "✅ ready",
    "claude": "✅ ready"
  }
}
```

### Test Simple Query
```bash
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?"}'

# Response will come from GEMINI (FREE) if available
```

### Test Complex Query
```bash
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze the differences between machine learning and deep learning and explain their applications"}'

# Response will come from DEEPSEEK or CLAUDE (smart routing)
```

### View Statistics
```bash
curl http://localhost:3000/stats

# Shows which model was used, cache hit rate, cost saved, etc.
```

---

## 💰 Cost Breakdown Example

### Scenario: 10,000 queries/day

**Without SmartBot Cache:**
```
Direct API calls:
- All to GEMINI (1,500/day limit): BLOCKED ❌
- All to DEEPSEEK: 300k × $0.28/M = $84/month
- All to CLAUDE: 300k × $15/M = $4,500/month
- Mixed average: ~$1,810/month
```

**With SmartBot Cache (70% cache hit):**
```
- 210,000 cache hits (FREE) ✅
- 30,000 GEMINI calls (FREE) ✅
- 45,000 DEEPSEEK calls: $12.60/month
- 15,000 CLAUDE calls: $225/month
- Total: ~$238/month ✅

SAVINGS: $1,572/month (87% reduction!)
```

---

## 🔄 Model Health Monitoring

Server automatically monitors model health:

```
Each model has:
├─ Health status (ok/down)
├─ Failure count
└─ Auto-recovery (5 min after 3 failures)

If model fails 3 times:
├─ Model marked as DOWN ⚠️
├─ Fallback to next model
└─ Auto-recovery after 300 seconds ✅
```

Check model status:
```bash
curl http://localhost:3000/health | jq .models
```

---

## 📊 API Comparison

| Feature | GEMINI | DEEPSEEK | CLAUDE |
|---------|--------|----------|--------|
| Cost | FREE | $0.28/M | $15/M |
| Speed | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Quality | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Best For | Simple Q&A | Analysis | Complex tasks |
| Daily Limit | 1,500 | ∞ | ∞ |
| Fallback | Step 1 | Step 2 | Step 3 |

---

## 🎯 Recommendations

✅ **For Development:** Use GEMINI only
✅ **For Small Scale:** GEMINI + DEEPSEEK  
✅ **For Production:** All 3 (with smart fallback)
✅ **For Premium Quality:** Add CLAUDE fallback

---

## 🐛 Troubleshooting

### "No AI model available"
→ ตั้ง API Key อย่างน้อย 1 ตัวใน `.env` ให้ครบ

### Model keeps failing
→ ตรวจสอบว่า API Key ถูกต้อง:
```bash
curl http://localhost:3000/health
```

### High latency
→ ตรวจสอบ cache hit rate:
```bash
curl http://localhost:3000/stats
```

### Rate limit exceeded
→ เพิ่ม `RATE_LIMIT` ใน `.env` หรือรอ 60 วินาที

---

## 📚 Resources

- 🔗 Gemini: https://aistudio.google.com
- 🔗 DeepSeek: https://platform.deepseek.com
- 🔗 Anthropic: https://console.anthropic.com
- 📖 SmartBot Docs: See SETUP.md

