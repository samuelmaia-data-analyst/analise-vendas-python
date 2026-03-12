from __future__ import annotations

from pathlib import Path
import runpy


def run_streamlit_app() -> None:
    root = Path(__file__).resolve().parents[2]
    app_file = root / "app" / "streamlit_app.py"
    runpy.run_path(str(app_file), run_name="__main__")
