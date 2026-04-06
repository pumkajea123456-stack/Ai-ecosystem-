/**
 * ╔══════════════════════════════════════════════════════════╗
 * ║          SmartBot Cache Server v4.0                     ║
 * ║          Production-Grade Multi-Model Router            ║
 * ╠══════════════════════════════════════════════════════════╣
 * ║ แก้ไขจาก v3.0:                                          ║
 * ║  ✅ Fallback chain — ถ้า model ล้มเหลว ลองตัวถัดไป      ║
 * ║  ✅ Request deduplication — ไม่เรียก AI ซ้อน            ║
 * ║  ✅ Model health monitoring + auto-recovery              ║
 * ║  ✅ LRU cache eviction แทน FIFO                          ║
 * ║  ✅ Rate limiting per IP                                 ║
 * ║  ✅ Body size limit ป้องกัน abuse                        ║
 * ║  ✅ Auto cache GC ทุก 5 นาที                            ║
 * ║  ✅ Security headers ทุก response                        ║
 * ║  ✅ Timeout per model call                               ║
 * ║  ✅ Structured logging                                   ║
 * ║  ✅ /version endpoint                                    ║
 * ║  ✅ /cache/info endpoint                                 ║
 * ║  ✅ Graceful shutdown                                    ║
 * ╚══════════════════════════════════════════════════════════╝
 */

"use strict";
const http   = require("http");
const https  = require("https");
const crypto = require("crypto");

const VERSION = "4.0.0";
const STARTED = new Date().toISOString();

const CFG = {
  PORT:          parseInt(process.env.PORT)           || 3000,
  GEMINI_KEY:    process.env.GEMINI_API_KEY           || "",
  DEEPSEEK_KEY:  process.env.DEEPSEEK_API_KEY         || "",
  CLAUDE_KEY:    process.env.ANTHROPIC_API_KEY        || "",
  CACHE_TTL:     parseInt(process.env.CACHE_TTL_MS)   || 3_600_000,
  MAX_CACHE:     parseInt(process.env.MAX_CACHE)      || 10_000,
  SEM_THRESH:    parseFloat(process.env.SEM_THRESH)   || 0.72,
  MAX_BODY_KB:   parseInt(process.env.MAX_BODY_KB)    || 32,
  RATE_WINDOW:   parseInt(process.env.RATE_WINDOW)    || 60_000,
  RATE_LIMIT:    parseInt(process.env.RATE_LIMIT)     || 300,
  MODEL_TIMEOUT: parseInt(process.env.MODEL_TIMEOUT)  || 15_000,
  LOG_LEVEL:     process.env.LOG_LEVEL                || "info",
};

const MODELS = {
  gemini: {
    name: "Gemini 1.5 Flash", tier: "free",
    call: callGemini,
    health: { ok: true, fails: 0, lastFail: null },
  },
  deepseek: {
    name: "DeepSeek V3.2", tier: "budget",
    call: callDeepSeek,
    health: { ok: true, fails: 0, lastFail: null },
  },
  claude: {
    name: "Claude Sonnet 4.6", tier: "quality",
    call: callClaude,
    health: { ok: true, fails: 0, lastFail: null },
  },
};

const STATS = {
  total: 0, cacheHits: 0, semanticHits: 0, aiCalls: 0,
  errors: 0, fallbacks: 0, deduplicated: 0,
  costSaved: 0, energySaved: 0,
  modelUsage: { gemini: 0, deepseek: 0, claude: 0 },
  start: Date.now(),
};

const CACHE    = new Map();
const PENDING  = new Map();
const RATE_MAP = new Map();

function log(level, msg, meta = {}) {
  if (level === "debug" && CFG.LOG_LEVEL !== "debug") return;
  const ts  = new Date().toISOString().slice(11, 23);
  const pfx = { info:"ℹ", debug:"·", error:"✗", warn:"⚠" }[level] || "·";
  const extra = Object.keys(meta).length
    ? " " + Object.entries(meta).map(([k,v]) => `${k}=${v}`).join(" ") : "";
  console.log(`[${ts}] ${pfx} ${msg}${extra}`);
}

function hashQ(q) {
  return crypto.createHash("sha256").update(q.trim().toLowerCase()).digest("hex").slice(0,16);
}

