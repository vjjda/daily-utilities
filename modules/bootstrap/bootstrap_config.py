# Path: modules/bootstrap/bootstrap_config.py
from pathlib import Path
from typing import Any, Dict, Final, Set

__all__ = [
    "TEMPLATE_DIR",
    "TYPE_HINT_MAP",
    "TYPING_IMPORTS",
    "CONFIG_SECTION_NAME",
    "DEFAULT_BIN_DIR_NAME",
    "DEFAULT_SCRIPTS_DIR_NAME",
    "DEFAULT_MODULES_DIR_NAME",
    "DEFAULT_DOCS_DIR_NAME",
    "TEMPLATE_FILENAME",
    "SPEC_TEMPLATE_FILENAME",
    "PROJECT_CONFIG_FILENAME",
    "MODULE_DIR",
    "BOOTSTRAP_DEFAULTS",
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
DEFAULT_SCRIPTS_DIR_NAME: Final[str] = "tools"
DEFAULT_MODULES_DIR_NAME: Final[str] = "modules"
DEFAULT_DOCS_DIR_NAME: Final[str] = "docs"


TEMPLATE_FILENAME: Final[str] = "bootstrap_templates/bootstrap.toml.template"


SPEC_TEMPLATE_FILENAME: Final[str] = (
    "modules/bootstrap/bootstrap_templates/tool_spec.toml.template"
)


PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"


MODULE_DIR: Final[Path] = Path(__file__).parent


BOOTSTRAP_DEFAULTS: Final[Dict[str, Any]] = {
    "bin_dir": DEFAULT_BIN_DIR_NAME,
    "scripts_dir": DEFAULT_SCRIPTS_DIR_NAME,
    "modules_dir": DEFAULT_MODULES_DIR_NAME,
    "docs_dir": DEFAULT_DOCS_DIR_NAME,
}
