/**
 * SmartBot Cache Server v3.0
 * Multi-Model Smart Routing
 * Cache → Gemini (ฟรี) → DeepSeek (ถูก) → Claude (คุณภาพสูง)
 */

const http   = require("http");
const https  = require("https");
const crypto = require("crypto");

// ── Config ────────────────────────────────────────────
const PORT         = process.env.PORT            || 3000;
const GEMINI_KEY   = process.env.GEMINI_API_KEY  || "";
const DEEPSEEK_KEY = process.env.DEEPSEEK_API_KEY|| "";
const CLAUDE_KEY   = process.env.ANTHROPIC_API_KEY|| "";
const CACHE_TTL    = parseInt(process.env.CACHE_TTL_MS || "3600000");
const MAX_CACHE    = parseInt(process.env.MAX_CACHE    || "10000");
const SEM_THRESH   = parseFloat(process.env.SEM_THRESH || "0.72");

// ── Models Config ─────────────────────────────────────
const MODELS = {
  gemini: {
    name: "Gemini Flash",
    costPer1M: 0.0,      // ฟรี 1,500/วัน
    maxTokens: 200,      // คำถามสั้น
    available: () => !!GEMINI_KEY,
  },
  deepseek: {
    name: "DeepSeek V3",
    costPer1M: 0.27,
    maxTokens: 500,      // คำถามกลาง
    available: () => !!DEEPSEEK_KEY,
  },
  claude: {
    name: "Claude Sonnet",
    costPer1M: 3.00,
    maxTokens: 99999,    // คำถามยากทุกอย่าง
    available: () => !!CLAUDE_KEY,
  },
};

// ── Smart Router ──────────────────────────────────────
function selectModel(query) {
  const words = query.trim().split(/\s+/).length;
  const isComplex = /วิเคราะห์|เปรียบเทียบ|อธิบาย|สรุป|แนะนำ|ช่วย|เขียน|สร้าง|analyze|compare|explain|write|create|complex/i.test(query);

  // ง่าย + สั้น → Gemini (ฟรี)
  if (words <= 10 && !isComplex && MODELS.gemini.available()) return "gemini";

  // กลาง → DeepSeek (ถูก)
  if (words <= 30 && MODELS.deepseek.available()) return "deepseek";

  // ยาก/ซับซ้อน → Claude
  if (MODELS.claude.available()) return "claude";

  // Fallback ตามลำดับ
  if (MODELS.gemini.available()) return "gemini";
  if (MODELS.deepseek.available()) return "deepseek";
  return null;
}

// ── Cache ─────────────────────────────────────────────
const cache = new Map();
const stats = {
  total: 0, cacheHits: 0, aiCalls: 0,
  costSaved: 0, energySaved: 0,
  modelUsage: { gemini: 0, deepseek: 0, claude: 0 },
  start: Date.now(),
};

function hashQ(q) {
  return crypto.createHash("md5").update(q.trim().toLowerCase()).digest("hex");
}

function semSim(a, b) {
  const wa = new Set(a.toLowerCase().split(/\s+/).filter(w => w.length > 2));
  const wb = new Set(b.toLowerCase().split(/\s+/).filter(w => w.length > 2));
  if (!wa.size || !wb.size) return 0;
  return [...wa].filter(x => wb.has(x)).length / new Set([...wa, ...wb]).size;
}

function checkCache(q) {
  const now = Date.now(), key = hashQ(q);
  if (cache.has(key)) {
    const e = cache.get(key);
    if (now - e.ts < CACHE_TTL) { e.hits++; return { hit: true, type: "EXACT", entry: e }; }
    cache.delete(key);
  }
  for (const [, e] of cache) {
    if (now - e.ts >= CACHE_TTL) continue;
    const sim = semSim(q, e.query);
    if (sim >= SEM_THRESH) { e.hits++; return { hit: true, type: `SEMANTIC_${Math.round(sim * 100)}`, entry: e }; }
  }
  return { hit: false };
}

function storeCache(q, response, model) {
  if (cache.size >= MAX_CACHE) {
    const old = [...cache.entries()].sort((a, b) => a[1].ts - b[1].ts)[0];
    if (old) cache.delete(old[0]);
  }
  cache.set(hashQ(q), { query: q, response, model, ts: Date.now(), hits: 0 });
}

setInterval(() => {
  const now = Date.now();
  for (const [k, v] of cache) if (now - v.ts >= CACHE_TTL) cache.delete(k);
}, 60000);

// ── AI Callers ────────────────────────────────────────
function callGemini(query, system) {
  return new Promise((resolve, reject) => {
    const prompt = system ? `${system}\n\n${query}` : query;
    const body = JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { maxOutputTokens: 1024 }
    });
    const req = https.request({
      hostname: "generativelanguage.googleapis.com",
      path: `/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_KEY}`,
      method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) },
    }, res => {
      let data = "";
      res.on("data", c => data += c);
      res.on("end", () => {
        try {
          const j = JSON.parse(data);
          if (j.error) return reject(new Error(j.error.message));
          resolve({ text: j.candidates?.[0]?.content?.parts?.[0]?.text || "" });
        } catch (e) { reject(e); }
      });
    });
    req.on("error", reject);
    req.write(body); req.end();
  });
}