function semSim(a, b) {
  const stop = new Set(["คือ","ที่","ของ","และ","ใน","การ","มี","ได้","the","a","is","of","and","in","to"]);
  const wa = new Set(a.toLowerCase().split(/\s+/).filter(w => w.length > 2 && !stop.has(w)));
  const wb = new Set(b.toLowerCase().split(/\s+/).filter(w => w.length > 2 && !stop.has(w)));
  if (!wa.size || !wb.size) return 0;
  return [...wa].filter(x => wb.has(x)).length / new Set([...wa,...wb]).size;
}

function selectModel(query) {
  const words     = query.trim().split(/\s+/).length;
  const isComplex = /วิเคราะห์|เปรียบเทียบ|อธิบาย|สรุป|เขียน|สร้าง|analyze|compare|explain|write|create|design/i.test(query);
  const order = [];

  if (words <= 12 && !isComplex && MODELS.gemini.health.ok && CFG.GEMINI_KEY)
    order.push("gemini");
  if (words <= 35 && MODELS.deepseek.health.ok && CFG.DEEPSEEK_KEY)
    order.push("deepseek");
  if (MODELS.claude.health.ok && CFG.CLAUDE_KEY)
    order.push("claude");

  // fallback: add remaining available models
  ["gemini","deepseek","claude"].forEach(id => {
    const hasKey = id==="gemini"?CFG.GEMINI_KEY:id==="deepseek"?CFG.DEEPSEEK_KEY:CFG.CLAUDE_KEY;
    if (!order.includes(id) && MODELS[id].health.ok && hasKey) order.push(id);
  });

  return order.length > 0 ? order : null;
}

function getCache(query) {
  const now = Date.now(), key = hashQ(query);
  if (CACHE.has(key)) {
    const e = CACHE.get(key);
    if (now - e.ts < CFG.CACHE_TTL) { e.hits++; e.lastHit = now; return { hit:true, type:"EXACT", entry:e }; }
    CACHE.delete(key);
  }
  for (const [,e] of CACHE) {
    if (now - e.ts >= CFG.CACHE_TTL) continue;
    const sim = semSim(query, e.query);
    if (sim >= CFG.SEM_THRESH) { e.hits++; e.lastHit = now; return { hit:true, type:`SEMANTIC_${Math.round(sim*100)}`, entry:e }; }
  }
  return { hit: false };
}

function setCache(query, response, model) {
  if (CACHE.size >= CFG.MAX_CACHE) {
    const sorted = [...CACHE.entries()].sort((a,b) => (a[1].lastHit||a[1].ts)-(b[1].lastHit||b[1].ts));
    sorted.slice(0, Math.ceil(CFG.MAX_CACHE*0.1)).forEach(([k]) => CACHE.delete(k));
  }
  CACHE.set(hashQ(query), {
    query, response, model,
    ts: Date.now(), hits: 0, lastHit: null,
    hash: crypto.createHash("md5").update(response).digest("hex").slice(0,8),
  });
}

setInterval(() => {
  const now = Date.now(); let n = 0;
  for (const [k,v] of CACHE) if (now-v.ts >= CFG.CACHE_TTL) { CACHE.delete(k); n++; }
  if (n > 0) log("info","Cache GC",{removed:n,remaining:CACHE.size});
}, 300_000);

function checkRate(ip) {
  const now = Date.now();
  const e = RATE_MAP.get(ip) || { count:0, reset:now+CFG.RATE_WINDOW };
  if (now > e.reset) { e.count=0; e.reset=now+CFG.RATE_WINDOW; }
  e.count++; RATE_MAP.set(ip,e);
  return e.count <= CFG.RATE_LIMIT;
}
setInterval(() => { const now=Date.now(); for(const[k,e]of RATE_MAP)if(now>e.reset)RATE_MAP.delete(k); }, 60_000);

function markFail(id) {
  const m = MODELS[id]; if(!m) return;
  m.health.fails++; m.health.lastFail = Date.now();
  if (m.health.fails >= 3) {
    m.health.ok = false;
    log("warn","Model disabled",{model:id});
    setTimeout(() => { m.health.ok=true; m.health.fails=0; log("info","Model recovered",{model:id}); }, 300_000);
  }
}
function markOk(id) { if(MODELS[id]) { MODELS[id].health.ok=true; MODELS[id].health.fails=0; } }

