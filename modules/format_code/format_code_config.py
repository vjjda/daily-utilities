# Path: modules/format_code/format_code_config.py
from pathlib import Path
from typing import Any, Dict, Final, Set

__all__ = [
    "DEFAULT_START_PATH",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "MODULE_DIR",
    "TEMPLATE_FILENAME",
    "FORC_DEFAULTS",
]


DEFAULT_START_PATH: Final[str] = "."


DEFAULT_EXTENSIONS: Final[Set[str]] = {"py"}


DEFAULT_IGNORE: Final[Set[str]] = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "dist",
    "build",
    "out",
    ".DS_Store",
}


PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".forc.toml"
CONFIG_SECTION_NAME: Final[str] = "forc"


MODULE_DIR: Final[Path] = Path(__file__).parent
TEMPLATE_FILENAME: Final[str] = "format_code.toml.template"

FORC_DEFAULTS: Final[Dict[str, Any]] = {
    "extensions": sorted(list(DEFAULT_EXTENSIONS)),
    "ignore": sorted(list(DEFAULT_IGNORE)),
}