function callDeepSeek(query, system) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: "deepseek-chat",
      messages: [
        ...(system ? [{ role: "system", content: system }] : []),
        { role: "user", content: query }
      ],
      max_tokens: 1024,
    });
    const req = https.request({
      hostname: "api.deepseek.com",
      path: "/v1/chat/completions",
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${DEEPSEEK_KEY}` },
    }, res => {
      let data = "";
      res.on("data", c => data += c);
      res.on("end", () => {
        try {
          const j = JSON.parse(data);
          if (j.error) return reject(new Error(j.error.message));
          resolve({ text: j.choices?.[0]?.message?.content || "" });
        } catch (e) { reject(e); }
      });
    });
    req.on("error", reject);
    req.write(body); req.end();
  });
}

function callClaude(query, system) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      system: system || "You are a helpful assistant.",
      messages: [{ role: "user", content: query }],
    });
    const req = https.request({
      hostname: "api.anthropic.com",
      path: "/v1/messages",
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": CLAUDE_KEY,
        "anthropic-version": "2023-06-01",
      },
    }, res => {
      let data = "";
      res.on("data", c => data += c);
      res.on("end", () => {
        try {
          const j = JSON.parse(data);
          if (j.error) return reject(new Error(j.error.message));
          resolve({ text: j.content?.[0]?.text || "" });
        } catch (e) { reject(e); }
      });
    });
    req.on("error", reject);
    req.write(body); req.end();
  });
}

async function callAI(modelId, query, system) {
  if (modelId === "gemini")   return callGemini(query, system);
  if (modelId === "deepseek") return callDeepSeek(query, system);
  if (modelId === "claude")   return callClaude(query, system);
  throw new Error("No AI model available");
}

// ── Request Handler ───────────────────────────────────
async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Content-Type", "application/json");
  if (req.method === "OPTIONS") return res.end("{}");

  const url = new URL(req.url, "http://localhost");

  // GET /health
  if (req.method === "GET" && url.pathname === "/health") {
    return res.end(JSON.stringify({
      status: "ok",
      version: "3.0",
      uptime: Date.now() - stats.start,
      models: {
        gemini:   MODELS.gemini.available()   ? "✅" : "❌ no key",
        deepseek: MODELS.deepseek.available() ? "✅" : "❌ no key",
        claude:   MODELS.claude.available()   ? "✅" : "❌ no key",
      }
    }));
  }

  // GET /stats
  if (req.method === "GET" && url.pathname === "/stats") {
    const rate = stats.total > 0 ? ((stats.cacheHits / stats.total) * 100).toFixed(1) : "0.0";
    return res.end(JSON.stringify({
      ...stats,
      cacheSize: cache.size,
      cacheRate: `${rate}%`,
      costSaved: `$${stats.costSaved.toFixed(4)}`,
      energySaved: `${(stats.energySaved * 1000).toFixed(2)}mWh`,
    }));
  }

  // POST /cache/clear
  if (req.method === "POST" && url.pathname === "/cache/clear") {
    cache.clear();
    return res.end(JSON.stringify({ cleared: true }));
  }

  // POST /query
  if (req.method === "POST" && url.pathname === "/query") {
    let body = "";
    req.on("data", c => body += c);
    req.on("end", async () => {
      try {
        const { query, system, model: forceModel } = JSON.parse(body);
        if (!query) { res.statusCode = 400; return res.end(JSON.stringify({ error: "query is required" })); }

        stats.total++;
        const t0 = Date.now();

        // เช็ค Cache ก่อน
        const cached = checkCache(query);
        if (cached.hit) {
          stats.cacheHits++;
          stats.costSaved   += 0.002;
          stats.energySaved += 0.0003;
          return res.end(JSON.stringify({
            response:  cached.entry.response,
            source:    cached.type,
            model:     cached.entry.model,
            ms:        Date.now() - t0,
            cached:    true,
            costSaved: "$0.002",
          }));
        }

        // เลือก Model
        const modelId = forceModel || selectModel(query);
        if (!modelId) { res.statusCode = 500; return res.end(JSON.stringify({ error: "No AI model available — please set at least one API key" })); }

        stats.aiCalls++;
        stats.modelUsage[modelId] = (stats.modelUsage[modelId] || 0) + 1;

        const { text } = await callAI(modelId, query, system);
        storeCache(query, text, modelId);

        return res.end(JSON.stringify({
          response: text,
          source:   "AI",
          model:    MODELS[modelId].name,
          ms:       Date.now() - t0,
          cached:   false,
        }));

      } catch (err) {
        res.statusCode = 500;
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  res.statusCode = 404;
  res.end(JSON.stringify({ error: "Not found" }));
}

http.createServer(handler).listen(PORT, () => {
  console.log(`\n✅ SmartBot Cache v3.0 — Multi-Model Router`);
  console.log(`   Port: ${PORT}`);
  console.log(`   Gemini:   ${MODELS.gemini.available()   ? "✅ Ready (FREE)" : "❌ No key"}`);
  console.log(`   DeepSeek: ${MODELS.deepseek.available() ? "✅ Ready ($0.27/M)" : "❌ No key"}`);
  console.log(`   Claude:   ${MODELS.claude.available()   ? "✅ Ready ($3/M)" : "❌ No key"}`);
  console.log(`\n   Routing: ง่าย→Gemini | กลาง→DeepSeek | ยาก→Claude\n`);
});
