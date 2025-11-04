# Path: modules/pack_code/pack_code_config.py
from pathlib import Path
from typing import Any, Dict, Final, Optional, Set

__all__ = [
    "DEFAULT_START_PATH",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "DEFAULT_INCLUDE",
    "DEFAULT_CLEAN_EXTENSIONS",
    "DEFAULT_FORMAT_EXTENSIONS",
    "DEFAULT_OUTPUT_DIR",
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "MODULE_DIR",
    "TEMPLATE_FILENAME",
    "PCODE_DEFAULTS",
]

DEFAULT_START_PATH: Final[str] = "."
DEFAULT_EXTENSIONS: Final[Set[str]] = {
    "md",
    "py",
    "txt",
    "json",
    "xml",
    "yaml",
    "yml",
    "ini",
    "cfg",
    "cfg.py",
    "sh",
    "bash",
    "zsh",
    "toml",
    "template",
    "gitignore",
    "",
}
DEFAULT_IGNORE: Final[Set[str]] = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    ".DS_Store",
}


DEFAULT_INCLUDE: Final[Optional[Set[str]]] = None
DEFAULT_OUTPUT_DIR: Final[str] = "~/Documents/code.context"

DEFAULT_CLEAN_EXTENSIONS: Final[Set[str]] = {"py", "zsh", "sh"}
DEFAULT_FORMAT_EXTENSIONS: Final[Set[str]] = {"py"}

PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_FILENAME: Final[str] = ".pcode.toml"
CONFIG_SECTION_NAME: Final[str] = "pcode"


MODULE_DIR: Final[Path] = Path(__file__).parent
TEMPLATE_FILENAME: Final[str] = "pack_code.toml.template"

PCODE_DEFAULTS: Final[Dict[str, Any]] = {
    "output_dir": DEFAULT_OUTPUT_DIR,
    "extensions": sorted(list(DEFAULT_EXTENSIONS)),
    "ignore": sorted(list(DEFAULT_IGNORE)),
    "include": sorted(list(DEFAULT_INCLUDE)) if DEFAULT_INCLUDE else [],
    "clean_extensions": sorted(list(DEFAULT_CLEAN_EXTENSIONS)),
    "format_extensions": sorted(list(DEFAULT_FORMAT_EXTENSIONS)),
}
