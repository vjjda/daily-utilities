# Path: utils/constants.py
from pathlib import Path
from typing import Final, Dict


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent


LOG_DIR_NAME: Final[str] = "logs"

LOG_DIR_PATH: Final[Path] = PROJECT_ROOT / LOG_DIR_NAME


CONSOLE_LOG_LEVEL: Final[str] = "INFO"

FILE_LOG_LEVEL: Final[str] = "DEBUG"


DEFAULT_EXTENSIONS_LANG_MAP: Final[Dict[str, str]] = {
    "py": "python",
    "pyi": "python",
    "js": "javascript",
    "sh": "shell",
    "bash": "shell",
    "zsh": "shell",
}