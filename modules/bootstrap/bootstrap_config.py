# Path: modules/bootstrap/bootstrap_config.py

from pathlib import Path
from typing import Dict, Set, Final

__all__ = [
    "TEMPLATE_DIR",
    "TYPE_HINT_MAP",
    "TYPING_IMPORTS",
    "CONFIG_SECTION_NAME",
    "DEFAULT_BIN_DIR_NAME",
    "DEFAULT_SCRIPTS_DIR_NAME",
    "DEFAULT_MODULES_DIR_NAME",
    "DEFAULT_DOCS_DIR_NAME",
]


TEMPLATE_DIR: Final[Path] = Path(__file__).parent / "bootstrap_templates"


TYPE_HINT_MAP: Final[Dict[str, str]] = {
    "int": "int",
    "str": "str",
    "bool": "bool",
    "Path": "Path",
}


TYPING_IMPORTS: Final[Set[str]] = {"Optional", "List"}


CONFIG_SECTION_NAME: Final[str] = "bootstrap"


DEFAULT_BIN_DIR_NAME: Final[str] = "bin"
DEFAULT_SCRIPTS_DIR_NAME: Final[str] = "scripts"
DEFAULT_MODULES_DIR_NAME: Final[str] = "modules"
DEFAULT_DOCS_DIR_NAME: Final[str] = "docs"