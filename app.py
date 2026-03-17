import os
import sqlite3
from datetime import date, datetime

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "sustainability.db"))

EMISSION_FACTORS = {
    "feed_kg": 1.60,  # kg CO2e per kg feed
    "diesel_l": 2.68,  # kg CO2e per liter diesel
    "electricity_kwh": 0.018,  # kg CO2e per kWh (nordic grid estimate)
}


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sustainability_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL,
                site_name TEXT NOT NULL,
                region TEXT DEFAULT '',
                feed_kg REAL DEFAULT 0,
                harvested_kg REAL DEFAULT 0,
                mortality_kg REAL DEFAULT 0,
                diesel_l REAL DEFAULT 0,
                electricity_kwh REAL DEFAULT 0,
                freshwater_m3 REAL DEFAULT 0,
                plastic_waste_kg REAL DEFAULT 0,
                net_waste_kg REAL DEFAULT 0,
                hse_incidents INTEGER DEFAULT 0,
                lost_time_injuries INTEGER DEFAULT 0,
                local_employees INTEGER DEFAULT 0,
                total_employees INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )


def seed_sample_data():
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM sustainability_reports").fetchone()["c"]
        if count > 0:
            return

        sample_rows = [
            ("2026-03-10", "Hitra Nord", "Midt", 89000, 72000, 1800, 1300, 26000, 420, 180, 70, 1, 0, 92, 116, "Stabil drift."),
            ("2026-03-11", "Frøya Vest", "Midt", 94000, 76000, 1700, 1450, 28100, 460, 210, 90, 0, 0, 88, 113, "Skiftet not på merd C."),
            ("2026-03-12", "Alta Sør", "Nord", 81000, 64500, 2300, 1700, 24500, 510, 240, 120, 2, 0, 56, 82, "Kortvarig algehendelse."),
            ("2026-03-13", "Senja Øst", "Nord", 87000, 69000, 1600, 1390, 25200, 390, 150, 75, 0, 0, 61, 84, "Lav dødelighet, god fôrutnyttelse."),
        ]

        for row in sample_rows:
            conn.execute(
                """
                INSERT INTO sustainability_reports (
                    report_date, site_name, region, feed_kg, harvested_kg, mortality_kg, diesel_l,
                    electricity_kwh, freshwater_m3, plastic_waste_kg, net_waste_kg, hse_incidents,
                    lost_time_injuries, local_employees, total_employees, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*row, datetime.utcnow().isoformat(timespec="seconds")),
            )


def parse_float(raw_value):
    if raw_value is None:
        return 0.0
    value = str(raw_value).strip().replace(",", ".")
    if value == "":
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def parse_int(raw_value):
    try:
        return int(float(str(raw_value).strip() or "0"))
    except ValueError:
        return 0


def parse_date(raw_value, fallback):
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return fallback


def list_sites():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT site_name FROM sustainability_reports ORDER BY site_name"
        ).fetchall()
    return [row["site_name"] for row in rows]


def fetch_reports(start_date, end_date, site_name):
    query = """
        SELECT *
        FROM sustainability_reports
        WHERE report_date BETWEEN ? AND ?
    """
    params = [start_date.isoformat(), end_date.isoformat()]
    if site_name:
        query += " AND site_name = ?"
        params.append(site_name)
    query += " ORDER BY report_date DESC, id DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def build_trend(start_date, end_date, site_name):
    query = """
        SELECT
            report_date,
            SUM(feed_kg) AS feed_kg,
            SUM(harvested_kg) AS harvested_kg,
            SUM(diesel_l) AS diesel_l,
            SUM(electricity_kwh) AS electricity_kwh
        FROM sustainability_reports
        WHERE report_date BETWEEN ? AND ?
    """
    params = [start_date.isoformat(), end_date.isoformat()]
    if site_name:
        query += " AND site_name = ?"
        params.append(site_name)
    query += " GROUP BY report_date ORDER BY report_date"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    trend = []
    for row in rows:
        emissions = (
            row["feed_kg"] * EMISSION_FACTORS["feed_kg"]
            + row["diesel_l"] * EMISSION_FACTORS["diesel_l"]
            + row["electricity_kwh"] * EMISSION_FACTORS["electricity_kwh"]
        )
        trend.append(
            {
                "date": row["report_date"],
                "feed_kg": round(row["feed_kg"], 2),
                "harvested_kg": round(row["harvested_kg"], 2),
                "emissions_kg_co2e": round(emissions, 2),
            }
        )
    return trend


def build_summary(reports):
    totals = {
        "feed_kg": 0.0,
        "harvested_kg": 0.0,
        "mortality_kg": 0.0,
        "diesel_l": 0.0,
        "electricity_kwh": 0.0,
        "freshwater_m3": 0.0,
        "plastic_waste_kg": 0.0,
        "net_waste_kg": 0.0,
        "hse_incidents": 0,
        "lost_time_injuries": 0,
        "local_employees": 0,
        "total_employees": 0,
    }

    for report in reports:
        for key in [
            "feed_kg",
            "harvested_kg",
            "mortality_kg",
            "diesel_l",
            "electricity_kwh",
            "freshwater_m3",
            "plastic_waste_kg",
            "net_waste_kg",
        ]:
            totals[key] += float(report.get(key) or 0)
        totals["hse_incidents"] += int(report.get("hse_incidents") or 0)
        totals["lost_time_injuries"] += int(report.get("lost_time_injuries") or 0)
        totals["local_employees"] += int(report.get("local_employees") or 0)
        totals["total_employees"] += int(report.get("total_employees") or 0)

    feed_emissions = totals["feed_kg"] * EMISSION_FACTORS["feed_kg"]
    diesel_emissions = totals["diesel_l"] * EMISSION_FACTORS["diesel_l"]
    power_emissions = totals["electricity_kwh"] * EMISSION_FACTORS["electricity_kwh"]
    total_emissions = feed_emissions + diesel_emissions + power_emissions

    fcr = totals["feed_kg"] / totals["harvested_kg"] if totals["harvested_kg"] else 0.0
    mortality_rate = (
        (totals["mortality_kg"] / (totals["harvested_kg"] + totals["mortality_kg"])) * 100
        if (totals["harvested_kg"] + totals["mortality_kg"]) > 0
        else 0.0
    )
    emission_intensity = (
        total_emissions / totals["harvested_kg"] if totals["harvested_kg"] else 0.0
    )
    local_share = (
        (totals["local_employees"] / totals["total_employees"]) * 100
        if totals["total_employees"] > 0
        else 0.0
    )

    return {
        "totals": {k: round(v, 2) if isinstance(v, float) else v for k, v in totals.items()},
        "co2e_total_kg": round(total_emissions, 2),
        "co2e_breakdown": {
            "feed_kg": round(feed_emissions, 2),
            "diesel_kg": round(diesel_emissions, 2),
            "electricity_kg": round(power_emissions, 2),
        },
        "fcr": round(fcr, 3),
        "mortality_rate_pct": round(mortality_rate, 2),
        "emission_intensity_kg_per_kg": round(emission_intensity, 3),
        "local_share_pct": round(local_share, 2),
    }


def insert_report(form):
    report_date = parse_date(form.get("report_date"), date.today()).isoformat()
    site_name = (form.get("site_name") or "").strip()
    if not site_name:
        return False

    payload = (
        report_date,
        site_name,
        (form.get("region") or "").strip(),
        parse_float(form.get("feed_kg")),
        parse_float(form.get("harvested_kg")),
        parse_float(form.get("mortality_kg")),
        parse_float(form.get("diesel_l")),
        parse_float(form.get("electricity_kwh")),
        parse_float(form.get("freshwater_m3")),
        parse_float(form.get("plastic_waste_kg")),
        parse_float(form.get("net_waste_kg")),
        parse_int(form.get("hse_incidents")),
        parse_int(form.get("lost_time_injuries")),
        parse_int(form.get("local_employees")),
        parse_int(form.get("total_employees")),
        (form.get("notes") or "").strip(),
        datetime.utcnow().isoformat(timespec="seconds"),
    )

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sustainability_reports (
                report_date, site_name, region, feed_kg, harvested_kg, mortality_kg, diesel_l,
                electricity_kwh, freshwater_m3, plastic_waste_kg, net_waste_kg, hse_incidents,
                lost_time_injuries, local_employees, total_employees, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            payload,
        )
    return True


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cermaq Bærekraftsrapportering</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #0f1923; color: #e0e0e0; padding: 24px; }
        h1 { color: #66d9ff; margin-bottom: 8px; font-size: 1.9rem; }
        .subtitle { color: #9eb0bf; margin-bottom: 20px; font-size: 0.95rem; }
        .saved { background: #113920; color: #9ff0bd; border-left: 4px solid #2ecc71; padding: 12px 14px; border-radius: 8px; margin-bottom: 16px; }
        .filters, .panel { background: #1b2a39; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
        .card { background: #213548; border-radius: 10px; padding: 14px; border-left: 4px solid #66d9ff; }
        .card h3 { color: #9eb0bf; font-size: 0.82rem; margin-bottom: 7px; }
        .card .value { color: #66d9ff; font-size: 1.5rem; font-weight: bold; }
        .card .unit { color: #9eb0bf; font-size: 0.8rem; }
        .section-title { color: #66d9ff; margin-bottom: 10px; font-size: 1.15rem; }
        form .row { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; margin-bottom: 10px; }
        label { display: block; font-size: 0.82rem; color: #b8c4ce; margin-bottom: 4px; }
        input, select, textarea {
            width: 100%; background: #0f1923; color: #e0e0e0; border: 1px solid #31475a;
            border-radius: 7px; padding: 8px 10px; font-size: 0.9rem;
        }
        textarea { min-height: 68px; resize: vertical; }
        button {
            border: none; border-radius: 7px; background: #66d9ff; color: #0f1923;
            padding: 9px 16px; cursor: pointer; font-weight: bold;
        }
        button:hover { background: #90e5ff; }
        table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
        th, td { padding: 8px; border-bottom: 1px solid #2e4253; text-align: left; }
        th { color: #9eb0bf; font-weight: 600; }
        .muted { color: #9eb0bf; font-size: 0.82rem; }
        .chart-wrap { margin-top: 8px; }
    </style>
</head>
<body>
    <h1>🌊 Cermaq bærekraftsrapportering</h1>
    <p class="subtitle">Miljø, sosial og driftsdata for lokaliteter med automatisk KPI-beregning.</p>

    {% if saved %}
    <div class="saved">Rapport lagret.</div>
    {% endif %}

    <div class="filters">
        <form method="get">
            <div class="row">
                <div>
                    <label for="start">Fra dato</label>
                    <input type="date" id="start" name="start" value="{{ filters.start }}">
                </div>
                <div>
                    <label for="end">Til dato</label>
                    <input type="date" id="end" name="end" value="{{ filters.end }}">
                </div>
                <div>
                    <label for="site">Lokalitet</label>
                    <select id="site" name="site">
                        <option value="">Alle lokaliteter</option>
                        {% for site_name in sites %}
                        <option value="{{ site_name }}" {% if site_name == filters.site %}selected{% endif %}>{{ site_name }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
            <button type="submit">Oppdater rapport</button>
        </form>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Totale utslipp</h3>
            <div class="value">{{ summary.co2e_total_kg }}</div>
            <div class="unit">kg CO2e</div>
        </div>
        <div class="card">
            <h3>Utslippsintensitet</h3>
            <div class="value">{{ summary.emission_intensity_kg_per_kg }}</div>
            <div class="unit">kg CO2e / kg slaktet fisk</div>
        </div>
        <div class="card">
            <h3>FCR</h3>
            <div class="value">{{ summary.fcr }}</div>
            <div class="unit">kg fôr / kg slaktet fisk</div>
        </div>
        <div class="card">
            <h3>Dødelighetsrate</h3>
            <div class="value">{{ summary.mortality_rate_pct }}%</div>
            <div class="unit">andel av biomasse</div>
        </div>
        <div class="card">
            <h3>HMS-hendelser</h3>
            <div class="value">{{ summary.totals.hse_incidents }}</div>
            <div class="unit">i valgt periode</div>
        </div>
        <div class="card">
            <h3>Lokal andel ansatte</h3>
            <div class="value">{{ summary.local_share_pct }}%</div>
            <div class="unit">{{ summary.totals.local_employees }} av {{ summary.totals.total_employees }}</div>
        </div>
    </div>

    <div class="panel">
        <h2 class="section-title">Trend: utslipp og slaktet volum</h2>
        <div class="chart-wrap">
            <canvas id="trendChart" height="90"></canvas>
        </div>
        <p class="muted" style="margin-top:8px;">
            Utslipp fordelt på fôr ({{ summary.co2e_breakdown.feed_kg }}), diesel ({{ summary.co2e_breakdown.diesel_kg }}) og strøm ({{ summary.co2e_breakdown.electricity_kg }}) i kg CO2e.
        </p>
    </div>

    <div class="panel">
        <h2 class="section-title">Ny rapport</h2>
        <form method="post">
            <input type="hidden" name="start" value="{{ filters.start }}">
            <input type="hidden" name="end" value="{{ filters.end }}">
            <input type="hidden" name="site_filter" value="{{ filters.site }}">
            <div class="row">
                <div><label>Dato</label><input type="date" name="report_date" value="{{ today }}" required></div>
                <div><label>Lokalitet</label><input type="text" name="site_name" placeholder="f.eks. Hitra Nord" required></div>
                <div><label>Region</label><input type="text" name="region" placeholder="Midt / Nord"></div>
            </div>
            <div class="row">
                <div><label>Fôr (kg)</label><input type="number" step="0.01" name="feed_kg"></div>
                <div><label>Slaktet fisk (kg)</label><input type="number" step="0.01" name="harvested_kg"></div>
                <div><label>Dødelighet (kg)</label><input type="number" step="0.01" name="mortality_kg"></div>
            </div>
            <div class="row">
                <div><label>Diesel (liter)</label><input type="number" step="0.01" name="diesel_l"></div>
                <div><label>Strøm (kWh)</label><input type="number" step="0.01" name="electricity_kwh"></div>
                <div><label>Ferskvann (m3)</label><input type="number" step="0.01" name="freshwater_m3"></div>
            </div>
            <div class="row">
                <div><label>Plastavfall (kg)</label><input type="number" step="0.01" name="plastic_waste_kg"></div>
                <div><label>Notavfall (kg)</label><input type="number" step="0.01" name="net_waste_kg"></div>
                <div><label>HMS-hendelser</label><input type="number" step="1" min="0" name="hse_incidents"></div>
            </div>
            <div class="row">
                <div><label>Fraværsskader</label><input type="number" step="1" min="0" name="lost_time_injuries"></div>
                <div><label>Lokale ansatte</label><input type="number" step="1" min="0" name="local_employees"></div>
                <div><label>Totalt ansatte</label><input type="number" step="1" min="0" name="total_employees"></div>
            </div>
            <div class="row">
                <div style="grid-column: 1 / -1;">
                    <label>Notater</label>
                    <textarea name="notes" placeholder="Hendelser, tiltak, forbedringer..."></textarea>
                </div>
            </div>
            <button type="submit">Lagre rapport</button>
        </form>
    </div>

    <div class="panel">
        <h2 class="section-title">Siste registreringer</h2>
        <table>
            <thead>
                <tr>
                    <th>Dato</th>
                    <th>Lokalitet</th>
                    <th>Fôr (kg)</th>
                    <th>Slaktet (kg)</th>
                    <th>CO2e (kg)</th>
                    <th>HMS</th>
                </tr>
            </thead>
            <tbody>
                {% for row in reports[:20] %}
                <tr>
                    <td>{{ row.report_date }}</td>
                    <td>{{ row.site_name }}</td>
                    <td>{{ row.feed_kg }}</td>
                    <td>{{ row.harvested_kg }}</td>
                    <td>{{ row.row_co2e_kg }}</td>
                    <td>{{ row.hse_incidents }}</td>
                </tr>
                {% endfor %}
                {% if reports|length == 0 %}
                <tr><td colspan="6">Ingen rapporter i valgt periode.</td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>

    <script>
        const trend = {{ trend | tojson }};
        const labels = trend.map(item => item.date);
        const emissions = trend.map(item => item.emissions_kg_co2e);
        const harvested = trend.map(item => item.harvested_kg);

        new Chart(document.getElementById('trendChart'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Utslipp (kg CO2e)',
                        data: emissions,
                        borderColor: '#66d9ff',
                        backgroundColor: 'rgba(102, 217, 255, 0.15)',
                        fill: true,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Slaktet volum (kg)',
                        data: harvested,
                        borderColor: '#8bc34a',
                        backgroundColor: 'rgba(139, 195, 74, 0.1)',
                        fill: false,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                plugins: { legend: { labels: { color: '#e0e0e0' } } },
                scales: {
                    x: { ticks: { color: '#9eb0bf' }, grid: { color: '#2e4253' } },
                    y: {
                        type: 'linear',
                        position: 'left',
                        ticks: { color: '#9eb0bf' },
                        grid: { color: '#2e4253' }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        ticks: { color: '#9eb0bf' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def dashboard():
    today = date.today()
    month_start = today.replace(day=1)

    if request.method == "POST":
        insert_report(request.form)
        return redirect(
            url_for(
                "dashboard",
                start=request.form.get("start") or month_start.isoformat(),
                end=request.form.get("end") or today.isoformat(),
                site=request.form.get("site_filter") or "",
                saved=1,
            )
        )

    start_date = parse_date(request.args.get("start"), month_start)
    end_date = parse_date(request.args.get("end"), today)
    site = (request.args.get("site") or "").strip()
    if end_date < start_date:
        end_date = start_date

    reports = fetch_reports(start_date, end_date, site)
    for row in reports:
        row["row_co2e_kg"] = round(
            row["feed_kg"] * EMISSION_FACTORS["feed_kg"]
            + row["diesel_l"] * EMISSION_FACTORS["diesel_l"]
            + row["electricity_kwh"] * EMISSION_FACTORS["electricity_kwh"],
            2,
        )
    summary = build_summary(reports)
    trend = build_trend(start_date, end_date, site)

    return render_template_string(
        DASHBOARD_HTML,
        reports=reports,
        summary=summary,
        trend=trend,
        sites=list_sites(),
        today=today.isoformat(),
        saved=request.args.get("saved") == "1",
        filters={"start": start_date.isoformat(), "end": end_date.isoformat(), "site": site},
    )


@app.route("/api/summary")
def api_summary():
    today = date.today()
    month_start = today.replace(day=1)
    start_date = parse_date(request.args.get("start"), month_start)
    end_date = parse_date(request.args.get("end"), today)
    site = (request.args.get("site") or "").strip()
    reports = fetch_reports(start_date, end_date, site)

    return jsonify(
        {
            "filters": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "site": site,
            },
            "summary": build_summary(reports),
            "trend": build_trend(start_date, end_date, site),
            "report_count": len(reports),
        }
    )


@app.route("/api/reports")
def api_reports():
    today = date.today()
    month_start = today.replace(day=1)
    start_date = parse_date(request.args.get("start"), month_start)
    end_date = parse_date(request.args.get("end"), today)
    site = (request.args.get("site") or "").strip()
    limit = min(parse_int(request.args.get("limit") or "100"), 500)

    reports = fetch_reports(start_date, end_date, site)
    return jsonify({"count": len(reports), "items": reports[:limit]})


init_db()
seed_sample_data()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
