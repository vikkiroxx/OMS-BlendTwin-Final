"""
Add config_json and plot_order columns to bts_cfg_trend_plots.
Run: python scripts/migrate_plots_table.py

Uses SSH tunnel if USE_SSH_TUNNEL=true (same as run.py).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# Start SSH tunnel if needed (same logic as run.py)
use_ssh = os.getenv("USE_SSH_TUNNEL", "false").lower().strip() == "true"
server = None

if use_ssh:
    try:
        from sshtunnel import SSHTunnelForwarder

        ssh_host = os.getenv("SSH_HOST")
        ssh_port = int(os.getenv("SSH_PORT", 22))
        ssh_user = os.getenv("SSH_USER")
        ssh_password = os.getenv("SSH_PASSWORD")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", 3306))

        print("Starting SSH tunnel...")
        server = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(db_host, db_port)
        )
        server.start()
        os.environ["DB_HOST"] = "127.0.0.1"
        os.environ["DB_PORT"] = str(server.local_bind_port)
        print(f"SSH tunnel established. DB: 127.0.0.1:{server.local_bind_port}")
    except Exception as e:
        print(f"Error starting SSH tunnel: {e}")
        sys.exit(1)

try:
    from sqlalchemy import text
    from app.database import SessionLocal

    def migrate():
        db = SessionLocal()
        try:
            result = db.execute(text("SHOW COLUMNS FROM bts_cfg_trend_plots LIKE 'config_json'"))
            if result.fetchone() is None:
                print("Adding config_json column...")
                db.execute(text("ALTER TABLE bts_cfg_trend_plots ADD COLUMN config_json TEXT NULL"))
                db.commit()
                print("Added config_json.")
            else:
                print("config_json already exists.")

            result = db.execute(text("SHOW COLUMNS FROM bts_cfg_trend_plots LIKE 'plot_order'"))
            if result.fetchone() is None:
                print("Adding plot_order column...")
                db.execute(text("ALTER TABLE bts_cfg_trend_plots ADD COLUMN plot_order INT DEFAULT 0"))
                db.commit()
                print("Added plot_order.")
            else:
                print("plot_order already exists.")

            print("Migration complete.")
        except Exception as e:
            print(f"Error: {e}")
            db.rollback()
        finally:
            db.close()

    if __name__ == "__main__":
        migrate()
finally:
    if server:
        print("Closing SSH tunnel...")
        server.stop()
