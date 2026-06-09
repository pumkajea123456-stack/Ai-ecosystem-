# 🚀 Quick Integration Guide - ใช้งานใน App ของคุณ

## 📦 สภาพพร้อมใช้งาน - Ready to Use

✅ **Status:** API Structure ตั้งค่าเสร็จสิ้นและทดสอบแล้ว
✅ **Features:** ทั้งหมด 10 ฟีเจอร์พร้อมใช้งาน
✅ **Performance:** ลดค่า 60-87% และ ระดับเร็ว
✅ **Reliability:** Multi-model fallback + health monitoring

---

## 🎯 3 ขั้นตอน เพื่อเริ่มใช้งาน

### 1️⃣ ตั้งค่า API Keys

```bash
# สร้างไฟล์ .env ด้วย 3 API Keys
chmod +x setup-multi-api.sh
./setup-multi-api.sh
```

**ต้องการ API Keys จาก:**
- 🔵 Gemini: https://aistudio.google.com/app/apikeys
- 🟢 DeepSeek: https://platform.deepseek.com/api_keys
- 🔴 Claude: https://console.anthropic.com/account/keys

---

### 2️⃣ เริ่ม Server

```bash
# Option A: Automatic
./setup-multi-api.sh

# Option B: Manual
npm install
node server.js

# Option C: Docker
docker build -t smartbot .
docker run -p 3000:3000 -e GEMINI_API_KEY=AIza... smartbot
```

**Server จะเริ่มที่:**
```
✅ http://localhost:3000
```

---

### 3️⃣ ใช้งานใน App

```javascript
// ตัวอย่าง JavaScript
const response = await fetch('http://localhost:3000/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'What is AI?' })
});

const data = await response.json();
console.log(data.response);        // AI response
console.log(data.cached);          // true/false
console.log(data.costSaved);       // $ saved
```

---

## 🔗 API Endpoints

### 1. POST /query - ส่งคำถาม
```bash
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?"}'
```

**Response:**
```json
{
  "response": "AI is...",
  "source": "EXACT",        // Cache hit
  "model": "Gemini",
  "ms": 8,
  "cached": true,
  "costSaved": "$0.003"
}
```

---

### 2. GET /health - ตรวจสอบสถานะ
```bash
curl http://localhost:3000/health
```

**Response:**
```json
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

---

### 3. GET /stats - ดูสถิติ
```bash
curl http://localhost:3000/stats
```

**Response:**
```json
{
  "total": 100,
  "cacheHits": 68,
  "cacheRate": "68.0%",
  "costSaved": "$0.204",
  "energySaved": "20.40mWh",
  "throughput": "0.28req/s"
}
```

---

### 4. GET /cache/info - ดู Cache ที่ใช้
```bash
curl http://localhost:3000/cache/info
```

---

### 5. POST /cache/clear - ล้าง Cache
```bash
curl -X POST http://localhost:3000/cache/clear
```

---

## 💻 Integration Examples

### React / React Native
```jsx
import React, { useState } from 'react';

export default function Chat() {
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({});

  const sendQuery = async (query) => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:3000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      
      setResponse(data.response);
      setStats({
        cached: data.cached,
        model: data.model,
        time: data.ms,
        saved: data.costSaved
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={() => sendQuery('What is AI?')}>
        Ask AI
      </button>
      {loading && <p>Loading...</p>}
      {response && (
        <div>
          <p>{response}</p>
          <p>
            {stats.cached ? '✅ From Cache' : '🔄 From AI'} 
            ({stats.time}ms) - Saved: {stats.saved}
          </p>
        </div>
      )}
    </div>
  );
}
```

---

### Vue.js
```vue
<template>
  <div>
    <button @click="askAI">Ask AI</button>
    <p v-if="loading">Loading...</p>
    <div v-if="response">
      <p>{{ response }}</p>
      <small>
        {{ cached ? '✅ Cached' : '🔄 AI Call' }} 
        ({{ time }}ms) - Saved: {{ saved }}
      </small>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      response: '',
      cached: false,
      time: 0,
      saved: '',
      loading: false
    }
  },
  methods: {
    async askAI() {
      this.loading = true;
      const res = await fetch('http://localhost:3000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'What is AI?' })
      });
      const data = await res.json();
      this.response = data.response;
      this.cached = data.cached;
      this.time = data.ms;
      this.saved = data.costSaved;
      this.loading = false;
    }
  }
}
</script>
```

---

### Python
```python
import requests

def ask_ai(question):
    """Send question to SmartBot Cache"""
    url = "http://localhost:3000/query"
    payload = {"query": question}
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    
    return {
        'response': data['response'],
        'cached': data['cached'],
        'model': data['model'],
        'time_ms': data['ms'],
        'cost_saved': data.get('costSaved', 'N/A')
    }

