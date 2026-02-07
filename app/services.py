"""Business logic for trends, SQL execution, and parameter substitution."""
import logging
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import SQLTemplate, TrendPlot, TrendParameter

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"cycleno", "value", "series"}


def list_trends(db: Session) -> List[Dict[str, Any]]:
    """List all SQL templates (trends) with basic info."""
    rows = db.query(SQLTemplate).filter(SQLTemplate.is_active == True).all()
    return [
        {
            "template_id": r.template_id,
            "trend_code": r.trend_code,
            "trend_name": r.trend_name or r.trend_code,
            "is_active": r.is_active,
            "last_updated_on": r.last_updated_on.isoformat() if r.last_updated_on else None,
        }
        for r in rows
    ]


def get_trend_by_id(db: Session, template_id: int) -> Optional[Dict[str, Any]]:
    """Get single trend template by ID."""
    t = db.query(SQLTemplate).filter(SQLTemplate.template_id == template_id).first()
    if not t:
        return None
    return _template_to_dict(t, db)


def get_trend_by_code(db: Session, trend_code: str) -> Optional[Dict[str, Any]]:
    """Get trend template by trend_code."""
    t = db.query(SQLTemplate).filter(SQLTemplate.trend_code == trend_code).first()
    if not t:
        return None
    return _template_to_dict(t, db)


def _template_to_dict(t: SQLTemplate, db: Session) -> Dict[str, Any]:
    """Convert template + plot config + params to full dict."""
    plot = db.query(TrendPlot).filter(TrendPlot.trend_code == t.trend_code).first()
    params = db.query(TrendParameter).filter(TrendParameter.trend_code == t.trend_code).order_by(TrendParameter.display_order).all()

    return {
        "template_id": t.template_id,
        "trend_code": t.trend_code,
        "trend_name": t.trend_name or t.trend_code,
        "sql_template": t.sql_template or "",
        "is_active": t.is_active,
        "last_updated_on": t.last_updated_on.isoformat() if t.last_updated_on else None,
        "plot_config": {
            "x_col": plot.x_col if plot else "cycleno",
            "y_col": plot.y_col if plot else "value",
            "series_col": plot.series_col if plot else "series",
            "plot_type": plot.plot_type if plot else "line",
            "title": plot.title if plot else "",
            "x_label": plot.x_label if plot else "Cycle",
            "y_label": plot.y_label if plot else "Value",
        } if plot else {},
        "parameters": [
            {
                "param_name": p.param_name,
                "param_type": p.param_type or "string",
                "is_required": p.is_required,
                "default_value": p.default_value,
                "ui_label": p.ui_label or p.param_name,
                "display_order": p.display_order,
            }
            for p in params
        ],
    }


def substitute_parameters(sql: str, params: Dict[str, Any]) -> str:
    """
    Substitute :param_name placeholders in SQL with values.
    Uses safe string replacement for simple params.
    """
    result = sql
    for key, val in params.items():
        placeholder = f":{key}"
        if placeholder in result:
            if val is None:
                s = "NULL"
            elif isinstance(val, (int, float)):
                s = str(val)
            else:
                s = str(val).replace("'", "''")
                s = f"'{s}'"
            result = result.replace(placeholder, s)
    return result


def execute_query(db: Session, sql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute SQL and return results as list of dicts.
    Validates output has cycleno, value, series (or uses first 3 cols as fallback).
    """
    params = params or {}
    rendered = substitute_parameters(sql, params)
    try:
        result = db.execute(text(rendered))
        rows = result.fetchall()
        columns = list(result.keys())
        df = pd.DataFrame(rows, columns=columns)
    except Exception as e:
        logger.exception("Query execution failed")
        return {"error": str(e), "rows": [], "columns": []}

    if df.empty:
        return {"rows": [], "columns": list(df.columns), "error": None}

    cols = list(df.columns)
    missing = REQUIRED_COLUMNS - set(c.lower() for c in cols)
    if missing:
        return {"error": f"Result must include columns: cycleno, value, series. Missing: {missing}", "rows": [], "columns": cols}

    # Sort by cycleno
    cycleno_col = next(c for c in cols if c.lower() == "cycleno")
    df = df.sort_values(cycleno_col)

    rows = df.to_dict(orient="records")
    for r in rows:
        for k, v in list(r.items()):
            if pd.isna(v):
                r[k] = None
            elif hasattr(v, "item"):
                r[k] = v.item() if hasattr(v, "item") else float(v)

    return {"rows": rows, "columns": cols, "error": None}


def create_template(db: Session, trend_code: str, trend_name: str, sql_template: str) -> Dict[str, Any]:
    """Create new SQL template."""
    t = SQLTemplate(trend_code=trend_code, trend_name=trend_name, sql_template=sql_template)
    db.add(t)
    db.commit()
    db.refresh(t)
    return _template_to_dict(t, db)


def update_template(db: Session, template_id: int, sql_template: str, trend_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Update existing SQL template."""
    t = db.query(SQLTemplate).filter(SQLTemplate.template_id == template_id).first()
    if not t:
        return None
    t.sql_template = sql_template
    if trend_name is not None:
        t.trend_name = trend_name
    db.commit()
    db.refresh(t)
    return _template_to_dict(t, db)


def get_schema(db: Session) -> Dict[str, List[str]]:
    """Get table names and columns for query builder autocomplete."""
    result = {}
    try:
        rows = db.execute(text("SHOW TABLES")).fetchall()
        tables = [list(r)[0] for r in rows]
        for table in tables:
            cols = db.execute(text(f"SHOW COLUMNS FROM `{table}`")).fetchall()
            result[table] = [c[0] for c in cols]
    except Exception as e:
        logger.exception("Schema fetch failed")
        return {"error": str(e)}
    return result
