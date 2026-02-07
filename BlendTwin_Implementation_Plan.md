# BlendTwin Trend Query Workbench — Implementation Plan

> **Project:** BlendTwin Trend Query Workbench – Web Application  
> **Client/Sponsor:** OMS (BlendTwin Program)  
> **Team:** Kamesh (Full-stack: Backend + Frontend)  
> **Duration:** 1 week (prototype) + deployment  
> **Delivery Model:** Agile prototype → Web app with deployment

---

## 📋 Executive Summary

Design and implement a **Python-based web application** using FastAPI to develop, test, visualize, and publish Trend SQL queries used by the BlendTwin cloud execution engine. The tool enables rapid validation of trend queries using a fixed test blend, with full **create** and **update** capabilities for SQL templates, optional **visual SQL query builder** support, and cloud deployment.

---

## 🎯 Objectives

| # | Objective |
|---|-----------|
| 1 | Build a web application (FastAPI + frontend) for trend query development |
| 2 | **Create new** and **update existing** Trend SQL templates in database |
| 3 | Execute queries against cloud database with parameter substitution |
| 4 | Display query results in tabular form and multi-series cycle-based plots |
| 5 | Use fixed test blend context (no blend selector in prototype) |
| 6 | Deploy as a web application |

---

## 📦 Scope

### ✅ In Scope

- [ ] Web application (FastAPI backend + frontend)
- [ ] Load Trend SQL templates from database
- [ ] **Create new** SQL templates
- [ ] **Edit and update** existing SQL templates
- [ ] SQL Editor (code-based) and/or Visual SQL Query Builder
- [ ] Execute queries against cloud database
- [ ] Display query output in tabular form
- [ ] Plot trend data (multi-series, cycle-based)
- [ ] Save SQL templates to database (create + update)
- [ ] Fixed test blend context (no blend selector)
- [ ] Logging and basic error handling
- [ ] Deployment (Docker / cloud)

### ❌ Out of Scope

- Multi-blend execution
- Cloud job orchestration
- User authentication (prototype phase)
- Role-based access

---

## 🛠 Technical Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.x, FastAPI |
| **Frontend** | React / Vue / or HTML+JS (SPA) |
| **DB Access** | SQLAlchemy + PyMySQL |
| **Data** | pandas |
| **Plotting** | Chart.js / Plotly.js / Apache ECharts (frontend) |
| **SQL Editor** | Monaco Editor (VS Code–like) or CodeMirror |
| **SQL Query Builder** | react-querybuilder (optional visual builder) |
| **Deployment** | Docker, cloud (AWS/GCP/Azure) or PaaS |
| **Packaging** | venv + requirements.txt, package.json |

---

## 🔌 Database Connection (Staging)

Credentials are sourced from **OMS_Connections.xlsx** (VPS-BlendTwin-Staging row). Use environment variables—never hardcode credentials.

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Environment** | VPS-BlendTwin-Staging | Staging |
| **App URL** | https://staging.blendtwin.com | — |
| **VPS Host** | 72.60.27.8 | Hostinger-VPS |
| **DB Host** | localhost | When app runs on VPS |
| **DB Port** | 3306 | MySQL |
| **DB Name** | blendtwin | — |
| **Charset** | utf8 | — |

**Setup:**
1. Copy `.env.example` → `.env`
2. Fill in `DB_USER`, `DB_PASSWORD`, `SSH_PASSWORD` from your credentials sheet
3. If running **on VPS**: `DB_HOST=localhost`, `USE_SSH_TUNNEL=false`
4. If running **locally**: set `USE_SSH_TUNNEL=true` and SSH vars to tunnel through VPS

**Config module:** `config/database.py` — `get_db_url()`, `get_ssh_config()`

---

## 🔧 SQL Query Builder Integration

### Overview

BlendTwin trend queries follow a fixed contract (`cycleno | value | series`). You can support both **manual SQL editing** and **visual query building** depending on user skill level.

### Option A: Code-Based SQL Editor (Recommended Primary)

| Component | Purpose |
|-----------|---------|
| **Monaco Editor** | VS Code–like editor with SQL syntax highlighting, autocomplete, validation |
| **Libraries** | `@monaco-editor/react` or `monaco-sql-languages` (MySQL dialect) |
| **Use case** | Full control for complex queries, joins, aggregations |

**Integration:** Embed Monaco in your frontend. Send raw SQL to FastAPI. Backend validates output columns match contract.

---

### Option B: Visual SQL Query Builder (Optional / Hybrid)

| Component | Purpose |
|-----------|---------|
| **react-querybuilder** | Drag-and-drop WHERE clause builder (fields, operators, values) |
| **Export** | Generates SQL WHERE conditions; combine with fixed SELECT/FROM |
| **Use case** | Non-SQL users building filter conditions; quick parameter-based queries |

