import os
import sys
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import pymysql

load_dotenv()

def check_table_columns():
    use_ssh = os.getenv("USE_SSH_TUNNEL", "false").lower() == "true"
    ssh_host = os.getenv("SSH_HOST")
    ssh_port = int(os.getenv("SSH_PORT", 22))
    ssh_user = os.getenv("SSH_USER")
    ssh_password = os.getenv("SSH_PASSWORD")
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", 3306))
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "ecp_tqts")
    
    server = None
    
    try:
        if use_ssh:
            print(f"Connecting via SSH to {ssh_host}...")
            server = SSHTunnelForwarder(
                (ssh_host, ssh_port),
                ssh_username=ssh_user,
                ssh_password=ssh_password,
                remote_bind_address=(db_host, db_port)
            )
            server.start()
            local_port = server.local_bind_port
            connect_host = "127.0.0.1"
            connect_port = local_port
        else:
            connect_host = db_host
            connect_port = db_port

        print(f"Connecting to database {db_name} at {connect_host}:{connect_port}...")
        conn = pymysql.connect(
            host=connect_host,
            port=connect_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        
        tables_to_check = ["bts_cfg_sql_templates", "bts_cfg_trend_plots", "bts_cfg_trend_parameters"]
        
        with conn.cursor() as cursor:
            for table in tables_to_check:
                print(f"\n--- Columns in {table} ---")
                try:
                    cursor.execute(f"SHOW COLUMNS FROM {table}")
                    columns = cursor.fetchall()
                    print(f"{'Field':<20} {'Type':<20} {'Null':<5} {'Key':<5} {'Default':<10}")
                    print("-" * 65)
                    for col in columns:
                        # Field, Type, Null, Key, Default, Extra
                        print(f"{col[0]:<20} {col[1]:<20} {col[2]:<5} {col[3]:<5} {str(col[4]):<10}")
                except Exception as e:
                    print(f"Error checking table {table}: {e}")
                        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if server:
            server.stop()

if __name__ == "__main__":
    check_table_columns()
