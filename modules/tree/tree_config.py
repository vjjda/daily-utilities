# Path: modules/tree/tree_config.py
from pathlib import Path
from typing import Any, Dict, Final, Optional, Set

__all__ = [
    "DEFAULT_IGNORE",
    "DEFAULT_PRUNE",
    "DEFAULT_DIRS_ONLY_LOGIC",
    "DEFAULT_EXTENSIONS",
    "FALLBACK_SHOW_SUBMODULES",
    "DEFAULT_MAX_LEVEL",
    "FALLBACK_USE_GITIGNORE",
    "CONFIG_FILENAME",
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "MODULE_DIR",
    "TEMPLATE_FILENAME",
    "TREE_DEFAULTS",
]


DEFAULT_IGNORE: Final[Set[str]] = {
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".git",
}
DEFAULT_PRUNE: Final[Set[str]] = {"dist", "build"}
DEFAULT_DIRS_ONLY_LOGIC: Final[Set[str]] = set()


DEFAULT_EXTENSIONS: Final[Optional[Set[str]]] = None

FALLBACK_SHOW_SUBMODULES: Final[bool] = False
DEFAULT_MAX_LEVEL: Final[Optional[int]] = None
FALLBACK_USE_GITIGNORE: Final[bool] = True


CONFIG_FILENAME: Final[str] = ".tree.toml"
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_SECTION_NAME: Final[str] = "tree"


MODULE_DIR: Final[Path] = Path(__file__).parent


TEMPLATE_FILENAME: Final[str] = "tree.toml.template"


TREE_DEFAULTS: Final[Dict[str, Any]] = {
    "level": DEFAULT_MAX_LEVEL,
    "show-submodules": FALLBACK_SHOW_SUBMODULES,
    "use-gitignore": FALLBACK_USE_GITIGNORE,
    "ignore": DEFAULT_IGNORE,
    "prune": DEFAULT_PRUNE,
    "dirs-only": DEFAULT_DIRS_ONLY_LOGIC,
    "extensions": DEFAULT_EXTENSIONS,
}
