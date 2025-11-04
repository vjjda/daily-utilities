# Path: modules/no_doc/no_doc_config.py
from pathlib import Path
from typing import Any, Dict, Final, Set

__all__ = [
    "DEFAULT_START_PATH",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "DEFAULT_FORMAT_EXTENSIONS",
    "PROJECT_CONFIG_FILENAME",
    "PROJECT_CONFIG_ROOT_KEY",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "MODULE_DIR",
    "TEMPLATE_FILENAME",
    "NDOC_DEFAULTS",
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
    ".gitignore",
    ".ruff_cache",
}


DEFAULT_FORMAT_EXTENSIONS: Final[Set[str]] = {"py"}

PROJECT_CONFIG_FILENAME: Final[str] = "pyproject.toml"
PROJECT_CONFIG_ROOT_KEY: Final[str] = "tool"
CONFIG_FILENAME: Final[str] = ".ndoc.toml"
CONFIG_SECTION_NAME: Final[str] = "ndoc"


MODULE_DIR: Final[Path] = Path(__file__).parent
TEMPLATE_FILENAME: Final[str] = "no_doc.toml.template"

NDOC_DEFAULTS: Final[Dict[str, Any]] = {
    "extensions": sorted(list(DEFAULT_EXTENSIONS)),
    "ignore": sorted(list(DEFAULT_IGNORE)),
    "format_extensions": sorted(list(DEFAULT_FORMAT_EXTENSIONS)),
}
