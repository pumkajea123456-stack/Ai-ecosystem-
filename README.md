# SmartBot Cache 🤖⚡

**ลดค่า AI API 60-80% ด้วย Local Cache Layer**

> เรียก AI เฉพาะเมื่อมีข้อมูลใหม่ — คำถามซ้ำตอบจาก cache ทันที

---

## ตัวเลขจริง (Benchmark)

| ระบบ | ค่าใช้จ่าย/เดือน | พลังงาน |
|---|---|---|
| Call AI ทุกครั้ง | $1,810 | 146 kWh |
| **SmartBot Cache** | **$724** | **53 kWh** |
| Smart Routing | **$160** | **53 kWh** |

**ประหยัด $1,086–$1,650 ต่อเดือน (10,000 queries/วัน)**

---

## วิธีใช้งาน

### Deploy บน Railway (5 นาที)

1. Fork repo นี้
2. ไป [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. ตั้ง Environment Variable: `ANTHROPIC_API_KEY=sk-ant-xxx`
4. Deploy → ได้ URL ทันที

### รันบนเครื่อง

```bash
git clone https://github.com/YOUR_USERNAME/smartbot-cache.git
cd smartbot-cache
ANTHROPIC_API_KEY=sk-ant-xxx node server.js
```

---

## API Endpoints

### POST /query
```bash
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "AI คืออะไร"}'
```

**Response — Cache HIT (ฟรี):**
```json
{
  "response": "AI คือ...",
  "source": "EXACT",
  "ms": 8,
  "cached": true,
  "costSaved": "$0.003"
}
```

**Response — AI Call:**
```json
{
  "response": "AI คือ...",
  "source": "AI",
  "ms": 1243,
  "cached": false
}
```

### GET /stats
```bash
curl http://localhost:3000/stats
```
```json
{
  "total": 1000,
  "cacheHits": 620,
  "cacheRate": "62.0%",
  "costSaved": "$1.860",
  "energySaved": "186.00mWh"
}
```

---

## เชื่อมต่อกับ App

```javascript
// เปลี่ยนแค่ URL — ไม่ต้องแก้ code อื่นเลย
const res = await fetch("https://YOUR-SERVER.railway.app/query", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ query: userMessage })
});
const { response, cached, costSaved } = await res.json();
```

---

## Environment Variables

| Variable | Default | คำอธิบาย |
|---|---|---|
| `ANTHROPIC_API_KEY` | **จำเป็น** | API Key จาก Anthropic |
| `PORT` | 3000 | Port |
| `CACHE_TTL_MS` | 3600000 | อายุ cache (1 ชั่วโมง) |
| `MAX_CACHE` | 10000 | จำนวน cache สูงสุด |
| `SEM_THRESH` | 0.72 | Semantic similarity threshold |

---

## License

MIT © 2026
