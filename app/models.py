"""
SQLAlchemy models for BlendTwin configuration tables.
Column names match typical schema from SOW; may need adjustment for actual DB.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SQLTemplate(Base):
    """bts_cfg_sql_templates"""
    __tablename__ = "bts_cfg_sql_templates"

    template_id = Column(String(50), primary_key=True)
    refid = Column(String(50), nullable=True)
    trend_id = Column(String(50), nullable=False, index=True)  # Was trend_code
    trend_name = Column(String(255), nullable=True)
    sql_template = Column(Text, nullable=True)
    last_updated_on = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # is_active removed


class TrendPlot(Base):
    """bts_cfg_trend_plots"""
    __tablename__ = "bts_cfg_trend_plots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trend_id = Column(String(50), nullable=False, index=True) 
    refid = Column(String(50), nullable=True)
    
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
    axis_side = Column(String(50), nullable=True)


class TrendParameter(Base):
    """bts_Trend_Parameters (Note Case)"""
    __tablename__ = "bts_Trend_Parameters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    refid = Column(String(50), nullable=True)
    trendid = Column(String(50), nullable=False, index=True) # trend_code
    parameter = Column(String(50), nullable=False) # param_name
    type = Column(String(50), default="string") # param_type
    required = Column(String(50), default="N") # is_required (Y/N)
    multi = Column(String(50), default="N")
    default = Column(String(50), nullable=True) # default_value
