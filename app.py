import os
import requests
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)

def get_token():
    r = requests.post(
        "https://api.scaleaq.com/auth/token",
        headers={
            "Content-Type": "application/json",
            "scale-version": "2025-01-01"
        },
        json={
            "username": os.getenv("SCALEAQ_USERNAME"),
            "password": os.getenv("SCALEAQ_PASSWORD")
        }
    )
    r.raise_for_status()
    return r.json()["access_token"]

def get_sites(token):
    r = requests.get(
        "https://api.scaleaq.com/meta/company?include=all",
        headers={
            "Scale-Version": "2025-01-01",
            "Authorization": f"Bearer {token}"
        }
    )
    r.raise_for_status()
    return r.json()

def get_feed_data(token, site_ids, unit_ids, from_time, to_time):
    r = requests.post(
        "https://api.scaleaq.com/time-series/retrieve/units/aggregate",
        headers={
            "Scale-Version": "2025-01-01",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "fromTime": from_time,
            "toTime": to_time,
            "siteids": site_ids,
            "dataTypes": ["FeedAmount", "Intensity"],
            "unitIds": unit_ids,
            "depth": None,
            "depthVariance": 1,
            "bucketSize": "0.00:10:00",
            "feedTypeId": None
        }
    )
    r.raise_for_status()
    return r.json()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScaleAQ Feeding Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #0f1923; color: #e0e0e0; padding: 24px; }
        h1 { color: #4fc3f7; margin-bottom: 8px; font-size: 1.8rem; }
        .subtitle { color: #90a4ae; margin-bottom: 24px; font-size: 0.9rem; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .card { background: #1e2d3d; border-radius: 10px; padding: 20px; border-left: 4px solid #4fc3f7; }
        .card h3 { font-size: 0.85rem; color: #90a4ae; margin-bottom: 8px; }
        .card .value { font-size: 1.8rem; font-weight: bold; color: #4fc3f7; }
        .card .unit { font-size: 0.8rem; color: #90a4ae; }
        .chart-box { background: #1e2d3d; border-radius: 10px; padding: 20px; margin-bottom: 24px; }
        .chart-box h2 { color: #4fc3f7; margin-bottom: 16px; font-size: 1.1rem; }
        .sites { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; }
        .site-card { background: #1e2d3d; border-radius: 10px; padding: 16px; }
        .site-card h3 { color: #4fc3f7; margin-bottom: 8px; }
        .site-card p { color: #90a4ae; font-size: 0.85rem; }
        .error { background: #3d1e1e; border-left: 4px solid #ef5350; border-radius: 10px; padding: 20px; color: #ef9a9a; }
        .date-controls { display: flex; gap: 12px; align-items: center; margin-bottom: 24px; flex-wrap: wrap; }
        .date-controls input { background: #1e2d3d; border: 1px solid #37474f; color: #e0e0e0; padding: 8px 12px; border-radius: 6px; font-size: 0.9rem; }
        .date-controls button { background: #4fc3f7; color: #0f1923; border: none; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .date-controls button:hover { background: #81d4fa; }
    </style>
</head>
<body>
    <h1>🐟 ScaleAQ Feeding Dashboard</h1>
    <p class="subtitle">Fôrdata fra ScaleAQ</p>

    {% if error %}
    <div class="error">
        <strong>Feil:</strong> {{ error }}
    </div>
    {% else %}

    <div class="cards">
        <div class="card">
            <h3>Totalt fôr i dag</h3>
            <div class="value" id="totalFeed">–</div>
            <div class="unit">kg</div>
        </div>
        <div class="card">
            <h3>Antall lokaliteter</h3>
            <div class="value">{{ site_count }}</div>
            <div class="unit">stk</div>
        </div>
        <div class="card">
            <h3>Datapunkter</h3>
            <div class="value" id="dataPoints">–</div>
            <div class="unit">10-min bøtter</div>
        </div>
    </div>

    <div class="chart-box">
        <h2>📈 Fôrmengde over tid (10-min bøtter)</h2>
        <canvas id="feedChart" height="80"></canvas>
    </div>

    <h2 style="color:#4fc3f7; margin-bottom:16px;">Lokaliteter</h2>
    <div class="sites">
        {% for site in sites %}
        <div class="site-card">
            <h3>{{ site.get('name', 'Ukjent') }}</h3>
            <p>ID: {{ site.get('id', '–') }}</p>
        </div>
        {% endfor %}
    </div>

    <script>
        const feedData = {{ feed_data | tojson }};
        
        const labels = feedData.map(d => {
            const t = new Date(d.time || d.timestamp || d.fromTime || '');
            return t.toLocaleTimeString('no-NO', {hour: '2-digit', minute: '2-digit'});
        });
        const amounts = feedData.map(d => d.feedAmount || d.FeedAmount || d.value || 0);
        
        const total = amounts.reduce((a, b) => a + b, 0);
        document.getElementById('totalFeed').textContent = Math.round(total).toLocaleString('no-NO');
        document.getElementById('dataPoints').textContent = feedData.length;

        new Chart(document.getElementById('feedChart'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Fôrmengde (kg)',
                    data: amounts,
                    borderColor: '#4fc3f7',
                    backgroundColor: 'rgba(79, 195, 247, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: '#e0e0e0' } } },
                scales: {
                    x: { ticks: { color: '#90a4ae' }, grid: { color: '#263238' } },
                    y: { ticks: { color: '#90a4ae' }, grid: { color: '#263238' } }
                }
            }
        });
    </script>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def dashboard():
    try:
        token = get_token()
        company = get_sites(token)

        sites = company.get("sites", []) if isinstance(company, dict) else []
        site_ids = [s["id"] for s in sites if "id" in s]
        unit_ids = []
        for site in sites:
            for unit in site.get("units", []):
                if "id" in unit:
                    unit_ids.append(unit["id"])

        today = datetime.utcnow().date()
        from_time = f"{today}T00:00:00Z"
        to_time = f"{today}T23:59:59Z"

        feed_data = []
        if site_ids:
            result = get_feed_data(token, site_ids, unit_ids, from_time, to_time)
            feed_data = result if isinstance(result, list) else result.get("data", [])

        return render_template_string(DASHBOARD_HTML,
            sites=sites,
            site_count=len(sites),
            feed_data=feed_data,
            error=None
        )
    except Exception as e:
        return render_template_string(DASHBOARD_HTML,
            sites=[], site_count=0, feed_data=[], error=str(e)
        )

@app.route("/api/feed")
def api_feed():
    try:
        token = get_token()
        company = get_sites(token)
        sites = company.get("sites", []) if isinstance(company, dict) else []
        site_ids = [s["id"] for s in sites if "id" in s]
        unit_ids = [u["id"] for s in sites for u in s.get("units", []) if "id" in u]
        today = datetime.utcnow().date()
        data = get_feed_data(token, site_ids, unit_ids, f"{today}T00:00:00Z", f"{today}T23:59:59Z")
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
