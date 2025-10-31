# Path: modules/check_path/__init__.pyi
"""Statically declared API for check_path"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

COMMENT_RULES: Any
COMMENT_RULES_BY_EXT: Any
CONFIG_FILENAME: Any
CONFIG_SECTION_NAME: Any
DEFAULT_EXTENSIONS: Any
DEFAULT_IGNORE: Any
PROJECT_CONFIG_FILENAME: Any
execute_check_path_action: Any
print_dry_run_report_for_group: Any
process_check_path_logic: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "COMMENT_RULES",
    "COMMENT_RULES_BY_EXT",
    "CONFIG_FILENAME",
    "CONFIG_SECTION_NAME",
    "DEFAULT_EXTENSIONS",
    "DEFAULT_IGNORE",
    "PROJECT_CONFIG_FILENAME",
    "execute_check_path_action",
    "print_dry_run_report_for_group",
    "process_check_path_logic",
]