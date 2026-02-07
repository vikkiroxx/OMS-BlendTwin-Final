# BlendTwin Trend Query Workbench

A web application to develop, test, visualize, and publish Trend SQL queries used by the BlendTwin cloud execution engine.

## Features

- **Trend Selector** — Load existing trend queries from database
- **Create New Trend** — Add new SQL templates with trend_code and trend_name
- **SQL Editor** — CodeMirror-based editor with syntax highlighting
- **Parameter Panel** — Dynamic parameters from `bts_cfg_trend_parameters`
- **Execute** — Run SQL with parameter substitution
- **Data Grid** — Tabular results
- **Plot Panel** — Multi-series line chart (cycleno vs value by series)
- **Save** — Create or update SQL templates in database

## Quick Start

### 1. Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy env template and fill credentials
copy .env.example .env
# Edit .env with your DB_USER, DB_PASSWORD from OMS_Connections.xlsx
```

### 2. Database

Ensure MySQL is running and the `blendtwin` database exists. If config tables don't exist:

```bash
python scripts/init_db.py
```

### 3. Run

```bash
python run.py
```

Open http://localhost:8000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/trends` | GET | List all trends |
| `/api/trends/by-id/{id}` | GET | Get trend by template_id |
| `/api/trends/by-code/{code}` | GET | Get trend by trend_code |
| `/api/trends` | POST | Create new trend |
| `/api/trends/{id}` | PUT | Update existing trend |
| `/api/execute` | POST | Execute SQL with params |
| `/api/schema` | GET | Database schema for autocomplete |

## SQL Contract

All trend queries must return:

- `cycleno` (numeric, sorted)
- `value` (numeric)
- `series` (string label)

## Docker

```bash
# Build and run
docker-compose up -d

# App at http://localhost:8000
```

Set `DB_HOST`, `DB_USER`, `DB_PASSWORD` in `.env` to point to your MySQL instance.

## Project Structure

```
OMS BlendTwin/
├── app/
│   ├── main.py       # FastAPI app
│   ├── models.py     # SQLAlchemy models
│   ├── database.py   # Session setup
│   └── services.py   # Business logic
├── config/
│   └── database.py   # Connection config (env vars)
├── static/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── scripts/
│   └── init_db.py    # Create tables if needed
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## License

OMS BlendTwin Program
