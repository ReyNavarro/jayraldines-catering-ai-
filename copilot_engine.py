"""
Catering Business Intelligence Copilot Engine
Translates natural language questions into safe SQL, executes against the catering database,
and produces executive business insights, key metrics, and recommended chart visualizations.
Supports both LLM APIs (Gemini/OpenAI) and a rich built-in semantic intent engine.
"""

import sqlite3
import re
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = Path(__file__).parent / "catering_bi.db"

# Schema context for Text-to-SQL LLM prompts
CATERING_SCHEMA_DOCS = """
Catering Database Schema & Core Business Logic:

Views:
- v_event_profitability (
    event_id, event_name, event_date, event_month (YYYY-MM), event_type ('Wedding','Corporate Gala','Cocktail Reception','Corporate Lunch','Charity Fundraiser','Private Dinner'),
    service_style ('Plated','Buffet','Family Style','Stations','Passed Hors d'oeuvres'),
    guest_count, client_name, company_name, client_type, venue_name, kitchen_type,
    quoted_price, actual_revenue, actual_food_bev_cost, actual_labor_cost, actual_overhead_cost,
    total_budgeted_expenses, total_actual_expenses, gross_profit, gross_margin_pct,
    food_cost_pct, labor_cost_pct, prime_cost_pct (food_cost_pct + labor_cost_pct),
    revenue_per_guest, cost_per_guest, profit_per_guest, total_cost_overrun
  )
- v_menu_performance (
    item_id, item_name, category_name, recipe_cost, selling_price, target_margin_pct,
    food_cost_pct, events_featured_in, total_portions_ordered, total_revenue_generated,
    total_food_cost_incurred, total_item_profit
  )

Tables:
- events (event_id, client_id, venue_id, event_name, event_date, event_type, service_style, guest_count, quoted_price, actual_revenue, status)
- clients (client_id, client_name, company_name, client_type, contact_email, created_at)
- venues (venue_id, venue_name, kitchen_type, city, preferred_caterer, commission_rate)
- menu_items (item_id, category_id, name, serving_unit, recipe_cost, selling_price, dietary_tags, food_cost_pct)
- menu_categories (category_id, category_name, target_food_cost_pct)
- event_line_items (line_id, event_id, item_id, quantity, unit_cost, unit_price, total_cost, total_price)
- event_expenses (expense_id, event_id, category, budgeted_amount, actual_amount, variance, vendor_or_payee, notes)
  expense categories: 'Food Ingredients', 'Beverage & Bar', 'Kitchen Labor', 'Front of House Service Labor', 'Equipment & Rentals', 'Transportation & Logistics', 'Venue Commission'

Key Catering Benchmarks & Formulas:
- Prime Cost % = (Food & Beverage Costs + Labor Costs) / Actual Revenue. Industry benchmark target is 55% - 65%.
- Gross Margin % = (Actual Revenue - Total Actual Expenses) / Actual Revenue * 100.
- Overrun / Variance = Total Actual Expenses - Total Budgeted Expenses.
"""

