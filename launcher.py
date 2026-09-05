"""
launcher.py
FastAPI backend runs on a background thread (uvicorn handles this fine).
Streamlit MUST run on the main thread because it installs signal handlers
(Ctrl+C support) which only work in the main thread of the main interpreter.

Place this file in the project ROOT: E:\\Projects\\seo-agent\\launcher.py
"""

import os
import sys
import time
import threading
import webbrowser
import multiprocessing

# ---------------- CONFIG ----------------
STREAMLIT_FILE = "frontend/app.py"
DB_FILE = "seo_agent.db"
ENV_FILE = ".env"
FASTAPI_PORT = 8000
STREAMLIT_PORT = 8501
# -----------------------------------------

os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHERUSAGESTATS"] = "false"
os.environ["STREAMLIT_GLOBAL_DEVELOPMENTMODE"] = "false"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# Tell Playwright to look for its browser inside our bundled exe instead
# of the default %LOCALAPPDATA%\ms-playwright location, which won't
# exist on the receiver's machine.
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = resource_path("ms-playwright")

def load_env():
    from dotenv import load_dotenv
    env_path = resource_path(ENV_FILE)
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        print(f"Warning: .env not found at {env_path}")


def ensure_working_dir():
    exe_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
    target_db = os.path.join(exe_dir, DB_FILE)
    if not os.path.exists(target_db):
        bundled_db = resource_path(DB_FILE)
        if os.path.exists(bundled_db):
            import shutil
            shutil.copy(bundled_db, target_db)
    os.chdir(exe_dir)


def start_fastapi():
    """Runs fine on a background thread — uvicorn skips signal handlers
    automatically when it detects it's not on the main thread."""
    import uvicorn
    from backend.main import app
    uvicorn.run(app, host="127.0.0.1", port=FASTAPI_PORT, log_level="info")


def open_browser_when_ready():
    """Runs on a background thread: waits for Streamlit's port to come up,
    then opens the browser. Doesn't block the main thread."""
    import socket
    start_time = time.time()
    while time.time() - start_time < 30:
        try:
            with socket.create_connection(("127.0.0.1", STREAMLIT_PORT), timeout=1):
                webbrowser.open(f"http://127.0.0.1:{STREAMLIT_PORT}")
                return
        except OSError:
            time.sleep(0.5)
    print("Server took too long to start. Please open http://127.0.0.1:8501 manually.")


def start_streamlit_blocking():
    """MUST run on the main thread — this is what fixes the signal handler crash."""
    from streamlit.web import cli as stcli

    script_path = resource_path(STREAMLIT_FILE)
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--server.port", str(STREAMLIT_PORT),
        "--server.address", "127.0.0.1",
        "--server.headless", "true",
        "--global.developmentMode=false",
    ]
    stcli.main()  # blocks here until the app is closed


def main():
    print("Starting SEOPilotAI, please wait...")

    ensure_working_dir()
    load_env()

    # FastAPI backend: background thread (safe, uvicorn handles non-main-thread fine)
    fastapi_thread = threading.Thread(target=start_fastapi, daemon=True)
    fastapi_thread.start()

    # Browser opener: background thread, just watches the port
    browser_thread = threading.Thread(target=open_browser_when_ready, daemon=True)
    browser_thread.start()

    # Streamlit: MAIN thread, blocking call (required for its signal handlers)
    start_streamlit_blocking()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()