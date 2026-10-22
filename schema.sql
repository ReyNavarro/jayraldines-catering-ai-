-- Catering Business Intelligence & Operations Database Schema
-- Optimized for SQLite & PostgreSQL compatibility

CREATE TABLE IF NOT EXISTS clients (
    client_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    company_name TEXT,
    client_type TEXT NOT NULL CHECK(client_type IN ('Corporate', 'Private', 'Non-profit', 'Wedding/Individual')),
    contact_email TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id TEXT PRIMARY KEY,
    venue_name TEXT NOT NULL,
    kitchen_type TEXT NOT NULL CHECK(kitchen_type IN ('Full Commercial Kitchen', 'Prep Only / Warming', 'No Kitchen / Mobile Only')),
    city TEXT NOT NULL,
    preferred_caterer INTEGER DEFAULT 0,
    commission_rate REAL DEFAULT 0.0 -- e.g. 0.10 for 10% venue commission
);

CREATE TABLE IF NOT EXISTS menu_categories (
    category_id TEXT PRIMARY KEY,
    category_name TEXT NOT NULL,
    target_food_cost_pct REAL NOT NULL -- e.g. 28.0%
);

CREATE TABLE IF NOT EXISTS menu_items (
    item_id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES menu_categories(category_id),
    name TEXT NOT NULL,
    serving_unit TEXT NOT NULL, -- 'Per Person', 'Platter', 'Dozen'
    recipe_cost REAL NOT NULL, -- Raw ingredient cost per unit
    selling_price REAL NOT NULL, -- Standard menu price per unit
    dietary_tags TEXT,
    food_cost_pct REAL GENERATED ALWAYS AS (ROUND((recipe_cost / selling_price) * 100, 2)) VIRTUAL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL REFERENCES clients(client_id),
    venue_id TEXT NOT NULL REFERENCES venues(venue_id),
    event_name TEXT NOT NULL,
    event_date TEXT NOT NULL, -- 'YYYY-MM-DD'
    event_type TEXT NOT NULL CHECK(event_type IN ('Wedding', 'Corporate Gala', 'Cocktail Reception', 'Corporate Lunch', 'Charity Fundraiser', 'Private Dinner')),
    service_style TEXT NOT NULL CHECK(service_style IN ('Plated', 'Buffet', 'Family Style', 'Stations', 'Passed Hors d''oeuvres')),
    guest_count INTEGER NOT NULL,
    quoted_price REAL NOT NULL,
    actual_revenue REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Completed', 'Confirmed', 'Cancelled'))
);

CREATE TABLE IF NOT EXISTS event_line_items (
    line_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id),
    item_id TEXT NOT NULL REFERENCES menu_items(item_id),
    quantity REAL NOT NULL,
    unit_cost REAL NOT NULL,
    unit_price REAL NOT NULL,
    total_cost REAL NOT NULL,
    total_price REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS event_expenses (
    expense_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id),
    category TEXT NOT NULL CHECK(category IN ('Food Ingredients', 'Beverage & Bar', 'Kitchen Labor', 'Front of House Service Labor', 'Equipment & Rentals', 'Transportation & Logistics', 'Venue Commission')),
    budgeted_amount REAL NOT NULL,
    actual_amount REAL NOT NULL,
    variance REAL GENERATED ALWAYS AS (actual_amount - budgeted_amount) VIRTUAL,
    vendor_or_payee TEXT,
    notes TEXT
);