class CateringCopilot:
    def __init__(self, db_path: Path = DB_PATH, gemini_api_key: Optional[str] = None):
        self.db_path = db_path
        self.gemini_api_key = gemini_api_key

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_executive_kpis(self) -> Dict[str, Any]:
        """Calculates high-level executive KPIs for the dashboard cards."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    COUNT(event_id) AS total_events,
                    ROUND(SUM(actual_revenue), 2) AS total_revenue,
                    ROUND(SUM(gross_profit), 2) AS total_gross_profit,
                    ROUND(AVG(gross_margin_pct), 1) AS avg_gross_margin_pct,
                    ROUND(AVG(prime_cost_pct), 1) AS avg_prime_cost_pct,
                    ROUND(AVG(food_cost_pct), 1) AS avg_food_cost_pct,
                    ROUND(AVG(labor_cost_pct), 1) AS avg_labor_cost_pct,
                    ROUND(AVG(revenue_per_guest), 2) AS avg_revenue_per_guest,
                    ROUND(SUM(total_cost_overrun), 2) AS total_cost_overrun
                FROM v_event_profitability
            """)
            row = cur.fetchone()
            
            # Count of events with cost overruns
            cur.execute("SELECT COUNT(*) FROM v_event_profitability WHERE total_cost_overrun > 500")
            overrun_count = cur.fetchone()[0]

            # Highest margin event type
            cur.execute("""
                SELECT event_type, ROUND(AVG(gross_margin_pct), 1) as avg_margin
                FROM v_event_profitability
                GROUP BY event_type
                ORDER BY avg_margin DESC
                LIMIT 1
            """)
            top_type = cur.fetchone()

        return {
            "total_events": row["total_events"] or 0,
            "total_revenue": row["total_revenue"] or 0.0,
            "total_gross_profit": row["total_gross_profit"] or 0.0,
            "avg_gross_margin_pct": row["avg_gross_margin_pct"] or 0.0,
            "avg_prime_cost_pct": row["avg_prime_cost_pct"] or 0.0,
            "avg_food_cost_pct": row["avg_food_cost_pct"] or 0.0,
            "avg_labor_cost_pct": row["avg_labor_cost_pct"] or 0.0,
            "avg_revenue_per_guest": row["avg_revenue_per_guest"] or 0.0,
            "total_cost_overrun": row["total_cost_overrun"] or 0.0,
            "overrun_events_count": overrun_count,
            "top_margin_event_type": top_type[0] if top_type else "N/A",
            "top_margin_pct": top_type[1] if top_type else 0.0
        }

    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """Safety guardrail: ensures only safe read-only queries are executed."""
        cleaned = sql.strip().strip(";").strip()
        
        # Check for forbidden mutations
        forbidden = [r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b", 
                     r"\bALTER\b", r"\bTRUNCATE\b", r"\bATTACH\b", r"\bDETACH\b",
                     r"\bCREATE\b", r"\bREPLACE\b", r"\bPRAGMA\b", r"\bEXEC\b"]
        for pattern in forbidden:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cmd_name = pattern.replace(r"\b", "")
                return False, f"Security restriction: Mutations and operational commands ({cmd_name}) are forbidden. Read-only queries only."

        # Must start with SELECT or WITH
        if not re.match(r"^(SELECT|WITH)\b", cleaned, re.IGNORECASE):
            return False, "Query must start with SELECT or WITH clause."

        return True, cleaned

    def execute_query(self, sql: str) -> Dict[str, Any]:
        """Executes a safe SQL query and returns column headers and rows."""
        is_safe, message = self.validate_sql(sql)
        if not is_safe:
            return {"error": message, "sql": sql, "rows": [], "columns": []}

        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(message)
                columns = [col[0] for col in cur.description] if cur.description else []
                raw_rows = cur.fetchall()
                rows = [dict(zip(columns, row)) for row in raw_rows]
                return {
                    "sql": message,
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "error": None
                }
        except Exception as e:
            return {
                "error": str(e),
                "sql": sql,
                "columns": [],
                "rows": [],
                "row_count": 0
            }

    def _fallback_semantic_engine(self, question: str) -> Tuple[str, str, str]:
        """
        Built-in deterministic Catering semantic engine.
        Handles natural language business questions reliably without external API dependencies.
        Returns (sql, chart_type, intent_label).
        """
        q = question.lower().strip()

        # 1. Event Type comparison / Profitability by Event Type
        if any(w in q for w in ["event type", "by type", "most profitable type", "margin by event", "compare event"]):
            sql = """
            SELECT 
                event_type,
                COUNT(event_id) AS event_count,
                ROUND(SUM(actual_revenue), 2) AS total_revenue,
                ROUND(AVG(gross_margin_pct), 1) AS avg_gross_margin_pct,
                ROUND(AVG(prime_cost_pct), 1) AS avg_prime_cost_pct,
                ROUND(AVG(revenue_per_guest), 2) AS avg_spend_per_guest
            FROM v_event_profitability
            GROUP BY event_type
            ORDER BY avg_gross_margin_pct DESC;
            """
            return sql, "bar", "Profitability & Margin Comparison by Event Type"

        # 2. Service style comparison (Buffet vs Plated)
        if any(w in q for w in ["service style", "buffet vs plated", "plated vs buffet", "style", "buffet"]):
            sql = """
            SELECT 
                service_style,
                COUNT(event_id) AS total_events,
                ROUND(AVG(gross_margin_pct), 1) AS avg_gross_margin_pct,
                ROUND(AVG(food_cost_pct), 1) AS avg_food_cost_pct,
                ROUND(AVG(labor_cost_pct), 1) AS avg_labor_cost_pct,
                ROUND(AVG(revenue_per_guest), 2) AS avg_revenue_per_guest
            FROM v_event_profitability
            GROUP BY service_style
            ORDER BY avg_gross_margin_pct DESC;
            """
            return sql, "bar", "Performance Breakdown by Service Style"

        # 3. Menu items food cost & margins
        if any(w in q for w in ["menu", "food cost", "recipe cost", "dish", "dishes", "item cost", "unprofitable item", "30%", "32%"]):
            sql = """
            SELECT 
                item_name,
                category_name,
                recipe_cost,
                selling_price,
                food_cost_pct,
                target_margin_pct,
                events_featured_in,
                total_portions_ordered,
                total_item_profit
            FROM v_menu_performance
            ORDER BY food_cost_pct DESC;
            """
            return sql, "table", "Menu Items Food Cost & Realized Margin Analysis"

        # 4. Labor overruns & variance / Venue issues
        if any(w in q for w in ["labor", "overtime", "overrun", "variance", "exceeded", "budget overrun", "kitchen labor"]):
            sql = """
            SELECT 
                e.event_name,
                e.event_type,
                v.venue_name,
                v.kitchen_type,
                exp.category,
                exp.budgeted_amount,
                exp.actual_amount,
                exp.variance,
                exp.notes
            FROM event_expenses exp
            JOIN events e ON exp.event_id = e.event_id
            JOIN venues v ON e.venue_id = v.venue_id
            WHERE exp.variance > 300
            ORDER BY exp.variance DESC
            LIMIT 15;
            """
            return sql, "table", "Significant Expense & Labor Variances (> $300 Overrun)"

        # 5. Venue performance / Kitchen type impact
        if any(w in q for w in ["venue", "venues", "kitchen type", "glasshouse", "vineyard", "location"]):
            sql = """
            SELECT 
                venue_name,
                kitchen_type,
                COUNT(event_id) AS total_events,
                ROUND(AVG(gross_margin_pct), 1) AS avg_gross_margin_pct,
                ROUND(AVG(labor_cost_pct), 1) AS avg_labor_cost_pct,
                ROUND(AVG(total_cost_overrun), 2) AS avg_cost_overrun
            FROM v_event_profitability
            GROUP BY venue_name
            ORDER BY avg_gross_margin_pct DESC;
            """
            return sql, "bar", "Venue Profitability & Labor Impact Comparison"

        # 6. Monthly trend / Revenue over time
        if any(w in q for w in ["month", "trend", "monthly", "over time", "timeline", "seasonality"]):
            sql = """
            SELECT 
                event_month,
                COUNT(event_id) AS total_events,
                ROUND(SUM(actual_revenue), 2) AS monthly_revenue,
                ROUND(SUM(gross_profit), 2) AS monthly_gross_profit,
                ROUND(AVG(gross_margin_pct), 1) AS avg_margin_pct
            FROM v_event_profitability
            GROUP BY event_month
            ORDER BY event_month ASC;
            """
            return sql, "line", "Monthly Catering Revenue & Profitability Trends"

        # 7. Top clients / Client tier
        if any(w in q for w in ["client", "customer", "accounts", "corporate vs private", "spend per client"]):
            sql = """
            SELECT 
                client_name,
                company_name,
                client_type,
                COUNT(event_id) AS total_events,
                ROUND(SUM(actual_revenue), 2) AS total_spend,
                ROUND(AVG(gross_margin_pct), 1) AS avg_margin_pct,
                ROUND(AVG(revenue_per_guest), 2) AS avg_spend_per_guest
            FROM v_event_profitability
            GROUP BY client_name
            ORDER BY total_spend DESC
            LIMIT 10;
            """
            return sql, "bar", "Top Catering Clients by Lifetime Revenue"

        # 8. Prime Cost analysis / Industry benchmark
        if any(w in q for w in ["prime cost", "benchmark", "ratio", "cost ratio", "food and labor"]):
            sql = """
            SELECT 
                event_type,
                ROUND(AVG(food_cost_pct), 1) AS avg_food_cost_pct,
                ROUND(AVG(labor_cost_pct), 1) AS avg_labor_cost_pct,
                ROUND(AVG(prime_cost_pct), 1) AS avg_prime_cost_pct,
                ROUND(AVG(gross_margin_pct), 1) AS avg_gross_margin_pct
            FROM v_event_profitability
            GROUP BY event_type
            ORDER BY avg_prime_cost_pct ASC;
            """
            return sql, "bar", "Prime Cost Breakdown (Food % + Labor %) vs 60% Benchmark"

        # Default: Top profitable events
        sql = """
        SELECT 
            event_name,
            event_type,
            guest_count,
            actual_revenue,
            gross_profit,
            gross_margin_pct,
            prime_cost_pct,
            revenue_per_guest
        FROM v_event_profitability
        ORDER BY gross_profit DESC
        LIMIT 10;
        """
        return sql, "table", "Top 10 Most Profitable Catering Events"

    def ask(self, question: str, custom_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Main query entry point.
        Uses LLM if API key is provided, otherwise falls back to rich semantic engine.
        """
        api_key = custom_api_key or self.gemini_api_key

        sql = None
        chart_type = "table"
        intent_label = "Catering Business Intelligence Analysis"

        # If LLM key is present, attempt LLM Text-to-SQL
        if api_key:
            llm_result = self._call_gemini_text_to_sql(question, api_key)
            if llm_result and "sql" in llm_result and llm_result["sql"]:
                sql = llm_result["sql"]
                chart_type = llm_result.get("chart_type", "table")
                intent_label = llm_result.get("intent", intent_label)

        # Fallback to local semantic engine if no API key or LLM error
        if not sql:
            sql, chart_type, intent_label = self._fallback_semantic_engine(question)

        # Execute Query
        query_result = self.execute_query(sql)

        # Generate Executive Narrative & Business Recommendations
        narrative = self._generate_narrative(question, query_result, intent_label, api_key)

        return {
            "question": question,
            "intent": intent_label,
            "sql": query_result["sql"],
            "error": query_result["error"],
            "columns": query_result["columns"],
            "rows": query_result["rows"],
            "row_count": query_result["row_count"],
            "chart_type": chart_type,
            "executive_summary": narrative["summary"],
            "recommendations": narrative["recommendations"]
        }

    def _call_gemini_text_to_sql(self, question: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Invokes Gemini API via standard HTTPS to generate SQL and chart recommendation."""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        system_instruction = f"""
You are the Catering Business Intelligence Copilot.
Translate user questions into an accurate SQLite SELECT query based on this schema:
{CATERING_SCHEMA_DOCS}

Strict Rules:
1. ONLY return a JSON object with keys:
   "sql": "SELECT ...",
   "chart_type": "bar" | "line" | "doughnut" | "table",
   "intent": "Brief description of analysis"
2. ONLY generate safe read-only SELECT or WITH statements.
3. Use pre-calculated views 'v_event_profitability' and 'v_menu_performance' whenever possible for faster, consistent calculations.
4. Always ROUND monetary and percentage calculations to 1 or 2 decimal places.
5. Do not include markdown codeblocks, only pure JSON.
"""
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_instruction}\n\nUser Question: {question}"}]}
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception:
            return None

    def _generate_narrative(self, question: str, query_result: Dict[str, Any], intent: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Produces clear, domain-specific catering executive takeaways and recommendations."""
        rows = query_result.get("rows", [])
        if not rows:
            return {
                "summary": "No historical catering records matched this criteria. Consider broadening the date filter or parameters.",
                "recommendations": ["Check if the event status or category filter matches actual records."]
            }

        # Catering-specific heuristic synthesis based on data content
        summary_lines = []
        recommendations = []

        # Analyze columns present
        first_row = rows[0]
        keys = list(first_row.keys())

        if "avg_gross_margin_pct" in keys or "gross_margin_pct" in keys:
            margin_key = "avg_gross_margin_pct" if "avg_gross_margin_pct" in keys else "gross_margin_pct"
            margins = [r[margin_key] for r in rows if r[margin_key] is not None]
            if margins:
                best_val = max(margins)
                worst_val = min(margins)
                best_row = next(r for r in rows if r[margin_key] == best_val)
                worst_row = next(r for r in rows if r[margin_key] == worst_val)
                
                label_col = keys[0]
                summary_lines.append(f"**Gross Margin Spread**: Ranges from **{worst_val}%** ({worst_row[label_col]}) up to **{best_val}%** ({best_row[label_col]}).")
                
                if worst_val < 15.0:
                    recommendations.append(f"⚠️ **Low Margin Alert**: '{worst_row[label_col]}' operates at only {worst_val}% gross margin. Review package pricing tiers and staffing ratios.")
                if best_val >= 20.0:
                    recommendations.append(f"⭐ **High Profit Opportunity**: Promote '{best_row[label_col]}' packages to maximize gross profit margins.")

        if "avg_prime_cost_pct" in keys or "prime_cost_pct" in keys:
            prime_key = "avg_prime_cost_pct" if "avg_prime_cost_pct" in keys else "prime_cost_pct"
            high_prime = [r for r in rows if r.get(prime_key) and r[prime_key] > 65.0]
            if high_prime:
                summary_lines.append(f"**Prime Cost Warning**: {len(high_prime)} segments exceed the 65% catering prime cost ceiling.")
                recommendations.append("📉 **Cost Control**: Re-engineer menu recipes with food costs > 32% or cap on-site staffing overtime.")

        if "variance" in keys or "total_cost_overrun" in keys:
            var_key = "variance" if "variance" in keys else "total_cost_overrun"
            overruns = [r[var_key] for r in rows if r[var_key] is not None and r[var_key] > 0]
            if overruns:
                total_overrun = sum(overruns)
                summary_lines.append(f"**Budget Overruns**: Identified **${total_overrun:,.2f}** in cumulative cost variances over quoted budgets.")
                recommendations.append("📋 **Standardize Scope**: Implement a contract clause for client schedule creep and overtime surcharges.")

        if "food_cost_pct" in keys and "item_name" in keys:
            high_food_cost = [r for r in rows if r.get("food_cost_pct") and r["food_cost_pct"] > 32.0]
            if high_food_cost:
                summary_lines.append(f"**Menu Engineering**: {len(high_food_cost)} menu items carry a food cost exceeding the 32% threshold.")
                top_costly = high_food_cost[0]
                recommendations.append(f"🍽️ **Menu Repricing**: '{top_costly['item_name']}' has a {top_costly['food_cost_pct']}% food cost. Consider increasing selling price from ${top_costly['selling_price']} or reducing portion cost.")

        if not summary_lines:
            summary_lines.append(f"Retrieved **{len(rows)} records** matching your catering inquiry. Results are sorted by primary performance metrics.")

        if not recommendations:
            recommendations.append("Monitor spend per guest and labor efficiency metrics regularly to prevent quote slippage.")

        return {
            "summary": " ".join(summary_lines),
            "recommendations": recommendations
        }