function httpsPost(host, path, headers, body) {
  return new Promise((resolve,reject) => {
    const timer = setTimeout(() => reject(new Error("Timeout")), CFG.MODEL_TIMEOUT);
    const req = https.request({hostname:host,path,method:"POST",headers}, res => {
      let data="";
      res.on("data",c=>data+=c);
      res.on("end",()=>{ clearTimeout(timer); try{resolve({status:res.statusCode,body:JSON.parse(data)})}catch(e){reject(new Error(`Parse:${data.slice(0,80)}`))} });
    });
    req.on("error",e=>{ clearTimeout(timer); reject(e); });
    req.write(body); req.end();
  });
}

async function callGemini(q, sys) {
  const prompt = sys?`${sys}\n\n${q}`:q;
  const body   = JSON.stringify({contents:[{parts:[{text:prompt}]}],generationConfig:{maxOutputTokens:1024,temperature:0.7}});
  const r = await httpsPost("generativelanguage.googleapis.com",
    `/v1beta/models/gemini-1.5-flash:generateContent?key=${CFG.GEMINI_KEY}`,
    {"Content-Type":"application/json","Content-Length":Buffer.byteLength(body)},body);
  if(r.body.error) throw new Error(r.body.error.message);
  const text = r.body.candidates?.[0]?.content?.parts?.[0]?.text;
  if(!text) throw new Error("Empty Gemini response");
  return text;
}

async function callDeepSeek(q, sys) {
  const msgs = sys?[{role:"system",content:sys},{role:"user",content:q}]:[{role:"user",content:q}];
  const body = JSON.stringify({model:"deepseek-chat",messages:msgs,max_tokens:1024,temperature:0.7});
  const r = await httpsPost("api.deepseek.com","/v1/chat/completions",
    {"Content-Type":"application/json","Authorization":`Bearer ${CFG.DEEPSEEK_KEY}`,"Content-Length":Buffer.byteLength(body)},body);
  if(r.body.error) throw new Error(r.body.error.message);
  const text = r.body.choices?.[0]?.message?.content;
  if(!text) throw new Error("Empty DeepSeek response");
  return text;
}

async function callClaude(q, sys) {
  const body = JSON.stringify({model:"claude-sonnet-4-20250514",max_tokens:1024,
    system:sys||"You are a helpful assistant. Answer clearly in the same language as the question.",
    messages:[{role:"user",content:q}]});
  const r = await httpsPost("api.anthropic.com","/v1/messages",
    {"Content-Type":"application/json","x-api-key":CFG.CLAUDE_KEY,"anthropic-version":"2023-06-01","Content-Length":Buffer.byteLength(body)},body);
  if(r.body.error) throw new Error(r.body.error.message);
  const text = r.body.content?.[0]?.text;
  if(!text) throw new Error("Empty Claude response");
  return text;
}

async function callWithFallback(query, system) {
  const key   = hashQ(query);
  const order = selectModel(query);
  if (PENDING.has(key)) { STATS.deduplicated++; return PENDING.get(key); }
  if (!order) throw new Error("No AI model available — set GEMINI_API_KEY / DEEPSEEK_API_KEY / ANTHROPIC_API_KEY");

  const promise = (async () => {
    let lastErr;
    for (const id of order) {
      try {
        const text = await MODELS[id].call(query, system);
        markOk(id);
        STATS.modelUsage[id] = (STATS.modelUsage[id]||0)+1;
        if (id !== order[0]) STATS.fallbacks++;
        return { text, model: id };
      } catch(err) { lastErr=err; markFail(id); log("warn","Model failed",{model:id,err:err.message}); }
    }
    throw lastErr || new Error("All models failed");
  })();

  PENDING.set(key, promise);
  promise.finally(() => PENDING.delete(key));
  return promise;
}

function parseBody(req) {
  return new Promise((resolve,reject) => {
    let body="", bytes=0;
    req.on("data",chunk=>{ bytes+=chunk.length; if(bytes>CFG.MAX_BODY_KB*1024){reject(new Error("Body too large"));return;} body+=chunk; });
    req.on("end",()=>{ try{resolve(JSON.parse(body))}catch{reject(new Error("Invalid JSON"))} });
    req.on("error",reject);
  });
}

