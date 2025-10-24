# Path: scripts/internal/bootstrap/bootstrap_config.py

"""
Configuration constants for the Bootstrap module.
"""

from pathlib import Path
from typing import Dict, Set

__all__ = ["TEMPLATE_DIR", "TYPE_HINT_MAP", "TYPING_IMPORTS"]

# Đường dẫn đến thư mục chứa các file .template
TEMPLATE_DIR = Path(__file__).parent.parent / "bootstrap_templates"

# Ánh xạ type TOML sang Python type hint
TYPE_HINT_MAP: Dict[str, str] = {
    "int": "int", 
    "str": "str", 
    "bool": "bool", 
    "Path": "Path"
}

# Các type cần import từ 'typing'
TYPING_IMPORTS: Set[str] = {"Optional", "List"}