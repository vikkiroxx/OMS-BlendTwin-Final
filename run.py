"""Run BlendTwin Trend Query Workbench. Usage: python run.py"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    
    # Check if SSH tunnel is needed
    use_ssh = os.getenv("USE_SSH_TUNNEL", "false").lower().strip() == "true"
    server = None
    
    if use_ssh:
        try:
            from sshtunnel import SSHTunnelForwarder
            
            ssh_host = os.getenv("SSH_HOST")
            ssh_port = int(os.getenv("SSH_PORT", 22))
            ssh_user = os.getenv("SSH_USER")
            ssh_password = os.getenv("SSH_PASSWORD")
            
            # The remote database host/port as seen from the SSH server
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = int(os.getenv("DB_PORT", 3306))
            
            print(f"Starting SSH tunnel to {ssh_host}@{ssh_port}...")
            server = SSHTunnelForwarder(
                (ssh_host, ssh_port),
                ssh_username=ssh_user,
                ssh_password=ssh_password,
                remote_bind_address=(db_host, db_port)
            )
            server.start()
            
            print(f"SSH tunnel established. Forwarding localhost:{server.local_bind_port} -> {db_host}:{db_port}", flush=True)
            
            # Override environment variables for the application (must be set before uvicorn spawns workers)
            os.environ["DB_HOST"] = "127.0.0.1"
            os.environ["DB_PORT"] = str(server.local_bind_port)
            print(f"DB connection: {os.environ['DB_HOST']}:{os.environ['DB_PORT']}", flush=True)
            
        except ImportError:
            print("Error: 'sshtunnel' library not found. Install it with: pip install sshtunnel")
            sys.exit(1)
        except Exception as e:
            print(f"Error starting SSH tunnel: {e}")
            if server:
                server.stop()
            sys.exit(1)

    port = int(os.getenv("PORT", "8000"))
    try:
        # Use reload=False when using SSH tunnel - reloader subprocess may not inherit env vars correctly
        use_reload = not use_ssh
        uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=use_reload)
    finally:
        if server:
            print("Closing SSH tunnel...")
            server.stop()