async function handler(req, res) {
  const ip  = (req.headers["x-forwarded-for"]||"").split(",")[0].trim()||req.socket?.remoteAddress||"?";
  const url = new URL(req.url,"http://localhost");

  res.setHeader("Access-Control-Allow-Origin","*");
  res.setHeader("Access-Control-Allow-Headers","Content-Type");
  res.setHeader("Access-Control-Allow-Methods","GET,POST,OPTIONS");
  res.setHeader("Content-Type","application/json; charset=utf-8");
  res.setHeader("X-SmartBot-Version",VERSION);
  res.setHeader("X-Content-Type-Options","nosniff");

  if (req.method==="OPTIONS") return res.end("{}");

  if (!checkRate(ip)) {
    res.statusCode=429;
    return res.end(JSON.stringify({error:"Rate limit exceeded",retryAfter:Math.ceil(CFG.RATE_WINDOW/1000)}));
  }

  const p = url.pathname;

  if (req.method==="GET" && p==="/health") {
    const models = {};
    for (const [id,m] of Object.entries(MODELS)) {
      const hasKey = id==="gemini"?!!CFG.GEMINI_KEY:id==="deepseek"?!!CFG.DEEPSEEK_KEY:!!CFG.CLAUDE_KEY;
      models[id] = hasKey&&m.health.ok?"✅ ready":!hasKey?"❌ no key":`⚠️ down(${m.health.fails}fails)`;
    }
    return res.end(JSON.stringify({status:"ok",version:VERSION,uptime:Math.floor((Date.now()-STATS.start)/1000)+"s",started:STARTED,models,cache:{size:CACHE.size,max:CFG.MAX_CACHE},pending:PENDING.size},null,2));
  }

  if (req.method==="GET" && p==="/version") {
    return res.end(JSON.stringify({
      version:VERSION,started:STARTED,
      changes:[
        "v4.0 — Fallback chain: auto-retry next model on failure",
        "v4.0 — Request deduplication: no duplicate AI calls",
        "v4.0 — Model health monitoring + 5min auto-recovery",
        "v4.0 — LRU cache eviction (10% evict when full)",
        "v4.0 — Rate limiting: 300 req/60s per IP",
        "v4.0 — Body size limit: 32KB max",
        "v4.0 — Auto cache GC every 5 minutes",
        "v4.0 — Security headers on all responses",
        "v4.0 — 15s timeout per model call",
        "v4.0 — /version and /cache/info endpoints",
        "v3.0 — Multi-model routing (Gemini/DeepSeek/Claude)",
        "v2.0 — Gemini API support",
        "v1.0 — Basic semantic cache + Anthropic",
      ],
      config:{cacheTTL:`${CFG.CACHE_TTL/3600000}hr`,maxCache:CFG.MAX_CACHE,semThresh:CFG.SEM_THRESH,
              rateLimit:`${CFG.RATE_LIMIT}req/${CFG.RATE_WINDOW/1000}s`,timeout:`${CFG.MODEL_TIMEOUT/1000}s`},
    },null,2));
  }

  if (req.method==="GET" && p==="/stats") {
    const total = STATS.total||1, uptime=(Date.now()-STATS.start)/1000;
    return res.end(JSON.stringify({
      version:VERSION,uptime:Math.floor(uptime)+"s",
      total:STATS.total,cacheHits:STATS.cacheHits,semanticHits:STATS.semanticHits,
      aiCalls:STATS.aiCalls,errors:STATS.errors,fallbacks:STATS.fallbacks,deduplicated:STATS.deduplicated,
      cacheRate:((STATS.cacheHits/total)*100).toFixed(1)+"%",cacheSize:CACHE.size,
      costSaved:"$"+STATS.costSaved.toFixed(4),energySaved:(STATS.energySaved*1000).toFixed(2)+"mWh",
      throughput:(STATS.total/Math.max(uptime,1)).toFixed(2)+"req/s",modelUsage:STATS.modelUsage,
    },null,2));
  }

  if (req.method==="POST" && p==="/cache/clear") {
    const n=CACHE.size; CACHE.clear();
    return res.end(JSON.stringify({cleared:true,removed:n}));
  }

  if (req.method==="GET" && p==="/cache/info") {
    const now=Date.now();
    const top=[...CACHE.values()].map(e=>({query:e.query.slice(0,50),model:e.model,hits:e.hits,ageMin:Math.floor((now-e.ts)/60000),hash:e.hash}))
      .sort((a,b)=>b.hits-a.hits).slice(0,20);
    return res.end(JSON.stringify({total:CACHE.size,top20:top},null,2));
  }

  if (req.method==="POST" && p==="/query") {
    let payload;
    try { payload = await parseBody(req); }
    catch(err) { res.statusCode=400; return res.end(JSON.stringify({error:err.message})); }

    const {query,system,forceModel} = payload;
    if (!query||typeof query!=="string"||!query.trim()) {
      res.statusCode=400; return res.end(JSON.stringify({error:"query is required"}));
    }
    if (query.length>4000) {
      res.statusCode=400; return res.end(JSON.stringify({error:"query too long (max 4000 chars)"}));
    }

    STATS.total++;
    const t0=Date.now(), cached=getCache(query);

    if (cached.hit && !forceModel) {
      STATS.cacheHits++;
      if (cached.type.startsWith("SEMANTIC")) STATS.semanticHits++;
      STATS.costSaved+=0.003; STATS.energySaved+=0.00024;
      return res.end(JSON.stringify({
        response:cached.entry.response,source:cached.type,model:cached.entry.model,
        ms:Date.now()-t0,cached:true,costSaved:"$0.003",hits:cached.entry.hits,
        cacheHash:cached.entry.hash,version:VERSION,
      }));
    }

    STATS.aiCalls++;
    try {
      const {text,model} = await callWithFallback(query,
        system||"You are a helpful assistant. Answer clearly in the same language as the question.");
      setCache(query,text,model);
      return res.end(JSON.stringify({
        response:text,source:"AI",model:MODELS[model]?.name||model,modelId:model,
        ms:Date.now()-t0,cached:false,version:VERSION,
      }));
    } catch(err) {
      STATS.errors++;
      res.statusCode=503;
      return res.end(JSON.stringify({
        error:err.message,
        suggestion:"Set GEMINI_API_KEY for free tier (aistudio.google.com)",
        models:Object.fromEntries(Object.entries(MODELS).map(([id,m])=>[id,m.health.ok?"available":"down"])),
        version:VERSION,
      }));
    }
  }

  res.statusCode=404;
  res.end(JSON.stringify({
    error:"Not found",version:VERSION,
    endpoints:["GET /health","GET /version","GET /stats","GET /cache/info","POST /query","POST /cache/clear"],
  }));
}