**Integration flow:**
```
User builds filters visually (e.g. blendid = 123, tankno = 5)
        ↓
react-querybuilder exports SQL WHERE clause
        ↓
Backend merges with template: SELECT cycleno, value, series FROM ... WHERE {builder_output}
        ↓
Execute and display
```

**Limitation:** Best for WHERE/filter logic. Full SELECT/FROM with joins typically still needs code editor.

---

### Option C: Hybrid Approach (Recommended)

| Mode | When to Use |
|------|-------------|
| **Visual Builder** | Simple trends: user picks table, columns, builds filters. Good for TI-01, FL-01, QL-01. |
| **Code Editor** | Complex trends: custom joins, subqueries, aggregations. Full SQL control. |
| **Toggle** | Let user switch between "Visual" and "Advanced (SQL)" in the UI. |

**Implementation steps:**
1. Add Monaco Editor for SQL editing (create/edit templates).
2. Add "New from template" flow: pick base trend type → pre-fill SELECT/FROM → use visual builder for WHERE.
3. Store final SQL in `bts_cfg_sql_templates` regardless of how it was built.

---

### FastAPI Endpoints for SQL Builder

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /api/trends` | GET | List trends + templates |
| `GET /api/trends/{trend_code}` | GET | Get template, plot config, params |
| `POST /api/trends` | POST | **Create** new SQL template |
| `PUT /api/trends/{template_id}` | PUT | **Update** existing SQL template |
| `POST /api/execute` | POST | Execute SQL with params, return results |
| `GET /api/schema` | GET | Table/column metadata for query builder autocomplete |

---

## 📊 Database Schema & Usage

### Table 1: SQL Templates (CREATE + UPDATE TARGET)

**Table:** `bts_cfg_sql_templates`

| Column | Purpose |
|--------|---------|
| template_id | Unique identifier |
| trend_code | Trend reference |
| trend_name | Display name |
| sql_template | SQL text |
| is_active | Active flag |
| last_updated_on | Timestamp |

**Web App Actions:** READ → **CREATE** → EDIT → **UPDATE** ✅

---

### Table 2: Trend Plot Configuration (REQUIRED)

**Table:** `bts_cfg_trend_plots`

| Column | Purpose |
|--------|---------|
| trend_code | Trend reference |
| x_col | e.g. cycleno |
| y_col | e.g. value |
| series_col | e.g. series |
| plot_type | line, step, etc. |
| y_axis | left, right |
| sort_numeric | Y/N |
| legend_order | optional |
| title, x_label, y_label | Plot labels |

**Python App Actions:** READ (always), OPTIONAL UPDATE (if needed)

---

### Table 3: Trend Parameters (REQUIRED)

**Table:** `bts_cfg_trend_parameters`

| Column | Purpose |
|--------|---------|
| trend_code | Trend reference |
| param_name | tankno, component, etc. |
| param_type | string, number, list |
| is_required | Required flag |
| default_value | Default |
| ui_label | Display label |
| display_order | UI order |

**Python App Actions:** READ → Build parameter panel → Substitute into SQL

---

## 🔄 End-to-End Flow

### Existing Trend (Update)

```
User selects Trend
        ↓
Load SQL template (Table 1)
Load plot config (Table 2)
Load parameters (Table 3)
        ↓
User enters parameters
        ↓
Render SQL (substitute parameters)
        ↓
Execute SQL
        ↓
Display table → Plot using plot config
        ↓
User edits SQL (Editor or Visual Builder)
        ↓
Save/Update SQL back to Table 1
```

### New Trend (Create)

```
User clicks "Create New Trend"
        ↓
Enter trend_code, trend_name
        ↓
Build SQL via Code Editor OR Visual Query Builder
        ↓
Configure parameters (Table 3) + plot config (Table 2)
        ↓
Execute & validate (cycleno | value | series)
        ↓
