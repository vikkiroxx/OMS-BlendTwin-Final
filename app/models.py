"""
SQLAlchemy models for BlendTwin configuration tables.
Column names match typical schema from SOW; may need adjustment for actual DB.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SQLTemplate(Base):
    """bts_cfg_sql_templates - CREATE + UPDATE target"""
    __tablename__ = "bts_cfg_sql_templates"

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    trend_code = Column(String(50), nullable=False, index=True)
    trend_name = Column(String(255), nullable=True)
    sql_template = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_updated_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TrendPlot(Base):
    """bts_cfg_trend_plots - READ only"""
    __tablename__ = "bts_cfg_trend_plots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trend_code = Column(String(50), nullable=False, index=True)
    x_col = Column(String(50), default="cycleno")
    y_col = Column(String(50), default="value")
    series_col = Column(String(50), default="series")
    plot_type = Column(String(20), default="line")
    y_axis = Column(String(10), default="left")
    sort_numeric = Column(String(1), default="Y")
    legend_order = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    x_label = Column(String(100), nullable=True)
    y_label = Column(String(100), nullable=True)


class TrendParameter(Base):
    """bts_cfg_trend_parameters - READ only, used for parameter panel"""
    __tablename__ = "bts_cfg_trend_parameters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trend_code = Column(String(50), nullable=False, index=True)
    param_name = Column(String(50), nullable=False)
    param_type = Column(String(20), default="string")
    is_required = Column(Boolean, default=False)
    default_value = Column(String(255), nullable=True)
    ui_label = Column(String(100), nullable=True)
    display_order = Column(Integer, default=0)
