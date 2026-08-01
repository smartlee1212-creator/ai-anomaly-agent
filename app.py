from flask import Flask, render_template_string, jsonify
import urllib.request
import json
import os
from google import genai

app = Flask(__name__)
client = genai.Client()

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Anomaly Detection Agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 font-sans p-4">
    <div class="max-w-xl mx-auto space-y-6">
        <header class="border-b border-slate-800 pb-4 flex justify-between items-center">
            <div>
                <h1 class="text-xl font-bold text-cyan-400">🤖 AI Data & Anomaly Agent</h1>
                <p class="text-sm text-slate-400">Live monitoring & LLM reasoning engine</p>
            </div>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-800 text-emerald-200">
                ● Live API
            </span>
        </header>

        <div class="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg">
            <h2 class="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-2">Live Market Telemetry</h2>
            <div id="data-container" class="text-sm space-y-1 font-mono text-slate-300">
                Fetching live metrics...
            </div>
        </div>

        <div class="bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg">
            <h2 class="text-sm font-semibold text-cyan-400 uppercase tracking-wider mb-2">AI Engineer Analysis</h2>
            <div id="ai-insight" class="text-sm text-slate-300 leading-relaxed">
                Consulting Gemini model...
            </div>
        </div>
    </div>

    <script>
        async function fetchAgentData() {
            try {
                const response = await fetch('/api/data');
                const result = await response.json();
                
                document.getElementById('data-container').innerHTML = `
                    <div>Asset: <span class="text-white font-bold">${result.symbol}</span></div>
                    <div>Price: <span class="text-emerald-400 font-bold">$${result.price}</span></div>
                    <div>24h Change: <span class="text-amber-400">${result.change}%</span></div>
                `;
                
                document.getElementById('ai-insight').innerText = result.analysis;
            } catch (err) {
                document.getElementById('ai-insight').innerText = "Error syncing with agent backend.";
            }
        }
        fetchAgentData();
        setInterval(fetchAgentData, 45000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(TEMPLATE)

@app.route('/api/data')
def get_data():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        price = data['bitcoin']['usd']
        change = round(data['bitcoin']['usd_24h_change'], 2)
        
        status = "Normal market parameters."
        if abs(change) > 3.0:
            status = f"ANOMALY ALERT: Volatility spike of {change}% recorded."

        prompt = f"Analyze this live feed as an AI engineer: Bitcoin is trading at ${price} with a 24h change of {change}%. Status note: {status}. Provide a concise 2-sentence market evaluation."
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        ai_text = response.text

        return jsonify({
            "symbol": "BTC/USD",
            "price": price,
            "change": change,
            "analysis": ai_text
        })
    except Exception as e:
        return jsonify({
            "symbol": "BTC/USD",
            "price": "N/A",
            "change": "0",
            "analysis": f"Telemetry warning: Upstream connection limitation or model timeout. ({str(e)})"
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