-- Analytical Views for Rapid Catering Insights
CREATE VIEW IF NOT EXISTS v_event_profitability AS
SELECT 
    e.event_id,
    e.event_name,
    e.event_date,
    strftime('%Y-%m', e.event_date) AS event_month,
    e.event_type,
    e.service_style,
    e.guest_count,
    c.client_name,
    c.company_name,
    c.client_type,
    v.venue_name,
    v.kitchen_type,
    e.quoted_price,
    e.actual_revenue,
    
    -- Expense category breakdowns
    COALESCE(SUM(CASE WHEN exp.category IN ('Food Ingredients', 'Beverage & Bar') THEN exp.actual_amount ELSE 0 END), 0) AS actual_food_bev_cost,
    COALESCE(SUM(CASE WHEN exp.category IN ('Kitchen Labor', 'Front of House Service Labor') THEN exp.actual_amount ELSE 0 END), 0) AS actual_labor_cost,
    COALESCE(SUM(CASE WHEN exp.category IN ('Equipment & Rentals', 'Transportation & Logistics', 'Venue Commission') THEN exp.actual_amount ELSE 0 END), 0) AS actual_overhead_cost,
    
    -- Budgeted totals
    COALESCE(SUM(exp.budgeted_amount), 0) AS total_budgeted_expenses,
    COALESCE(SUM(exp.actual_amount), 0) AS total_actual_expenses,
    
    -- Profit & Margin metrics
    ROUND(e.actual_revenue - COALESCE(SUM(exp.actual_amount), 0), 2) AS gross_profit,
    ROUND(((e.actual_revenue - COALESCE(SUM(exp.actual_amount), 0)) / NULLIF(e.actual_revenue, 0)) * 100, 2) AS gross_margin_pct,
    
    -- Catering Industry Core Ratios (Prime Cost = Food/Bev % + Labor %)
    ROUND((COALESCE(SUM(CASE WHEN exp.category IN ('Food Ingredients', 'Beverage & Bar') THEN exp.actual_amount ELSE 0 END), 0) / NULLIF(e.actual_revenue, 0)) * 100, 2) AS food_cost_pct,
    ROUND((COALESCE(SUM(CASE WHEN exp.category IN ('Kitchen Labor', 'Front of House Service Labor') THEN exp.actual_amount ELSE 0 END), 0) / NULLIF(e.actual_revenue, 0)) * 100, 2) AS labor_cost_pct,
    ROUND(((COALESCE(SUM(CASE WHEN exp.category IN ('Food Ingredients', 'Beverage & Bar', 'Kitchen Labor', 'Front of House Service Labor') THEN exp.actual_amount ELSE 0 END), 0)) / NULLIF(e.actual_revenue, 0)) * 100, 2) AS prime_cost_pct,
    
    -- Per-Guest Metrics (Spend Per Head & Cost Per Head)
    ROUND(e.actual_revenue / NULLIF(e.guest_count, 0), 2) AS revenue_per_guest,
    ROUND(COALESCE(SUM(exp.actual_amount), 0) / NULLIF(e.guest_count, 0), 2) AS cost_per_guest,
    ROUND((e.actual_revenue - COALESCE(SUM(exp.actual_amount), 0)) / NULLIF(e.guest_count, 0), 2) AS profit_per_guest,
    
    -- Overrun / Variance
    ROUND(COALESCE(SUM(exp.actual_amount), 0) - COALESCE(SUM(exp.budgeted_amount), 0), 2) AS total_cost_overrun
FROM events e
JOIN clients c ON e.client_id = c.client_id
JOIN venues v ON e.venue_id = v.venue_id
LEFT JOIN event_expenses exp ON e.event_id = exp.event_id
WHERE e.status = 'Completed'
GROUP BY e.event_id;

CREATE VIEW IF NOT EXISTS v_menu_performance AS
SELECT 
    m.item_id,
    m.name AS item_name,
    mc.category_name,
    m.recipe_cost,
    m.selling_price,
    ROUND(((m.selling_price - m.recipe_cost) / NULLIF(m.selling_price, 0)) * 100, 2) AS target_margin_pct,
    m.food_cost_pct,
    COUNT(DISTINCT eli.event_id) AS events_featured_in,
    COALESCE(SUM(eli.quantity), 0) AS total_portions_ordered,
    COALESCE(SUM(eli.total_price), 0) AS total_revenue_generated,
    COALESCE(SUM(eli.total_cost), 0) AS total_food_cost_incurred,
    ROUND(COALESCE(SUM(eli.total_price), 0) - COALESCE(SUM(eli.total_cost), 0), 2) AS total_item_profit
FROM menu_items m
JOIN menu_categories mc ON m.category_id = mc.category_id
LEFT JOIN event_line_items eli ON m.item_id = eli.item_id
GROUP BY m.item_id;
