import os
import sys
import time
import threading
import webbrowser
import multiprocessing
import subprocess

STREAMLIT_FILE = "frontend/app.py"
DB_FILE = "seo_agent.db"
ENV_FILE = ".env"

FASTAPI_PORT = 8000
STREAMLIT_PORT = 8501

os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
os.environ["STREAMLIT_BROWSER_GATHERUSAGESTATS"] = "false"
os.environ["STREAMLIT_GLOBAL_DEVELOPMENTMODE"] = "false"


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if getattr(sys, "frozen", False):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = resource_path("ms-playwright")


def load_env():
    from dotenv import load_dotenv

    env_path = resource_path(ENV_FILE)

    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        print(f"Warning: .env not found at {env_path}")


def ensure_working_dir():
    exe_dir = os.path.dirname(
        os.path.abspath(
            sys.executable if getattr(sys, "frozen", False) else __file__
        )
    )

    target_db = os.path.join(exe_dir, DB_FILE)

    if not os.path.exists(target_db):
        bundled_db = resource_path(DB_FILE)

        if os.path.exists(bundled_db):
            import shutil
            shutil.copy(bundled_db, target_db)

    os.chdir(exe_dir)


def start_fastapi():
    import uvicorn
    from backend.main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=FASTAPI_PORT,
        log_level="info",
    )


def wait_for_port(port, timeout=30):
    import socket

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(
                ("127.0.0.1", port),
                timeout=1,
            ):
                return True

        except OSError:
            time.sleep(0.5)

    return False


def start_streamlit():
    script_path = resource_path(STREAMLIT_FILE)

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        script_path,
        "--server.port",
        str(STREAMLIT_PORT),
        "--server.address",
        "127.0.0.1",
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]

    return subprocess.Popen(
        command,
        cwd=os.getcwd(),
    )


def open_browser_when_ready():
    if wait_for_port(STREAMLIT_PORT, timeout=60):
        webbrowser.open(
            f"http://127.0.0.1:{STREAMLIT_PORT}"
        )
    else:
        print(
            "Server took too long to start. "
            "Please open http://127.0.0.1:8501 manually."
        )


def main():
    print("Starting SEOPilotAI, please wait...")

    ensure_working_dir()
    load_env()

    # Start FastAPI only once
    fastapi_thread = threading.Thread(
        target=start_fastapi,
        daemon=True,
    )

    fastapi_thread.start()

    # Wait until FastAPI is ready
    if not wait_for_port(FASTAPI_PORT, timeout=30):
        print("FastAPI backend did not start on port 8000.")
        return

    # Start Streamlit as a separate process
    streamlit_process = start_streamlit()

    # Open browser after Streamlit starts
    browser_thread = threading.Thread(
        target=open_browser_when_ready,
        daemon=True,
    )

    browser_thread.start()

    try:
        streamlit_process.wait()

    except KeyboardInterrupt:
        print("\nStopping SEOPilotAI...")

    finally:
        if streamlit_process.poll() is None:
            streamlit_process.terminate()

            try:
                streamlit_process.wait(timeout=5)

            except subprocess.TimeoutExpired:
                streamlit_process.kill()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()