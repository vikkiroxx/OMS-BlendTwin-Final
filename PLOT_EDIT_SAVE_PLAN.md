# Plot Edit & Save to bts_cfg_trend_plots — Implementation Plan

## Context

Another app will use the saved SQL templates and plot configs to generate the same graphs. Users need to:
1. **Edit** a plot — change config and regenerate (in-memory)
2. **Save** a plot — persist to `bts_cfg_trend_plots` so the other platform can render it

---

## Current bts_cfg_trend_plots Schema

| Column      | Type         | Purpose                          |
|-------------|--------------|----------------------------------|
| id          | INT PK       | Auto-increment                   |
| trend_id    | VARCHAR(50)  | Links to trend (trend_code)      |
| refid       | VARCHAR(50)  | Optional reference               |
| x_col       | VARCHAR(50)  | X-axis column (e.g. cycleno)     |
| y_col       | VARCHAR(50)  | Y-axis column (legacy single)    |
| series_col  | VARCHAR(50)  | Series column (legacy)           |
| plot_type   | VARCHAR(20)  | line, bar, pie                   |
| y_axis      | VARCHAR(10)  | left/right (legacy)              |
| title       | VARCHAR(255) | Plot title                       |
| x_label     | VARCHAR(100) | X-axis label                     |
| y_label     | VARCHAR(100) | Y-axis label                     |
| axis_side   | VARCHAR(50)  | Primary/Secondary                |
| sort_numeric| VARCHAR(1)   | Y/N                              |
| legend_order| VARCHAR(255) | Optional                         |

**Gap:** Current schema supports one series per row (y_axis = series name). Our plots use **multi-series with per-series colors** (`y_cols: [{col, label, color}]`). We need to store this.

---

## Table Modification Required

Add one column:

| Column       | Type | Purpose |
|--------------|------|---------|
| **config_json** | TEXT | Full plot config as JSON. Stores: `{title, type, x_col, x_label, y_label, series_mode, y_cols: [{col, label, color}], pie_label_col, pie_value_col}` |

Add for display order:

| Column       | Type | Purpose |
|--------------|------|---------|
| **plot_order** | INT  | Display order (1, 2, 3...). Default 0. |

**Migration SQL:**
```sql
ALTER TABLE bts_cfg_trend_plots 
  ADD COLUMN config_json TEXT NULL,
  ADD COLUMN plot_order INT DEFAULT 0;
```

**Design:** One row = one complete plot. For new saves we use `config_json` as the source of truth. Legacy rows (without config_json) can still be read via x_col, y_col, etc.

---

## Config JSON Structure

```json
{
  "title": "Duration Vs Blend No",
  "type": "line",
  "x_col": "cycleno",
  "x_label": "Blend Cycle (5 min)",
  "y_label": "RefID",
  "series_mode": "multi_col",
  "y_cols": [
    { "col": "Stream Quality", "label": "Stream Quality", "color": "#9a6700" },
    { "col": "CSTRModel", "label": "CSTRModel", "color": "#cf222e" },
    { "col": "LaggedModel", "label": "LaggedModel", "color": "#8250df" },
    { "col": "HybridModel", "label": "HybridModel", "color": "#1a7f37" }
  ]
}
```

For pie:
```json
{
  "title": "% Grade Distribution",
  "type": "pie",
  "pie_label_col": "grade",
  "pie_value_col": "value"
}
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/trends/{template_id}/plots` | List saved plots for trend |
| POST | `/api/trends/{template_id}/plots` | Save new plot |
| PUT | `/api/trends/{template_id}/plots/{plot_id}` | Update saved plot |
| DELETE | `/api/trends/{template_id}/plots/{plot_id}` | Delete saved plot |

---

## Frontend Changes

### Plot Card (per plot)

| Button | Action |
|--------|--------|
| **Edit** | Open Add Plot modal pre-filled with current config. Button becomes "Update". On Update → replace plot at index, regenerate. |
| **Save** | POST to `/api/trends/{id}/plots` with config. Show "Saved" badge. Store `saved_plot_id` on config. |
| **Remove** | Remove from canvas (existing). If saved, optionally DELETE from API. |

### Save Button States

- **Save** — plot not yet saved to DB
- **Saved** (badge) — plot persisted. Clicking could open Edit modal to update and re-save.

### Flow

1. User executes query → adds plots (in-memory `plotConfigs`)
2. **Edit** → modal opens with current values → user changes → **Update** → `plotConfigs[idx] = newConfig`, `renderPlotsCanvas()`
3. **Save** → POST config to API → plot saved. Card shows "Saved" badge, config gets `id` for future updates.
4. When loading trend: GET `/api/trends/{id}/plots` to show which plots are saved. After execute, user can "Load saved plots" to pre-populate canvas.

---

## Implementation Order

1. **DB migration** — Add `config_json`, `plot_order` to bts_cfg_trend_plots
2. **Model** — Add columns to TrendPlot
3. **Services** — `list_plots`, `create_plot`, `update_plot`, `delete_plot`
4. **API** — Four endpoints
5. **Frontend** — Edit button, Save button, modal pre-fill for Edit, saved state badge

---

## Run Migration

Before using the new features, run:

```bash
cd OMS-BlendTwin
python scripts/migrate_plots_table.py
```

This adds `config_json` and `plot_order` columns to `bts_cfg_trend_plots` if they don't exist.
