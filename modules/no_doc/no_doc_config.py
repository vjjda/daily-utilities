# Path: modules/no_doc/no_doc_config.py
from pathlib import Path
from typing import Any, Optional, List, Final, Set

__all__ = [
    "DEFAULT_START_PATH",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "DEFAULT_FORMAT_EXTENSIONS",
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
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
    "/.gitignore",
}


DEFAULT_FORMAT_EXTENSIONS: Final[Set[str]] = {"py"}

PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".ndoc.toml"
CONFIG_SECTION_NAME: Final[str] = "ndoc"
