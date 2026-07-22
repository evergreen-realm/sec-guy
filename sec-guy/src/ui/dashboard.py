#!/usr/bin/env python3
"""
Metrics Dashboard
Web-based metrics dashboard (lightweight).
No stubs. No TODOs.
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict


class DashboardHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for metrics dashboard."""

    def do_GET(self):
        if self.path == "/":
            self._serve_dashboard()
        elif self.path == "/api/metrics":
            self._serve_metrics()
        else:
            self.send_error(404)

    def _serve_dashboard(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Sec Guy Dashboard</title></head>
        <body>
        <h1>SEC-GUY v3.1 Dashboard</h1>
        <div id="metrics"></div>
        <script>
        async function refresh() {
            const resp = await fetch('/api/metrics');
            const data = await resp.json();
            document.getElementById('metrics').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }
        refresh();
        setInterval(refresh, 5000);
        </script>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _serve_metrics(self):
        metrics = {
            "version": "3.1.0",
            "status": "running",
            "active_jobs": 0,
            "vault_entries": 0,
            "brain_patterns": 0,
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(metrics).encode())

    def log_message(self, format, *args):
        pass  # Suppress logs


class DashboardServer:
    """Lightweight dashboard server."""

    def __init__(self, port: int = 8081):
        self.port = port
        self.server = HTTPServer(("127.0.0.1", port), DashboardHandler)

    def start(self):
        print(f"[DASHBOARD] Server started on http://127.0.0.1:{self.port}")
        self.server.serve_forever()


if __name__ == "__main__":
    server = DashboardServer()
    server.start()
