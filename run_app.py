import os
import sys
import webbrowser
import streamlit.web.cli as stcli


def resolve_path(relative_path):
    """Finds the absolute path to a file inside the temporary bundle directory

    created by PyInstaller when the executable is launched. Fallback points
    to standard current directory execution during manual testing scripts.
    """
    try:
        # PyInstaller creates a temporary folder and stores its path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def run_app_instance():
    """Locates the unified user interface file and passes execution args

    directly into Streamlit's core command line interface modules.
    """
    # Pinpoint exactly where the multi-page main dashboard is nested inside the exe payload
    script_path = resolve_path("main_app.py")

    # Replicate standard terminal args programmatically to start the server smoothly
    sys.argv = [
        "streamlit",
        "run",
        script_path,
        "--global.developmentMode=false",
        "--server.port=8507",
    ]

    # Hand execution tracking flags over to Streamlit's main thread line
    stcli.main()


if __name__ == "__main__":
    # 1. Open the local machine's native web browser to point to our dashboard port address
    webbrowser.open("http://localhost:8501")

    # 2. Boot up the hidden background system server process loops instantly
    run_app_instance()
