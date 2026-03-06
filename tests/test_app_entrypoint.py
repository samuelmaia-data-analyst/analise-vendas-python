import runpy
from pathlib import Path


def test_app_entrypoint_runs_without_import_error():
    app_file = Path(__file__).resolve().parents[1] / "app.py"
    runpy.run_path(str(app_file), run_name="__main__")
