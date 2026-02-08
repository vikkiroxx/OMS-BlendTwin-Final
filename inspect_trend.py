import os
import pymysql
from sshtunnel import SSHTunnelForwarder
from config.database import get_ssh_config
from dotenv import load_dotenv

load_dotenv()

def inspect_t002():
    ssh_config = get_ssh_config()
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "3306"))

    try:
        print(f"Connecting to {ssh_config['host']} via SSH...")
        with SSHTunnelForwarder(
            (ssh_config['host'], ssh_config['port']),
            ssh_username=ssh_config['username'],
            ssh_password=ssh_config['password'],
            remote_bind_address=('localhost', 3306)
        ) as tunnel:
            tunnel.start()
            print(f"SSH tunnel established at localhost:{tunnel.local_bind_port}")
            
            conn = pymysql.connect(
                host='127.0.0.1',
                port=tunnel.local_bind_port,
                user=db_user,
                password=db_pass,
                database=db_name,
                cursorclass=pymysql.cursors.DictCursor
            )
            
            try:
                with conn.cursor() as cursor:
                    # Cleanup duplicates for T002
                    print("\n--- DELETING DUPLICATE PARAMETERS (9, 10) ---")
                    cursor.execute("DELETE FROM bts_Trend_Parameters WHERE id IN (9, 10)")
                    conn.commit()
                    print("Deletion successful.")

                    # Check parameters for T002
                    print("\n--- PARAMETERS FOR T002 ---")
                    cursor.execute("SELECT * FROM bts_Trend_Parameters WHERE trendid IN ('T002', 'T2')")
                    rows = cursor.fetchall()
                    for r in rows:
                        print(r)
                    
                    # Check template for T002
                    print("\n--- TEMPLATE FOR T002 ---")
                    cursor.execute("SELECT * FROM bts_cfg_sql_templates WHERE trend_id = 'T002'")
                    t = cursor.fetchone()
                    if t:
                        print(f"ID: {t['template_id']}, Name: {t['trend_name']}")
                        print(f"SQL: {t['sql_template']}")
                    else:
                        print("T002 not found")

            finally:
                conn.close()

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    inspect_t002()
