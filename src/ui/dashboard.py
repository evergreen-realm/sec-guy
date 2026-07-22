"""
Web dashboard for SEC-GUY metrics.
Provides a modern full-screen HTML UI at http://localhost:8081 and JSON API at /api/metrics.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
from typing import Dict

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEC-GUY v3.1 — Recovery Metrics Dashboard</title>
    <style>
        :root {
            --bg-color: #0b0e14;
            --card-bg: #151a23;
            --border-color: #262c36;
            --text-main: #9da7b3;
            --text-heading: #ffffff;
            --accent-cyan: #58a6ff;
            --accent-green: #3fb950;
            --accent-purple: #bc8cff;
            --accent-yellow: #d29922;
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 30px 40px;
            min-height: 100vh;
            display: flex;
            justify-content: center;
        }

        .container {
            max-width: 1600px;
            width: 95%;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 24px;
            margin-bottom: 36px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .logo {
            font-size: 36px;
        }

        h1 {
            margin: 0;
            font-size: 32px;
            color: var(--text-heading);
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .subtitle {
            font-size: 15px;
            color: #8b949e;
            margin-top: 6px;
        }

        .status-badge {
            background-color: rgba(63, 185, 80, 0.15);
            color: var(--accent-green);
            border: 1px solid rgba(63, 185, 80, 0.4);
            padding: 8px 20px;
            border-radius: 24px;
            font-size: 14px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .dot {
            width: 10px;
            height: 10px;
            background-color: var(--accent-green);
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 10px var(--accent-green);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 28px;
            margin-bottom: 40px;
        }

        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            transition: transform 0.2s, border-color 0.2s;
        }

        .card:hover {
            transform: translateY(-3px);
            border-color: var(--accent-cyan);
        }

        .card-title {
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #8b949e;
            font-weight: 600;
            margin-bottom: 16px;
        }

        .card-value {
            font-size: 52px;
            font-weight: 700;
            color: var(--text-heading);
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            line-height: 1.1;
        }

        .card-desc {
            font-size: 14px;
            color: #8b949e;
            margin-top: 12px;
        }

        .json-box {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 28px;
        }

        .json-box h3 {
            margin-top: 0;
            font-size: 18px;
            color: var(--text-heading);
            margin-bottom: 16px;
        }

        pre {
            background-color: #070a0f;
            padding: 24px;
            border-radius: 12px;
            overflow-x: auto;
            color: var(--accent-cyan);
            font-size: 15px;
            line-height: 1.5;
            margin: 0;
            border: 1px solid #1c212a;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">
                <span class="logo">🛡️</span>
                <div>
                    <h1>SEC-GUY v3.1</h1>
                    <div class="subtitle">Autonomous Data Recovery & Password Orchestration</div>
                </div>
            </div>
            <div class="status-badge">
                <span class="dot"></span> SYSTEM ONLINE
            </div>
        </header>

        <div class="grid">
            <div class="card">
                <div class="card-title">Total Recovery Jobs</div>
                <div class="card-value" id="jobs_total">0</div>
                <div class="card-desc">Submitted to orchestrator</div>
            </div>
            <div class="card">
                <div class="card-title">Active Operations</div>
                <div class="card-value" style="color: var(--accent-cyan);" id="active_jobs">0</div>
                <div class="card-desc">Running in memory / Redis</div>
            </div>
            <div class="card">
                <div class="card-title">Candidates Generated</div>
                <div class="card-value" style="color: var(--accent-purple);" id="candidates_generated">0</div>
                <div class="card-desc">LLM & Profiler password space</div>
            </div>
            <div class="card">
                <div class="card-title">Successful Recoveries</div>
                <div class="card-value" style="color: var(--accent-green);" id="jobs_success">0</div>
                <div class="card-desc">Decrypted & vaulted</div>
            </div>
            <div class="card">
                <div class="card-title">Failed / Exhausted</div>
                <div class="card-value" style="color: var(--accent-yellow);" id="jobs_failed">0</div>
                <div class="card-desc">Key space exhausted</div>
            </div>
            <div class="card">
                <div class="card-title">System Uptime</div>
                <div class="card-value" style="font-size: 38px; color: var(--accent-cyan);" id="uptime_seconds">0s</div>
                <div class="card-desc">Metrics collector runtime</div>
            </div>
        </div>

        <div class="json-box">
            <h3>Raw Telemetry Payload (<a href="/api/metrics" target="_blank" style="color: var(--accent-cyan); text-decoration: none;">/api/metrics</a>)</h3>
            <pre id="json-raw">Loading telemetry...</pre>
        </div>
    </div>

    <script>
        function formatUptime(seconds) {
            const hrs = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            if (hrs > 0) return `${hrs}h ${mins}m ${secs}s`;
            if (mins > 0) return `${mins}m ${secs}s`;
            return `${secs}s`;
        }

        async function fetchMetrics() {
            try {
                const res = await fetch('/api/metrics');
                const data = await res.json();
                
                document.getElementById('jobs_total').innerText = data.jobs_total || 0;
                document.getElementById('active_jobs').innerText = data.active_jobs || 0;
                document.getElementById('candidates_generated').innerText = (data.candidates_generated || 0).toLocaleString();
                document.getElementById('jobs_success').innerText = data.jobs_success || 0;
                document.getElementById('jobs_failed').innerText = data.jobs_failed || 0;
                document.getElementById('uptime_seconds').innerText = formatUptime(data.uptime_seconds || 0);
                
                document.getElementById('json-raw').innerText = JSON.stringify(data, null, 2);
            } catch (err) {
                console.error("Error updating telemetry:", err);
            }
        }

        fetchMetrics();
        setInterval(fetchMetrics, 2000);
    </script>
</body>
</html>
"""


class MetricsCollector:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data = {
                "jobs_total": 0,
                "jobs_success": 0,
                "jobs_failed": 0,
                "candidates_generated": 0,
                "uptime_seconds": 0,
                "active_jobs": 0,
            }
            cls._instance.start_time = time.time()
        return cls._instance

    def update(self, key: str, value: int = 1):
        if key in self.data:
            self.data[key] += value

    def get(self) -> Dict:
        self.data["uptime_seconds"] = int(time.time() - self.start_time)
        return self.data


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif self.path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            metrics = MetricsCollector().get()
            self.wfile.write(json.dumps(metrics).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def start_dashboard(port: int = 8081):
    server = HTTPServer(("", port), MetricsHandler)
    print(f"SEC-GUY Dashboard running on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    start_dashboard(8081)