Save new template to Table 1
```

---

## 📐 SQL Contract (Mandatory)

All trend queries **must** return:

| Column | Type | Notes |
|--------|------|-------|
| cycleno | numeric | Sorted |
| value | numeric | — |
| series | string | Label for plotting |

---

## 🖥 Application Features

| Feature | Description |
|---------|-------------|
| **Trend Selector** | Load existing trend queries |
| **Create New Trend** | Create new SQL template with trend_code, trend_name |
| **SQL Editor** | Code-based SQL editing (Monaco/CodeMirror) |
| **Visual Query Builder** | Optional drag-and-drop WHERE builder |
| **Parameter Panel** | Fixed blend ID + optional parameters |
| **Execute** | Run SQL and load results |
| **Data Grid** | Show result rows |
| **Plot Panel** | Line plot by series |
| **Save** | Create or update SQL template in DB |

---

## 📅 Implementation Phases

### Phase 1: Web Foundation (Day 1–2)

| Task | Owner | Status |
|------|-------|--------|
| Set up FastAPI project structure (venv, requirements.txt) | Kamesh | ⬜ |
| Implement DB connection (SQLAlchemy + PyMySQL) | Kamesh | ⬜ |
| CRUD for `bts_cfg_sql_templates` (Create + Read + Update) | Kamesh | ⬜ |
| Read for `bts_cfg_trend_plots` and `bts_cfg_trend_parameters` | Kamesh | ⬜ |
| Basic frontend shell (Trend Selector + SQL Editor) | Kamesh | ⬜ |
| Integrate Monaco Editor or CodeMirror for SQL | Kamesh | ⬜ |

---

### Phase 2: Core Functionality (Day 3–4)

| Task | Owner | Status |
|------|-------|--------|
| Dynamic parameter panel from `bts_cfg_trend_parameters` | Kamesh | ⬜ |
| SQL parameter substitution logic | Kamesh | ⬜ |
| Execute API endpoint + pandas result handling | Kamesh | ⬜ |
| Data grid display (frontend) | Kamesh | ⬜ |
| Create new trend flow (POST) | Kamesh | ⬜ |
| Update existing trend flow (PUT) | Kamesh | ⬜ |

---

### Phase 3: Visualization & SQL Builder (Day 5–6)

| Task | Owner | Status |
|------|-------|--------|
| Plot panel using `bts_cfg_trend_plots` (Chart.js/Plotly) | Kamesh | ⬜ |
| Multi-series line plot (cycle-based) | Kamesh | ⬜ |
| Correct cycle ordering | Kamesh | ⬜ |
| **Optional:** Integrate react-querybuilder for visual WHERE | Kamesh | ⬜ |
| Logging and error handling | Kamesh | ⬜ |
| Basic user guide (1–2 pages) | Kamesh | ⬜ |

---

### Phase 4: Deployment & Handover (Day 7+)

| Task | Owner | Status |
|------|-------|--------|
| Dockerize application (Dockerfile, docker-compose) | Kamesh | ⬜ |
| Deploy to cloud or PaaS | Kamesh | ⬜ |
| README with setup and usage | Kamesh | ⬜ |
| Handover walkthrough | Technical Owner | ⬜ |
| Final testing against acceptance criteria | Kamesh | ⬜ |

---

## 📋 P1 Trends (Prototype Scope)

| Code | Name | Category | Source Table(s) | Parameters | Series Examples |
|------|------|----------|-----------------|------------|-----------------|
| **TI-01** | Tank Inventory Trend | Inventory | bts_TankInventory | blendid, tankno | tankvol, flowin |
| **TI-02** | Tank Volume Delta Trend | Inventory | bts_TankInventory | blendid, tankno | delta |
| **FL-01** | Stream Flow Trend | Flow | bts_TankInventory | blendid, tankno | flowin, flowout |
| **QL-01** | Single Quality Trend | Quality | Quality result table | blendid, quality | measured |
| **HB-01** | History Inventory Balance | History/Balance | bts_HistoryInventoryBalance | blendid, tankno | ivol, fvol, diff |
| **VL-01** | Validation Status Trend | Validation | History/validation table | blendid | error, validation |

---

## 📋 P2 Trends (Optional – If Time Permits)

| Code | Name | Category | Notes |
|------|------|----------|-------|
| QL-02 | Multi-Quality Comparison | Quality | Same pattern as QL-01 |
| FL-02 | Cumulative Flow Trend | Flow | Derived metric |

---

## ✅ Acceptance Criteria

- [ ] Can load a trend query from DB
- [ ] Can **create** new SQL templates
- [ ] Can **update** existing SQL templates
- [ ] Can execute query for test blend
- [ ] Correct cycle ordering in results and plot
- [ ] Multiple series plotted correctly
- [ ] SQL edits saved back to DB
- [ ] Web app runs in browser
- [ ] Deployable (Docker / cloud)

---

## 👥 Roles & Responsibilities

| Role | Responsibility |
|------|----------------|
| **Sponsor** | Direction, scope control |
| **Technical Owner** | Architecture, reviews |
| **Kamesh** | Full-stack: Backend, GUI, DB integration, data handling, plotting, testing, documentation |

---

## 📦 Deliverables

1. Working web application (FastAPI + frontend source code)
2. Database-backed SQL template CRUD (Create + Update)
3. SQL Editor (and optional Visual Query Builder)
4. Plotting of trend data
5. Docker + deployment configuration
6. README with setup and usage
7. Basic user guide (1–2 pages)
8. Handover walkthrough

---

## 📌 Key Notes

> **Configuration Tables:** The application uses existing trend configuration tables for SQL templates, plot definitions, and parameter definitions. The tool updates **only** the SQL template table; all other configuration and data tables are **read-only** during the prototype phase.

---

*Document generated from BlendTwin Platform Project SOW • Implementation Plan v2.0 (Web App + CRUD + SQL Builder)*
