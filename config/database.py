"""
Database connection configuration for BlendTwin Trend Query Workbench.
Loads credentials from environment variables - never hardcode credentials.
"""
import os
from typing import Optional
from urllib.parse import quote_plus

# Optional: use python-dotenv to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Run without .env if dotenv not installed


def get_db_url(use_ssh: Optional[bool] = None) -> str:
    """
    Build SQLAlchemy database URL from environment variables.
    
    Connection source: OMS_Connections.xlsx (VPS-BlendTwin-Staging)
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "blendtwin")
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    charset = os.getenv("DB_CHARSET", "utf8")
    
    if use_ssh is None:
        use_ssh = os.getenv("USE_SSH_TUNNEL", "false").lower() == "true"
    
    # When using SSH tunnel, connect to localhost (tunnel endpoint)
    if use_ssh:
        host = "127.0.0.1"
    
    # URL-encode credentials (passwords with @, !, etc. break URL parsing)
    user_enc = quote_plus(user)
    password_enc = quote_plus(password)
    return f"mysql+pymysql://{user_enc}:{password_enc}@{host}:{port}/{name}?charset={charset}"


def get_ssh_config() -> dict:
    """SSH tunnel config for connecting to VPS-bound MySQL from local dev."""
    return {
        "host": os.getenv("SSH_HOST", ""),
        "port": int(os.getenv("SSH_PORT", "22")),
        "username": os.getenv("SSH_USER", ""),
        "password": os.getenv("SSH_PASSWORD", ""),
    }


# Column mapping from OMS_Connections.xlsx
CONNECTION_COLUMNS = [
    "Connection Name",
    "Website URL",
    "Tested ?",
    "Category",
    "Database Type",
    "MySQL Host",
    "SSH Host",
    "SSH Port",
    "SSH User",
    "SSH Password",
    "Database",
    "Database Host",
    "MySQL Port",
    "MySQL User",
    "MySQL Password",
    "Database.1",
    "Extra Parameters",
    "Putty Session Name",
]
