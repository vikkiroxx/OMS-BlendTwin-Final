"""
BlendTwin Trend Query Workbench - FastAPI application.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import SessionLocal
from app.services import (
    list_trends,
    get_trend_by_id,
    get_trend_by_code,
    create_template,
    update_template,
    execute_query,
    get_schema,
    get_trend_params_list,
    delete_template,
    list_plots_for_trend,
    create_plot,
    update_plot,
    delete_plot,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project root for static files
ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # cleanup if needed


app = FastAPI(title="BlendTwin Trend Query Workbench", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic models ---
class ExecuteRequest(BaseModel):
    sql: str
    params: dict | None = None


class TrendParameterCreate(BaseModel):
    parameter: str
    type: str = "string"
    required: str = "Y"
    multi: str = "N"
    default: str | None = None


class CreateTrendRequest(BaseModel):
    trend_code: str
    trend_name: str
    sql_template: str
    refid: str | None = None
    template_id: str | None = None  # If different from trend_code
    parameters: list[TrendParameterCreate] | None = None  # BlendID added by default


class UpdateTrendRequest(BaseModel):
    sql_template: str
    trend_name: str | None = None


class PlotConfigBody(BaseModel):
    config: dict  # Full plot config: title, type, x_col, y_cols, colors, etc.


# --- API Routes ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/trends")
def api_list_trends(db: Session = Depends(get_db)):
    """List all trend templates."""
    try:
        trends = list_trends(db)
        return {"trends": trends}
    except Exception as e:
        logger.exception("List trends failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trends/by-id/{template_id}")
def api_get_trend_by_id(template_id: str, db: Session = Depends(get_db)):
    """Get trend by template_id."""
    try:
        trend = get_trend_by_id(db, template_id)
        if not trend:
            raise HTTPException(status_code=404, detail="Trend not found")
        return trend
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Get trend failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trends/by-code/{trend_code}")
def api_get_trend_by_code(trend_code: str, db: Session = Depends(get_db)):
    """Get trend by trend_code."""
    try:
        trend = get_trend_by_code(db, trend_code)
        if not trend:
            raise HTTPException(status_code=404, detail="Trend not found")
        return trend
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Get trend failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trends")
def api_create_trend(req: CreateTrendRequest, db: Session = Depends(get_db)):
    """Create new SQL template with optional refid and parameters."""
    try:
        trend = create_template(
            db,
            trend_code=req.trend_code,
            trend_name=req.trend_name,
            sql_template=req.sql_template,
            refid=req.refid,
            template_id=req.template_id,
            parameters=req.parameters,
        )
        return trend
    except Exception as e:
        logger.exception("Create trend failed")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/trends/{template_id}")
def api_update_trend(template_id: str, req: UpdateTrendRequest, db: Session = Depends(get_db)):
    """Update existing SQL template."""
    try:
        trend = update_template(db, template_id, req.sql_template, req.trend_name)
        if not trend:
            raise HTTPException(status_code=404, detail="Trend not found")
        return trend
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Update trend failed")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/trends/{template_id}")
def api_delete_trend(template_id: str, db: Session = Depends(get_db)):
    """Delete existing SQL template."""
    try:
        success = delete_template(db, template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Trend not found")
        return {"message": "Trend deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Delete trend failed")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/execute")
def api_execute(req: ExecuteRequest, db: Session = Depends(get_db)):
    """Execute SQL with optional parameters."""
    try:
        result = execute_query(db, req.sql, req.params)
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Execute failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schema")
def api_schema(db: Session = Depends(get_db)):
    """Get database schema for query builder autocomplete."""
    try:
        return get_schema(db)
    except Exception as e:
        logger.exception("Schema fetch failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trend-params")
def api_trend_params(db: Session = Depends(get_db)):
    """Get list of allowed trend parameter names from trend_parms column or fallback."""
    try:
        params = get_trend_params_list(db)
        return {"params": params}
    except Exception as e:
        logger.exception("Trend params fetch failed")
        raise HTTPException(status_code=500, detail=str(e))


# --- Plot CRUD (bts_cfg_trend_plots) ---

@app.get("/api/trends/{template_id}/plots")
def api_list_plots(template_id: str, db: Session = Depends(get_db)):
    """List saved plots for a trend."""
    try:
        plots = list_plots_for_trend(db, template_id)
        return {"plots": plots}
    except Exception as e:
        logger.exception("List plots failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trends/{template_id}/plots")
def api_create_plot(template_id: str, req: PlotConfigBody, db: Session = Depends(get_db)):
    """Save a new plot config to bts_cfg_trend_plots."""
    try:
        plot = create_plot(db, template_id, req.config)
        if not plot:
            raise HTTPException(status_code=404, detail="Trend not found")
        return plot
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Create plot failed")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/trends/{template_id}/plots/{plot_id}")
def api_update_plot(template_id: str, plot_id: int, req: PlotConfigBody, db: Session = Depends(get_db)):
    """Update an existing saved plot."""
    try:
        plot = update_plot(db, template_id, plot_id, req.config)
        if not plot:
            raise HTTPException(status_code=404, detail="Plot or trend not found")
        return plot
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Update plot failed")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/trends/{template_id}/plots/{plot_id}")
def api_delete_plot(template_id: str, plot_id: int, db: Session = Depends(get_db)):
    """Delete a saved plot."""
    try:
        success = delete_plot(db, template_id, plot_id)
        if not success:
            raise HTTPException(status_code=404, detail="Plot or trend not found")
        return {"message": "Plot deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Delete plot failed")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dropdown-options")
def api_dropdown_options(db: Session = Depends(get_db)):
    """Get dropdown options from bts_DropDownList for Quality, Model, Stream, Tank No."""
    from sqlalchemy import text
    result = {}
    mappings = [
        ("quality", "quality"),
        ("streams", "streams"),
        ("tank_no", "tank_no"),
        ("ai_mixing_model", "ai_mixing_model"),
    ]
    for col, key in mappings:
        try:
            rows = db.execute(
                text(f"SELECT DISTINCT `{col}` FROM bts_DropDownList WHERE `{col}` IS NOT NULL AND `{col}` != '' ORDER BY `{col}`")
            ).fetchall()
            result[key] = [str(r[0]).strip() for r in rows if r[0]]
        except Exception:
            result[key] = []
    return result


# --- Static files & SPA ---
static_dir = ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def index():
    """Serve main SPA."""
    index_path = ROOT / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "BlendTwin Trend Query Workbench API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
