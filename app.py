from pathlib import Path
import runpy


APP_FILE = Path(__file__).parent / "app" / "streamlit_app.py"
runpy.run_path(str(APP_FILE), run_name="__main__")
