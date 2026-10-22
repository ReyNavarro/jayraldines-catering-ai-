# CateringIQ Copilot - Data-Driven Catering Business Intelligence

**CateringIQ Copilot** is a specialized, conversational AI business intelligence engine designed for catering executives, operations directors, and culinary managers. It translates natural language questions into safe SQL queries against your catering operations data (bookings, menus, actual expenses, labor, and venue logs) to provide immediate executive takeaways, visual charts, and actionable operational recommendations.

---

## 🌟 Key Features

1. **Conversational Business Intelligence**: Ask natural questions like:
   - *"Which event types have the highest and lowest gross margins?"*
   - *"Compare buffet vs plated service styles on profitability and spend per head."*
   - *"Which menu items have a food cost percentage exceeding 32%?"*
   - *"Where did our biggest labor and expense budget overruns occur?"*
   - *"Which venues result in the highest labor cost percentages?"*
2. **Catering Financial Benchmarking**:
   - **Prime Cost % Analysis**: Tracks combined Food/Beverage + Labor costs against the industry target of **55% - 65%**.
   - **Spend Per Head vs. Cost Per Head**: Evaluates actual realized profit per guest across corporate, wedding, and social events.
   - **Labor & Expense Variance Tracker**: Detects schedule creep and off-site venue overtime.
3. **Menu Engineering & Recipe Costing Matrix**:
   - Compares raw recipe costs against selling prices.
   - Highlights high-risk proteins (filet mignon, Chilean sea bass, lobster) needing price adjustments or portion adjustments.
4. **Dual AI Architecture**:
   - **Local Semantic Engine (Default)**: Zero configuration, instant response, runs completely offline without any API keys.
   - **Gemini LLM Integration (Optional)**: Drop in your Gemini API key in the UI Settings to allow arbitrary, open-ended conversational inquiries.
5. **Zero External Python Dependencies**:
   - Powered by Python 3's built-in `http.server` and `sqlite3`. Runs instantly on any machine.

---

## 🚀 Quick Start

### 1. Start the Copilot Web Server
In your terminal, navigate to this directory and run:
```bash
python server.py
```

The server will start on port `8080`.

### 2. Open the Dashboard in your Browser
Navigate to:
```
http://localhost:8080
```

You can now:
- Click any of the **Quick Prompt chips** to see instant catering analysis, charts, and executive recommendations.
- Open the **Events Explorer** tab to inspect all 115 historical catering events.
- Open the **Menu Engineering** tab to check recipe food costs.
- Open the **Safe SQL Studio** to run custom analytical queries.

---

## 📊 Database Schema Overview

The database (`catering_bi.db`) is structured around standard catering operations:

| Table / View | Description |
| :--- | :--- |
| `events` | Master bookings (dates, guest counts, service styles, quoted vs billed revenue). |
| `clients` | Corporate accounts, wedding couples, and non-profits. |
| `venues` | Preferred venues, kitchen facilities (Commercial Kitchen vs Prep Only vs Mobile), commission fees. |
| `menu_items` | Recipe ingredient costs, menu prices, dietary tags, target food cost %. |
| `event_line_items` | Specific dishes, quantities, and portion prices selected per event. |
| `event_expenses` | Actual line-item expenses (Food, Bar, Kitchen Labor, Service Labor, Rentals, Transport). |
| `v_event_profitability` | Pre-calculated analytical view providing gross profit, margin %, prime cost %, spend per guest, and variances. |
| `v_menu_performance` | Aggregate performance view tracking portions sold, revenue, cost, and realized margins. |

---

## 🔌 Connecting to Your Catering / POS / CRM System

### Importing CSV Exports (Caterease, Toast, Square)
Use the included `import_catering_data.py` pipeline to import your own data:
```python
from import_catering_data import import_events_from_csv, import_expenses_from_csv

# Import events
import_events_from_csv("path/to/caterease_bookings.csv")

# Import actual supplier and labor expenses
import_expenses_from_csv("path/to/event_expenses.csv")
```

### Direct PostgreSQL Connection
If you host your catering database in PostgreSQL, you can update the connection in `copilot_engine.py` by pointing to your PostgreSQL connection string:
```python
# In copilot_engine.py
# import psycopg2
# conn = psycopg2.connect("postgresql://user:pass@localhost:5432/catering_db")
```

---

## 📁 Project Structure

```
catering-bi-copilot/
├── schema.sql             # Relational catering schema & analytical views
├── seed_data.py           # Generates 115 realistic past events with labor & margin variance
├── catering_bi.db         # SQLite database containing catering history
├── copilot_engine.py      # Semantic Text-to-SQL engine & business intelligence synthesizer
├── import_catering_data.py# ETL helper for Caterease/Toast/Square imports
├── server.py              # Lightweight REST API & Web Server (port 8080)
├── web/
│   └── index.html         # Modern Executive BI Dashboard (Tailwind + Chart.js)
└── README.md              # Project documentation
```
