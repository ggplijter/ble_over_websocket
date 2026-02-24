from os import makedirs
from pathlib import Path

FILEDIR = Path(__file__).parent
ROOT_DIR = (FILEDIR / "../.").resolve()
PYTHON_EXE = Path(ROOT_DIR) / ".venv" / "Scripts" / "python.exe"

LOGGING_CONFIG = ROOT_DIR / "./utils/logging_config.json"

LOG_DIR = ROOT_DIR / "log"



makedirs(LOG_DIR, exist_ok=True)


