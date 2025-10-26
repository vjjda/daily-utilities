# Path: modules/bootstrap/bootstrap_loader.py
"""
Helper utilities for the Bootstrap module.
(Loading templates, parsing config)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

from .bootstrap_config import TEMPLATE_DIR, CONFIG_SECTION_NAME
# --- MODIFIED: Import hàm helper chung ---
from utils.core import load_project_config_section, load_text_template
# --- END MODIFIED ---

__all__ = [
    "load_template",
    "load_bootstrap_config",
    "load_spec_file"
]


def load_template(template_name: str) -> str:
    """Helper: Đọc nội dung từ một file template."""
    # --- MODIFIED: Tái sử dụng logic chung ---
    # (Chúng ta dùng getLogger vì logger không được truyền vào đây,
    #  điều này nhất quán với hành vi cũ)
    logger = logging.getLogger("Bootstrap") 
    template_path = TEMPLATE_DIR / template_name
    return load_text_template(template_path, logger)
    # --- END MODIFIED ---

def load_bootstrap_config(
    logger: logging.Logger, 
    project_root: Path
) -> Dict[str, Any]:
    """
    Tải section [bootstrap] từ file .project.toml.
    """
    if tomllib is None:
        logger.error("Lỗi: Cần gói 'toml' (cho Python < 3.11)")
        sys.exit(1)
        
    config_path = project_root / ".project.toml"
    return load_project_config_section(config_path, CONFIG_SECTION_NAME, logger)

def load_spec_file(
    logger: logging.Logger, 
    spec_file_path: Path
) -> Dict[str, Any]:
    """
    Tải và parse file *.spec.toml.
    """
    if tomllib is None:
        logger.error("Lỗi: Cần gói 'toml' (cho Python < 3.11)")
        sys.exit(1)
        
    try:
        with open(spec_file_path, 'rb') as f:
            config = tomllib.load(f)
        return config
    except Exception as e:
        logger.error(f"❌ Lỗi khi đọc file TOML: {e}")
        sys.exit(1)