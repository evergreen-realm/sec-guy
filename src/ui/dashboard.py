"""
Web dashboard for SEC-GUY metrics (using Flask or simple HTTP server).
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
from typing import Dict

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
        if self.path == "/api/metrics":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            metrics = MetricsCollector().get()
            self.wfile.write(json.dumps(metrics).encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_dashboard(port: int = 8081):
    server = HTTPServer(('', port), MetricsHandler)
    print(f"Dashboard running on http://localhost:{port}")
    server.serve_forever()
