# Path: modules/zsh_wrapper/zsh_wrapper_config.py
from pathlib import Path
from typing import Any, Dict, Final

__all__ = [
    "DEFAULT_MODE",
    "DEFAULT_VENV",
    "DEFAULT_WRAPPER_RELATIVE_DIR",
    "DEFAULT_WRAPPER_ABSOLUTE_PATH",
    "CONFIG_FILENAME",
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "TEMPLATE_FILENAME",
    "ZRAP_DEFAULTS",
    "MODULE_DIR",
]


DEFAULT_MODE: Final[str] = "relative"
DEFAULT_VENV: Final[str] = ".venv"


DEFAULT_WRAPPER_RELATIVE_DIR: Final[str] = "bin"
DEFAULT_WRAPPER_ABSOLUTE_PATH: Final[Path] = Path.home() / "bin"


CONFIG_FILENAME: Final[str] = ".zrap.toml"
PROJECT_CONFIG_FILENAME: Final[str] = ".project.toml"
CONFIG_SECTION_NAME: Final[str] = "zrap"
TEMPLATE_FILENAME: Final[str] = "zsh_wrapper.toml.template"

ZRAP_DEFAULTS: Final[Dict[str, Any]] = {
    "mode": DEFAULT_MODE,
    "venv": DEFAULT_VENV,
    "relative_dir": DEFAULT_WRAPPER_RELATIVE_DIR,
    "absolute_dir": str(DEFAULT_WRAPPER_ABSOLUTE_PATH),
}


MODULE_DIR: Final[Path] = Path(__file__).parent
