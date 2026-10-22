"""
Jayraldine's Catering AI Copilot & Financial Advisor Server
Enhanced with:
- /api/reports?timeframe=daily|weekly|monthly|yearly&target=...
- /api/expense-burn (Stop Spending Alert & Budget Guardrail)
- /api/calculate-custom-cost (The Cost of Everything Profit Calculator)
- Real database integration (jayraldines_live.db)
"""

import http.server
import socketserver
import json
import urllib.parse
from pathlib import Path
from jayraldines_advisor import JayraldinesAdvisor

PORT = 8080
BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"

advisor = JayraldinesAdvisor()

class JayraldineAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/health":
            self._send_json({"status": "healthy", "service": "Jayraldine's Catering Financial Advisor AI"})
            return

        if path == "/api/kpis":
            kpis = advisor.get_executive_kpis()
            self._send_json(kpis)
            return

        if path == "/api/reports":
            timeframe = query_params.get("timeframe", ["daily"])[0]
            target = query_params.get("target", [None])[0]
            report = advisor.get_periodic_report(timeframe=timeframe, target=target)
            self._send_json(report)
            return

        if path == "/api/expense-burn":
            burn = advisor.audit_expense_burn()
            self._send_json(burn)
            return

        if path == "/api/receivables":
            rec = advisor.get_accounts_receivable()
            self._send_json({"receivables": rec, "count": len(rec)})
            return

        if path == "/api/food-sets":
            sets = advisor.get_food_sets_unit_economics()
            self._send_json({"sets": sets, "count": len(sets)})
            return

        if path == "/api/events":
            with advisor.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT bk_id, bk_booking_ref, bk_customer_name, bk_event_date, bk_occasion,
                           bk_pax, bk_total_amount, bk_amount_paid,
                           (bk_total_amount - bk_amount_paid) as balance,
                           bk_venue, bk_status
                    FROM bookings
                    WHERE bk_status IN ('CONFIRMED', 'COMPLETED')
                    ORDER BY bk_event_date DESC
                    LIMIT 100
                """)
                columns = [c[0] for c in cur.description]
                rows = [dict(zip(columns, r)) for r in cur.fetchall()]
                self._send_json({"events": rows, "count": len(rows)})
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/calculate-custom-cost":
            result = advisor.calculate_custom_cost(payload)
            self._send_json(result)
            return

        if path == "/api/simulate-quote":
            pax = int(payload.get("pax", 60))
            price = float(payload.get("price", 33500.0))
            occasion = payload.get("occasion", "Party")
            has_lechon = bool(payload.get("has_lechon", False))
            hours = int(payload.get("venue_hours", 3))
            offsite = bool(payload.get("is_offsite", False))

            simulation = advisor.simulate_quote(
                pax=pax,
                package_price=price,
                occasion=occasion,
                has_lechon=has_lechon,
                venue_hours=hours,
                is_offsite=offsite
            )
            self._send_json(simulation)
            return

        if path == "/api/query":
            question = payload.get("question", "").strip()
            if not question:
                self._send_json({"error": "Question is required"}, status=400)
                return

            response = advisor.ask_advisor(question)
            self._send_json(response)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def _send_json(self, data: dict, status: int = 200):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

def start_server(port=PORT):
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), JayraldineAPIHandler) as httpd:
        print(f"Jayraldine's Financial Advisor Server listening on http://localhost:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    start_server()
