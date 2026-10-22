"""
Realistic Catering Dataset Seeder
Populates SQLite database with comprehensive historical catering events,
clients, venues, menu items, line items, and detailed operational expenses.
"""

import sqlite3
import random
import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "catering_bi.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

def seed_database(db_path=DB_PATH):
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Load and execute schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    # 1. Seed Clients
    clients_data = [
        ("c_001", "Apex Global Tech", "Apex Global Inc.", "Corporate", "events@apextech.com", "2024-01-15"),
        ("c_002", "Elena Rostova & Liam Vance", None, "Wedding/Individual", "elena.rostova@gmail.com", "2024-02-10"),
        ("c_003", "St. Jude Children's Gala Committee", "St. Jude Foundation", "Non-profit", "gala@stjude-benefit.org", "2024-01-20"),
        ("c_004", "Vanguard Law Partners", "Vanguard Legal LLP", "Corporate", "concierge@vanguardlaw.com", "2024-03-05"),
        ("c_005", "Marcus & Chloe Sterling", None, "Wedding/Individual", "chloesterling@outlook.com", "2024-03-12"),
        ("c_006", "Horizon Biotech Labs", "Horizon Biotech", "Corporate", "admin@horizonbio.com", "2024-02-18"),
        ("c_007", "Metropolitan Arts Council", "Metro Arts", "Non-profit", "fundraising@metroarts.org", "2024-01-28"),
        ("c_008", "David & Priya Patel", None, "Wedding/Individual", "priya.patel.events@gmail.com", "2024-04-02"),
        ("c_009", "Pinnacle Financial Advisory", "Pinnacle Capital", "Corporate", "reception@pinnaclecap.com", "2024-03-22"),
        ("c_010", "Dr. Julian Montgomery", None, "Private", "j.montgomery@alumni.harvard.edu", "2024-05-11"),
        ("c_011", "Greenfield University Alumni", "Greenfield Univ", "Non-profit", "alumni@greenfield.edu", "2024-04-15"),
        ("c_012", "Synthetix Robotics", "Synthetix AI", "Corporate", "people-ops@synthetix.ai", "2024-06-01"),
        ("c_013", "Sophia & Alexander Bennett", None, "Wedding/Individual", "bennett.wedding2025@gmail.com", "2024-05-19"),
        ("c_014", "Oakwood Private Wealth", "Oakwood Group", "Corporate", "vip@oakwoodwealth.com", "2024-06-14"),
        ("c_015", "Humane Animal Sanctuary", "HAS Charity", "Non-profit", "donations@has-sanctuary.org", "2024-07-02"),
    ]
    cursor.executemany("INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?)", clients_data)

    # 2. Seed Venues
    venues_data = [
        ("v_001", "The Grand Estate & Gardens", "Full Commercial Kitchen", "Suburban Valley", 1, 0.10),
        ("v_002", "Historic Glasshouse Conservatory", "Prep Only / Warming", "Downtown", 1, 0.12),
        ("v_003", "Skyline Loft Penthouse", "Full Commercial Kitchen", "Downtown", 0, 0.08),
        ("v_004", "Whispering Pines Vineyard", "Prep Only / Warming", "Wine Country", 1, 0.15),
        ("v_005", "Metropolitan Innovation Hall", "Prep Only / Warming", "Tech District", 0, 0.05),
        ("v_006", "The Foundry Industrial Hall", "No Kitchen / Mobile Only", "Arts District", 0, 0.00),
        ("v_007", "Harborview Yacht Club", "Full Commercial Kitchen", "Waterfront", 1, 0.10),
    ]
    cursor.executemany("INSERT INTO venues VALUES (?, ?, ?, ?, ?, ?)", venues_data)

    # 3. Seed Menu Categories
    categories_data = [
        ("cat_app", "Passed Hors d'oeuvres", 24.0),
        ("cat_plated", "Plated Entrees", 28.0),
        ("cat_buffet", "Buffet Stations & Carvery", 32.0),
        ("cat_dessert", "Desserts & Pastries", 22.0),
        ("cat_bar", "Bar & Beverage Packages", 20.0),
        ("cat_late", "Late Night Bites", 25.0),
    ]
    cursor.executemany("INSERT INTO menu_categories VALUES (?, ?, ?)", categories_data)

    # 4. Seed Menu Items
    menu_items_data = [
        # (item_id, category_id, name, serving_unit, recipe_cost, selling_price, dietary_tags)
        ("m_001", "cat_app", "Truffle Arancini with Garlic Aioli", "Per Person", 3.20, 14.00, "Vegetarian"),
        ("m_002", "cat_app", "Mini Maine Lobster Rolls on Brioche", "Per Person", 7.50, 22.00, "Contains Shellfish"),
        ("m_003", "cat_app", "Seared Ahi Tuna Wonton Crisps", "Per Person", 5.10, 18.00, "Pescatarian, Dairy-Free"),
        ("m_004", "cat_app", "Bacon-Wrapped Medjool Dates with Goat Cheese", "Per Person", 3.80, 15.00, "Gluten-Free"),
        ("m_005", "cat_app", "Wild Mushroom & Gruyere Tartlet", "Per Person", 2.90, 13.00, "Vegetarian"),
        
        ("m_010", "cat_plated", "Pan-Roasted Chilean Sea Bass", "Per Person", 16.50, 48.00, "Gluten-Free, Pescatarian"),
        ("m_011", "cat_plated", "Prime Center-Cut Filet Mignon with Red Wine Demi", "Per Person", 19.80, 56.00, "Gluten-Free"),
        ("m_012", "cat_plated", "Rosemary & Garlic Roasted French Cut Chicken", "Per Person", 7.20, 34.00, "Gluten-Free, Halal Friendly"),
        ("m_013", "cat_plated", "Butternut Squash & Sage Risotto", "Per Person", 5.40, 30.00, "Vegetarian, Gluten-Free"),
        ("m_014", "cat_plated", "Braised Beef Short Ribs with Polenta", "Per Person", 14.20, 44.00, "Gluten-Free"),

        ("m_020", "cat_buffet", "Carved Prime Rib with Horseradish Crème", "Per Person", 15.00, 42.00, "Gluten-Free"),
        ("m_021", "cat_buffet", "Cedar Plank Salmon with Lemon Dill Glaze", "Per Person", 12.80, 38.00, "Gluten-Free, Pescatarian"),
        ("m_022", "cat_buffet", "Artisanal Mediterranean Mezze Display", "Per Person", 6.20, 24.00, "Vegetarian, Vegan Options"),
        ("m_023", "cat_buffet", "Gourmet Macaroni & Cheese Station with Crispy Pancetta", "Per Person", 4.80, 20.00, "Comfort Food"),
        ("m_024", "cat_buffet", "Roasted Herb Seasonal Vegetables & Fingerling Potatoes", "Per Person", 3.10, 14.00, "Vegan, Gluten-Free"),

        ("m_030", "cat_dessert", "Warm Belgian Chocolate Lava Cake", "Per Person", 3.50, 14.00, "Vegetarian"),
        ("m_031", "cat_dessert", "Mini French Macaron & Petit Fours Tower", "Per Person", 4.20, 16.00, "Gluten-Free Friendly"),
        ("m_032", "cat_dessert", "New York Style Cheesecake Bites with Berry Coulis", "Per Person", 3.00, 12.00, "Vegetarian"),

        ("m_040", "cat_bar", "Ultra Premium Open Bar Package (4 Hours)", "Per Person", 12.00, 48.00, "Full Bar"),
        ("m_041", "cat_bar", "Craft Beer, Sommelier Wine & Prosecco Bar (4 Hours)", "Per Person", 8.50, 34.00, "Beer & Wine"),
        ("m_042", "cat_bar", "Artisanal Mocktail & Specialty Soda Station", "Per Person", 3.20, 16.00, "Non-Alcoholic"),

        ("m_050", "cat_late", "Gourmet Slider Trio & Truffle Parmesan Fries", "Per Person", 4.60, 18.00, "Late Night"),
        ("m_051", "cat_late", "Wood-Fired Neapolitan Flatbreads", "Per Person", 3.40, 15.00, "Late Night"),
    ]
    cursor.executemany("INSERT INTO menu_items (item_id, category_id, name, serving_unit, recipe_cost, selling_price, dietary_tags) VALUES (?, ?, ?, ?, ?, ?, ?)", menu_items_data)

    # 5. Generate Events across 2025 and 2026
    event_types = [
        ("Wedding", ["Plated", "Family Style", "Buffet"], (90, 240), 140, 260),
        ("Corporate Gala", ["Plated", "Stations"], (120, 350), 125, 210),
        ("Corporate Lunch", ["Buffet", "Stations"], (35, 120), 45, 85),
        ("Cocktail Reception", ["Passed Hors d'oeuvres", "Stations"], (60, 180), 65, 120),
        ("Charity Fundraiser", ["Plated", "Buffet"], (100, 300), 110, 190),
        ("Private Dinner", ["Plated"], (14, 40), 160, 320)
    ]

    base_date = datetime.date(2025, 1, 10)
    events_records = []
    line_items_records = []
    expenses_records = []

    event_counter = 100
    line_counter = 1000
    exp_counter = 5000

    random.seed(42) # Reproducible, highly realistic variance

    for i in range(115):
        event_counter += 1
        event_id = f"evt_{event_counter}"
        
        # Pick event type
        etype_info = random.choice(event_types)
        etype_name = etype_info[0]
        service_style = random.choice(etype_info[1])
        guest_count = random.randint(etype_info[2][0], etype_info[2][1])
        per_head_target = random.uniform(etype_info[3], etype_info[4])

        # Client matching
        if etype_name == "Wedding":
            client = random.choice([c for c in clients_data if c[3] == "Wedding/Individual"])
        elif etype_name in ("Corporate Gala", "Corporate Lunch"):
            client = random.choice([c for c in clients_data if c[3] == "Corporate"])
        elif etype_name == "Charity Fundraiser":
            client = random.choice([c for c in clients_data if c[3] == "Non-profit"])
        else:
            client = random.choice(clients_data)

        # Venue matching
        venue = random.choice(venues_data)
        
        # Calculate date (spaced across 2025 to mid 2026)
        day_offset = int((i / 115.0) * 520) + random.randint(-4, 4)
        event_date = base_date + datetime.timedelta(days=max(0, day_offset))
        date_str = event_date.strftime("%Y-%m-%d")

        event_name = f"{client[1]} - {etype_name}"
        
        quoted_price = round(guest_count * per_head_target, 2)
        # Revenue adjustments: 80% exact, 15% added bar/guest add-ons (+5-15%), 5% negotiated discount (-3-8%)
        rev_factor = random.choices([1.0, 1.08, 1.14, 0.95], weights=[65, 20, 10, 5])[0]
        actual_revenue = round(quoted_price * rev_factor, 2)

        events_records.append((
            event_id, client[0], venue[0], event_name, date_str, etype_name,
            service_style, guest_count, quoted_price, actual_revenue, "Completed"
        ))

        # Menu selections for line items
        selected_items = []
        if service_style == "Plated":
            selected_items += [random.choice([m for m in menu_items_data if m[1] == "cat_app"])]
            selected_items += [random.choice([m for m in menu_items_data if m[1] == "cat_plated"])]
            selected_items += [random.choice([m for m in menu_items_data if m[1] == "cat_dessert"])]
        elif service_style == "Buffet":
            selected_items += [random.choice([m for m in menu_items_data if m[1] == "cat_buffet"])]
            selected_items += [random.choice([m for m in menu_items_data if m[1] == "cat_buffet"])]
            selected_items += [random.choice([m for m in menu_items_data if m[1] == "cat_dessert"])]
        elif service_style == "Passed Hors d'oeuvres":
            selected_items += random.sample([m for m in menu_items_data if m[1] == "cat_app"], 3)
        else: # Stations / Family style
            selected_items += [random.choice([m for m in menu_items_data if m[1] == "cat_app"])]
            selected_items += [random.choice([m for m in menu_items_data if m[1] == "cat_buffet"])]
            selected_items += [random.choice([m for m in menu_items_data if m[1] == "cat_dessert"])]

        # Bar selection
        if etype_name in ("Wedding", "Corporate Gala", "Cocktail Reception"):
            selected_items.append(random.choice([m for m in menu_items_data if m[1] == "cat_bar"]))

        for item in selected_items:
            line_counter += 1
            line_id = f"line_{line_counter}"
            item_id = item[0]
            unit_cost = item[4]
            unit_price = item[5]
            qty = float(guest_count)
            # Add slight over-prep for buffets
            if service_style == "Buffet":
                qty = round(qty * 1.08, 0)
            
            line_items_records.append((
                line_id, event_id, item_id, qty, unit_cost, unit_price,
                round(qty * unit_cost, 2), round(qty * unit_price, 2)
            ))

        # Expenses calculation (Budgeted vs Actual with real-world operational variance)
        # Target Industry Breakdown:
        # Food & Bev: 24-32% of quoted
        # Kitchen Labor: 12-18% of quoted
        # Front of House Labor: 14-22% of quoted
        # Rentals/Linens: 6-12% of quoted
        # Transport & Logistics: 3-6% of quoted
        # Venue Commission: venue[5] * quoted

        # 1. Food Ingredients
        budget_food = round(actual_revenue * random.uniform(0.24, 0.28), 2)
        # Buffets and remote kitchens tend to have ingredient waste variance
        food_var_factor = random.uniform(0.96, 1.15) if venue[2] != "Full Commercial Kitchen" else random.uniform(0.95, 1.05)
        actual_food = round(budget_food * food_var_factor, 2)
        exp_counter += 1
        expenses_records.append((
            f"exp_{exp_counter}", event_id, "Food Ingredients", budget_food, actual_food, "Sysco & Local Organic Farms", "Fresh proteins & produce"
        ))

        # 2. Beverage & Bar
        if any(it[1] == "cat_bar" for it in selected_items):
            budget_bev = round(actual_revenue * random.uniform(0.08, 0.12), 2)
            actual_bev = round(budget_bev * random.uniform(0.92, 1.18), 2)
            exp_counter += 1
            expenses_records.append((
                f"exp_{exp_counter}", event_id, "Beverage & Bar", budget_bev, actual_bev, "Southern Glazer's Wine & Spirits", "Spirits, wine, mixers"
            ))

        # 3. Kitchen Labor (Chef & Cooks)
        budget_kitchen = round(actual_revenue * random.uniform(0.12, 0.16), 2)
        # Mobile / prep only venues incur overtime
        labor_mult = random.uniform(1.05, 1.25) if venue[2] == "No Kitchen / Mobile Only" else random.uniform(0.95, 1.08)
        actual_kitchen = round(budget_kitchen * labor_mult, 2)
        exp_counter += 1
        expenses_records.append((
            f"exp_{exp_counter}", event_id, "Kitchen Labor", budget_kitchen, actual_kitchen, "Culinary Staff Payroll", "Executive Chef, Sous, Prep cooks"
        ))

        # 4. Front of House Service Labor (Captains, Bartenders, Servers)
        budget_foh = round(actual_revenue * random.uniform(0.14, 0.18), 2)
        # Weddings and Galas often run over scheduled hours
        overtime_factor = random.uniform(1.02, 1.28) if etype_name in ("Wedding", "Corporate Gala") else random.uniform(0.96, 1.05)
        actual_foh = round(budget_foh * overtime_factor, 2)
        exp_counter += 1
        notes = "Event ran 45 mins over schedule" if overtime_factor > 1.12 else "Standard service shift"
        expenses_records.append((
            f"exp_{exp_counter}", event_id, "Front of House Service Labor", budget_foh, actual_foh, "Staffing Agency & Core Crew", notes
        ))

        # 5. Rentals & Linens
        budget_rentals = round(actual_revenue * random.uniform(0.06, 0.10), 2)
        actual_rentals = round(budget_rentals * random.uniform(0.98, 1.10), 2)
        exp_counter += 1
        expenses_records.append((
            f"exp_{exp_counter}", event_id, "Equipment & Rentals", budget_rentals, actual_rentals, "Classic Party Rentals", "China, flatware, glassware, linens"
        ))

        # 6. Logistics & Transportation
        budget_logistics = round(actual_revenue * random.uniform(0.03, 0.05), 2)
        actual_logistics = round(budget_logistics * random.uniform(0.95, 1.08), 2)
        exp_counter += 1
        expenses_records.append((
            f"exp_{exp_counter}", event_id, "Transportation & Logistics", budget_logistics, actual_logistics, "Fleet Logistics", "Refrigerated van fuel & transit"
        ))

        # 7. Venue Commission (if applicable)
        if venue[5] > 0:
            comm_amount = round(actual_revenue * venue[5], 2)
            exp_counter += 1
            expenses_records.append((
                f"exp_{exp_counter}", event_id, "Venue Commission", comm_amount, comm_amount, venue[1], f"{int(venue[5]*100)}% venue preferred caterer fee"
            ))

    cursor.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", events_records)
    cursor.executemany("INSERT INTO event_line_items VALUES (?, ?, ?, ?, ?, ?, ?, ?)", line_items_records)
    cursor.executemany("INSERT INTO event_expenses (expense_id, event_id, category, budgeted_amount, actual_amount, vendor_or_payee, notes) VALUES (?, ?, ?, ?, ?, ?, ?)", expenses_records)

    conn.commit()
    conn.close()
    print(f"Successfully seeded database at {db_path} with:")
    print(f"- {len(clients_data)} Clients")
    print(f"- {len(venues_data)} Venues")
    print(f"- {len(menu_items_data)} Menu Items")
    print(f"- {len(events_records)} Historical Catering Events")
    print(f"- {len(line_items_records)} Event Line Items")
    print(f"- {len(expenses_records)} Detailed Expense Records")

if __name__ == "__main__":
    seed_database()
