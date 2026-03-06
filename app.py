from pathlib import Path
import runpy
import sys
import types


ROOT = Path(__file__).parent
PKG_DIR = ROOT / "app"
APP_FILE = PKG_DIR / "streamlit_app.py"

# Workaround defensivo para conflito de nome entre app.py e pacote app no Python 3.14.
pkg = types.ModuleType("app")
pkg.__path__ = [str(PKG_DIR)]
sys.modules["app"] = pkg

try:
    from app.streamlit_app import *  # noqa: F401,F403
except Exception:
    runpy.run_path(str(APP_FILE), run_name="__main__")
