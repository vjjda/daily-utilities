# Path: modules/bootstrap/bootstrap_config.py

"""
Configuration constants for the Bootstrap module.
"""

from pathlib import Path
from typing import Dict, Set

__all__ = [
    "TEMPLATE_DIR", "TYPE_HINT_MAP", "TYPING_IMPORTS",
    "CONFIG_SECTION_NAME", "DEFAULT_BIN_DIR_NAME", "DEFAULT_SCRIPTS_DIR_NAME",
    "DEFAULT_MODULES_DIR_NAME", "DEFAULT_DOCS_DIR_NAME"
]

# --- MODIFIED: Cập nhật đường dẫn TEMPLATE_DIR ---
# (Path(__file__).parent trỏ đến modules/bootstrap)
TEMPLATE_DIR = Path(__file__).parent / "bootstrap_templates"
# --- END MODIFIED ---

# Ánh xạ type TOML sang Python type hint
TYPE_HINT_MAP: Dict[str, str] = {
    "int": "int", 
    "str": "str", 
    "bool": "bool", 
    "Path": "Path"
}

# Các type cần import từ 'typing'
TYPING_IMPORTS: Set[str] = {"Optional", "List"}

# --- Cấu hình cho bootstrap_tool.py ---
CONFIG_SECTION_NAME = "bootstrap"
DEFAULT_BIN_DIR_NAME = "bin"
DEFAULT_SCRIPTS_DIR_NAME = "scripts"
DEFAULT_MODULES_DIR_NAME = "modules"
DEFAULT_DOCS_DIR_NAME = "docs"