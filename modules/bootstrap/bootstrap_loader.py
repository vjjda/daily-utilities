# Path: modules/bootstrap/bootstrap_loader.py
"""
Helper utilities for the Bootstrap module.
(Loading templates, parsing config)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

# --- (tomllib import) ---
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        # Lỗi này sẽ được bắt ở entrypoint, nhưng vẫn an toàn
        tomllib = None

from .bootstrap_config import TEMPLATE_DIR, CONFIG_SECTION_NAME
# (Import load_project_config_section từ utils.core)
from utils.core import load_project_config_section

__all__ = [
    "load_template",
    "load_bootstrap_config",
    "load_spec_file"
]


def load_template(template_name: str) -> str:
    """Helper: Đọc nội dung từ một file template."""
    try:
        template_path = TEMPLATE_DIR / template_name
        return template_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logging.error(f"Lỗi nghiêm trọng: Không tìm thấy template '{template_name}'")
        raise
    except Exception as e:
        logging.error(f"Lỗi khi đọc template '{template_name}': {e}")
        raise

def load_bootstrap_config(
    logger: logging.Logger, 
    project_root: Path
) -> Dict[str, Any]:
    """
    Tải section [bootstrap] từ file .project.toml.
    (Logic chuyển từ bootstrap_tool.py)
    """
    if tomllib is None:
        # --- MODIFIED: Đã xóa 'file=sys.stderr' ---
        logger.error("Lỗi: Cần gói 'toml' (cho Python < 3.11)")
        # --- END MODIFIED ---
        sys.exit(1)
        
    config_path = project_root / ".project.toml"
    return load_project_config_section(config_path, CONFIG_SECTION_NAME, logger)

def load_spec_file(
    logger: logging.Logger, 
    spec_file_path: Path
) -> Dict[str, Any]:
    """
    Tải và parse file *.spec.toml.
    (Logic chuyển từ bootstrap_tool.py)
    """
    if tomllib is None:
        # --- MODIFIED: Đã xóa 'file=sys.stderr' ---
        logger.error("Lỗi: Cần gói 'toml' (cho Python < 3.11)")
        # --- END MODIFIED ---
        sys.exit(1)
        
    try:
        with open(spec_file_path, 'rb') as f:
            config = tomllib.load(f)
        return config
    except Exception as e:
        logger.error(f"❌ Lỗi khi đọc file TOML: {e}")
        sys.exit(1)

# --- REMOVED: get_cli_args (Đã chuyển sang bootstrap_utils.py) ---