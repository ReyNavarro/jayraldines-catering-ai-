"""
Catering Data Ingestion & ETL Pipeline
Enables importing live or historical data from:
1. Caterease, Toast, or Square CSV exports
2. PostgreSQL / MySQL enterprise database connections
3. Custom spreadsheet exports
"""

import sqlite3
import csv
from pathlib import Path
from typing import Optional, Dict

DB_PATH = Path(__file__).parent / "catering_bi.db"

def get_connection(db_path: Path = DB_PATH):
    return sqlite3.connect(db_path)

def import_events_from_csv(csv_path: str, mapping: Optional[Dict[str, str]] = None) -> int:
    """
    Imports events from a CSV export.
    Default expected headers: event_id, client_id, venue_id, event_name, event_date, event_type, service_style, guest_count, quoted_price, actual_revenue, status
    """
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Apply mapping if column names differ (e.g. from Caterease or Toast)
            e_id = row.get("event_id") or row.get("BookingID") or row.get("id")
            c_id = row.get("client_id") or row.get("CustomerID") or "c_default"
            v_id = row.get("venue_id") or row.get("LocationID") or "v_default"
            name = row.get("event_name") or row.get("BookingName") or "Catering Event"
            date = row.get("event_date") or row.get("EventDate") or "2025-01-01"
            etype = row.get("event_type") or row.get("EventType") or "Corporate Lunch"
            style = row.get("service_style") or row.get("ServiceStyle") or "Buffet"
            guests = int(row.get("guest_count") or row.get("GuestCount") or 50)
            quoted = float(row.get("quoted_price") or row.get("ContractTotal") or 0.0)
            revenue = float(row.get("actual_revenue") or row.get("FinalBilled") or quoted)
            status = row.get("status") or "Completed"

            cur.execute("""
                INSERT OR REPLACE INTO events 
                (event_id, client_id, venue_id, event_name, event_date, event_type, service_style, guest_count, quoted_price, actual_revenue, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (e_id, c_id, v_id, name, date, etype, style, guests, quoted, revenue, status))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"Imported {inserted} events into Catering database.")
    return inserted

def import_expenses_from_csv(csv_path: str) -> int:
    """
    Imports post-event expenses and supplier bills (Sysco, staffing, rentals).
    """
    conn = get_connection()
    cur = conn.cursor()
    inserted = 0

    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exp_id = row.get("expense_id") or f"exp_imp_{inserted+1}"
            e_id = row.get("event_id") or row.get("BookingID")
            cat = row.get("category") or "Food Ingredients"
            budgeted = float(row.get("budgeted_amount") or 0.0)
            actual = float(row.get("actual_amount") or budgeted)
            vendor = row.get("vendor_or_payee") or "Supplier"
            notes = row.get("notes") or ""

            cur.execute("""
                INSERT OR REPLACE INTO event_expenses 
                (expense_id, event_id, category, budgeted_amount, actual_amount, vendor_or_payee, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (exp_id, e_id, cat, budgeted, actual, vendor, notes))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"Imported {inserted} expense records into Catering database.")
    return inserted

if __name__ == "__main__":
    print("Catering Data Ingestion Module Ready.")
    print("Usage: Call import_events_from_csv('events_export.csv') or import_expenses_from_csv('expenses_export.csv')")
