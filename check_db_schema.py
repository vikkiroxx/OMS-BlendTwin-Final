import os
import sys
from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
import pymysql

load_dotenv()

def check_schema():
    use_ssh = os.getenv("USE_SSH_TUNNEL", "false").lower() == "true"
    ssh_host = os.getenv("SSH_HOST")
    ssh_port = int(os.getenv("SSH_PORT", 22))
    ssh_user = os.getenv("SSH_USER")
    ssh_password = os.getenv("SSH_PASSWORD")
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", 3306))
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
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
            print(f"SSH Tunnel established. Local port: {local_port}")
            connect_host = "127.0.0.1"
            connect_port = local_port
        else:
            connect_host = db_host
            connect_port = db_port

        print(f"Connecting to database at {connect_host}:{connect_port}...")
        conn = pymysql.connect(
            host=connect_host,
            port=connect_port,
            user=db_user,
            password=db_password
        )
        
        with conn.cursor() as cursor:
            print("\nSearching for schemas with 'tqts'...")
            cursor.execute("SHOW SCHEMAS LIKE '%tqts%'")
            schemas = cursor.fetchall()
            
            if not schemas:
                print("No schemas found containing 'tqts'.")
                cursor.execute("SHOW SCHEMAS")
                all_schemas = cursor.fetchall()
                print("Available schemas:", [s[0] for s in all_schemas])
            else:
                for schema in schemas:
                    schema_name = schema[0]
                    print(f"\nFound schema: {schema_name}")
                    print(f"Tables in {schema_name}:")
                    cursor.execute(f"USE {schema_name}")
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    for table in tables:
                        print(f" - {table[0]}")
                        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if server:
            server.stop()

if __name__ == "__main__":
    check_schema()
