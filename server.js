/**
 * SmartBot Cache Server v1.0
 * ลดค่า AI API 60-80% ด้วย Local Cache
 * Deploy: node server.js
 */

const http   = require("http");
const https  = require("https");
const crypto = require("crypto");

const PORT       = process.env.PORT       || 3000;
const API_KEY    = process.env.ANTHROPIC_API_KEY || "";
const CACHE_TTL  = parseInt(process.env.CACHE_TTL_MS || "3600000");
const MAX_CACHE  = parseInt(process.env.MAX_CACHE    || "10000");
const MODEL      = process.env.AI_MODEL  || "claude-sonnet-4-20250514";
const SEM_THRESH = parseFloat(process.env.SEM_THRESH || "0.72");

// ── Cache & Stats ────────────────────────────────────
const cache = new Map();
const stats = {
  total: 0, cacheHits: 0, aiCalls: 0,
  costSaved: 0, energySaved: 0,
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
  const now = Date.now();
  const key = hashQ(q);
  if (cache.has(key)) {
    const e = cache.get(key);
    if (now - e.ts < CACHE_TTL) { e.hits++; return { hit: true, type: "EXACT", entry: e }; }
    cache.delete(key);
  }
  for (const [, e] of cache) {
    if (now - e.ts >= CACHE_TTL) continue;
    const sim = semSim(q, e.query);
    if (sim >= SEM_THRESH) { e.hits++; return { hit: true, type: `SEMANTIC_${Math.round(sim*100)}`, entry: e }; }
  }
  return { hit: false };
}

function storeCache(q, response) {
  if (cache.size >= MAX_CACHE) {
    const old = [...cache.entries()].sort((a,b) => a[1].ts - b[1].ts)[0];
    if (old) cache.delete(old[0]);
  }
  cache.set(hashQ(q), { query: q, response, ts: Date.now(), hits: 0 });
}

setInterval(() => {
  const now = Date.now();
  for (const [k, v] of cache) if (now - v.ts >= CACHE_TTL) cache.delete(k);
}, 60000);

// ── Call Claude API ───────────────────────────────────
function callClaude(query, system) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: MODEL, max_tokens: 1024,
      system: system || "You are a helpful assistant. Answer clearly and concisely.",
      messages: [{ role: "user", content: query }],
    });
    const req = https.request({
      hostname: "api.anthropic.com", path: "/v1/messages", method: "POST",
      headers: { "Content-Type": "application/json", "x-api-key": API_KEY, "anthropic-version": "2023-06-01" },
    }, res => {
      let data = "";
      res.on("data", c => data += c);
      res.on("end", () => {
        try {
          const j = JSON.parse(data);
          if (j.error) return reject(new Error(j.error.message));
          resolve({ text: j.content?.[0]?.text || "", tokens: (j.usage?.input_tokens||0) + (j.usage?.output_tokens||0) });
        } catch(e) { reject(e); }
      });
    });
    req.on("error", reject);
    req.write(body); req.end();
  });
}

// ── Request Handler ───────────────────────────────────
async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader("Content-Type", "application/json");
  if (req.method === "OPTIONS") return res.end("{}");

  const url = new URL(req.url, "http://localhost");

  // GET /health
  if (req.method === "GET" && url.pathname === "/health")
    return res.end(JSON.stringify({ status: "ok", uptime: Date.now() - stats.start }));

  // GET /stats
  if (req.method === "GET" && url.pathname === "/stats") {
    const rate = stats.total > 0 ? ((stats.cacheHits / stats.total) * 100).toFixed(1) : "0.0";
    return res.end(JSON.stringify({
      ...stats, cacheSize: cache.size,
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

  // POST /query  ← endpoint หลัก
  if (req.method === "POST" && url.pathname === "/query") {
    let body = "";
    req.on("data", c => body += c);
    req.on("end", async () => {
      try {
        const { query, system } = JSON.parse(body);
        if (!query) { res.statusCode = 400; return res.end(JSON.stringify({ error: "query is required" })); }

        stats.total++;
        const t0 = Date.now();
        const cached = checkCache(query);

        if (cached.hit) {
          stats.cacheHits++;
          stats.costSaved   += 0.003;
          stats.energySaved += 0.0003;
          return res.end(JSON.stringify({
            response: cached.entry.response,
            source: cached.type, ms: Date.now() - t0,
            cached: true, costSaved: "$0.003",
          }));
        }

        if (!API_KEY) { res.statusCode = 500; return res.end(JSON.stringify({ error: "ANTHROPIC_API_KEY not set" })); }

        stats.aiCalls++;
        const { text, tokens } = await callClaude(query, system);
        storeCache(query, text);
        return res.end(JSON.stringify({
          response: text, source: "AI",
          ms: Date.now() - t0, cached: false, tokens,
        }));
      } catch(err) {
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
  console.log(`\n✅ SmartBot Cache รันอยู่ที่ port ${PORT}`);
  console.log(`   POST /query   → ค้นหา (cache first)`);
  console.log(`   GET  /stats   → สถิติ`);
  console.log(`   GET  /health  → health check\n`);
});
