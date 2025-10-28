# Path: modules/bootstrap/bootstrap_config.py
"""
Các hằng số cấu hình cho module Bootstrap.
"""

from pathlib import Path
from typing import Dict, Set, Final

__all__ = [
    "TEMPLATE_DIR", "TYPE_HINT_MAP", "TYPING_IMPORTS",
    "CONFIG_SECTION_NAME", "DEFAULT_BIN_DIR_NAME", "DEFAULT_SCRIPTS_DIR_NAME",
    "DEFAULT_MODULES_DIR_NAME", "DEFAULT_DOCS_DIR_NAME"
]

# --- Đường dẫn Templates ---
# Đường dẫn đến thư mục chứa các file template (*.template)
TEMPLATE_DIR: Final[Path] = Path(__file__).parent / "bootstrap_templates"

# --- Ánh xạ Type Hint ---
# Ánh xạ từ type trong spec.toml ('str', 'int', 'bool', 'Path')
# sang type hint Python thực tế ('str', 'int', 'bool', 'Path')
TYPE_HINT_MAP: Final[Dict[str, str]] = {
    "int": "int",
    "str": "str",
    "bool": "bool",
    "Path": "Path" # Cần `from pathlib import Path` trong template
}

# Các type cần import từ module 'typing' (ví dụ: Optional)
TYPING_IMPORTS: Final[Set[str]] = {"Optional", "List"}

# --- Cấu hình cho bootstrap_tool.py ---
# Tên section trong file .project.toml chứa cấu hình đường dẫn
CONFIG_SECTION_NAME: Final[str] = "bootstrap"

# Tên thư mục mặc định (nếu không có trong .project.toml)
DEFAULT_BIN_DIR_NAME: Final[str] = "bin"
DEFAULT_SCRIPTS_DIR_NAME: Final[str] = "scripts"
DEFAULT_MODULES_DIR_NAME: Final[str] = "modules"
DEFAULT_DOCS_DIR_NAME: Final[str] = "docs"