const server = http.createServer(async (req,res) => {
  try { await handler(req,res); }
  catch(err) {
    log("error","Unhandled",{err:err.message});
    if (!res.headersSent) { res.statusCode=500; res.end(JSON.stringify({error:"Internal error",version:VERSION})); }
  }
});

server.listen(CFG.PORT, () => {
  const G = CFG.GEMINI_KEY   ? "✅ Free"   : "❌ No key";
  const D = CFG.DEEPSEEK_KEY ? "✅ $0.28"  : "❌ No key";
  const C = CFG.CLAUDE_KEY   ? "✅ $3.00"  : "❌ No key";
  console.log(`
╔══════════════════════════════════════╗
║   SmartBot Cache v${VERSION}          ║
╠══════════════════════════════════════╣
║  Port     : ${CFG.PORT}                       ║
║  Gemini   : ${G}              ║
║  DeepSeek : ${D}            ║
║  Claude   : ${C}            ║
╠══════════════════════════════════════╣
║  Cache    : ${CFG.MAX_CACHE} / ${CFG.CACHE_TTL/3600000}hr TTL         ║
║  Rate     : ${CFG.RATE_LIMIT}req/${CFG.RATE_WINDOW/1000}s/IP          ║
╚══════════════════════════════════════╝`);
});

server.on("error", err => { console.error("Fatal:", err.message); process.exit(1); });
process.on("SIGTERM", () => { server.close(() => process.exit(0)); });
