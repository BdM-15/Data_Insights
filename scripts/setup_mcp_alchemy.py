"""
Automated setup and launch for mcp-alchemy MCP server (cross-platform, Python-only)
- Installs uv if missing
- Prompts for PostgreSQL connection info (or uses env vars)
- Launches mcp-alchemy using uvx
"""
import os
import subprocess
import sys
import shutil

def ensure_uv():
    """Ensure uv is installed, install via pip if missing."""
    if shutil.which("uv") is None:
        print("[INFO] uv not found. Installing uv via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
    else:
        print("[INFO] uv is already installed.")

def prompt_env(var, prompt, default=None, secret=False):
    val = os.environ.get(var)
    if val:
        return val
    if secret:
        import getpass
        val = getpass.getpass(f"{prompt}: ")
    else:
        val = input(f"{prompt}{f' [{default}]' if default else ''}: ")
        if not val and default:
            val = default
    return val

def main():
    ensure_uv()
    pg_user = prompt_env("PGUSER", "PostgreSQL user", default="postgres")
    pg_password = prompt_env("PGPASSWORD", "PostgreSQL password", secret=True)
    pg_host = prompt_env("PGHOST", "PostgreSQL host", default="localhost")
    pg_port = prompt_env("PGPORT", "PostgreSQL port", default="5432")
    pg_db = prompt_env("PGDATABASE", "PostgreSQL database", default="capture_insights")
    db_url = f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    env = os.environ.copy()
    env["DB_URL"] = db_url
    env["UV_REFRESH_PACKAGE"] = "mcp-alchemy"
    print("[INFO] Launching mcp-alchemy MCP server...")
    cmd = ["uvx", "--from", "mcp-alchemy", "--with", "psycopg2-binary", "--refresh-package", "mcp-alchemy", "mcp-alchemy"]
    try:
        subprocess.run(cmd, env=env, check=True)
    except FileNotFoundError:
        print("[ERROR] uvx not found. Please ensure uv is installed and on your PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] mcp-alchemy failed to start: {e}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