# Usage
result = ask_ai("What is AI?")
print(result['response'])
print(f"✅ Cached: {result['cached']}")
print(f"💰 Saved: {result['cost_saved']}")
```

---

### Java
```java
import java.net.http.*;
import com.google.gson.*;

public class SmartBotClient {
    private static final String API_URL = "http://localhost:3000/query";
    
    public static String askAI(String question) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        
        JsonObject body = new JsonObject();
        body.addProperty("query", question);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(new URI(API_URL))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(body.toString()))
            .build();
        
        HttpResponse<String> response = client.send(request, 
            HttpResponse.BodyHandlers.ofString());
        
        JsonObject data = JsonParser.parseString(response.body())
            .getAsJsonObject();
        
        return data.get("response").getAsString();
    }
}
```

---

### C# (.NET)
```csharp
using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;

public class SmartBotClient
{
    private static readonly string ApiUrl = "http://localhost:3000/query";
    
    public static async Task<string> AskAI(string question)
    {
        using (var client = new HttpClient())
        {
            var payload = new { query = question };
            var json = JsonSerializer.Serialize(payload);
            var content = new StringContent(json, 
                System.Text.Encoding.UTF8, "application/json");
            
            var response = await client.PostAsync(ApiUrl, content);
            var responseText = await response.Content.ReadAsStringAsync();
            
            var doc = JsonDocument.Parse(responseText);
            return doc.RootElement.GetProperty("response").GetString();
        }
    }
}
```

---

## 📱 Mobile Integration

### React Native
```javascript
const askAI = async (question) => {
  try {
    const response = await fetch('http://your-server:3000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: question })
    });
    
    const data = await response.json();
    return {
      text: data.response,
      model: data.model,
      cached: data.cached
    };
  } catch (error) {
    console.error('API Error:', error);
  }
};
```

### Flutter
```dart
Future<String> askAI(String question) async {
  final response = await http.post(
    Uri.parse('http://your-server:3000/query'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'query': question}),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return data['response'];
  }
  throw Exception('Failed to fetch');
}
```

---

## 🎨 Web Integration

### HTML + JavaScript
```html
<!DOCTYPE html>
<html>
<head>
    <title>SmartBot Chat</title>
</head>
<body>
    <input id="question" type="text" placeholder="Ask a question...">
    <button onclick="askAI()">Send</button>
    <div id="response"></div>
    <div id="stats"></div>

    <script>
        async function askAI() {
            const question = document.getElementById('question').value;
            
            const res = await fetch('http://localhost:3000/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: question })
            });
            
            const data = await res.json();
            
            document.getElementById('response').innerHTML = 
                `<p>${data.response}</p>`;
            
            document.getElementById('stats').innerHTML = 
                `<small>${data.cached ? '✅ Cached' : '🔄 AI'} 
                 (${data.ms}ms) - ${data.costSaved}</small>`;
        }
    </script>
</body>
</html>
```

---

## 🐛 Troubleshooting

### "Connection refused"
→ ตรวจสอบว่า server กำลังทำงาน:
```bash
curl http://localhost:3000/health
```

### "No AI model available"
→ ตั้ง API Key ใน .env และรีสตาร์ท server

### "Rate limit exceeded"
→ ลดจำนวน requests หรือรอ 60 วินาที

### High latency
→ ตรวจสอบ cache hit rate:
```bash
curl http://localhost:3000/stats | jq .cacheRate
```

---

## 📊 Performance Tips

1. **Maximize Cache Hit Rate**
   - ขอคำถามที่มีความหมายใกล้เคียง
   - Cache จะจับ 72% ความคล้าย (semantic)

2. **Monitor Costs**
   - Check `/stats` regularly
   - Focus on expensive queries

3. **Use Appropriate Models**
   - Simple: Gemini (FREE)
   - Complex: DeepSeek ($0.28/M)
   - Premium: Claude ($15/M)

---

## 🚀 Deploy to Production

### Railway.app
```bash
# 1. Push to GitHub
git push origin main

# 2. Connect to Railway
# Go to railway.app → New Project → Deploy from GitHub

# 3. Set environment variables
GEMINI_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Docker Deploy
```bash
docker build -t smartbot .
docker push your-registry/smartbot:latest

# Deploy
docker run -p 3000:3000 \
  -e GEMINI_API_KEY=AIza... \
  -e DEEPSEEK_API_KEY=sk-... \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  your-registry/smartbot:latest
```

---

## ✅ Checklist

- [ ] Clone repository
- [ ] Get 3 API Keys
- [ ] Run setup-multi-api.sh
- [ ] Verify with health check
- [ ] Test cache features
- [ ] Check statistics
- [ ] Integrate to app
- [ ] Monitor production

---

## 📞 Support

📖 **Documentation:** See SETUP.md, TESTING-GUIDE.md, MULTI-API-SETUP.md
🐛 **Issues:** Check server logs with LOG_LEVEL=debug
📊 **Stats:** Monitor with `/stats` endpoint

---

**🎉 Ready to integrate! Start with Step 1 above.**

