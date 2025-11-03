# Path: modules/check_path/__init__.py

from .check_path_config import (
    MODULE_DIR,
    TEMPLATE_FILENAME,
    CPATH_DEFAULTS,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    CONFIG_FILENAME,
)


from .check_path_core import run_check_path


__all__ = [
    "run_check_path",
    "MODULE_DIR",
    "TEMPLATE_FILENAME",
    "CPATH_DEFAULTS",
    "PROJECT_CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "CONFIG_FILENAME",
]
