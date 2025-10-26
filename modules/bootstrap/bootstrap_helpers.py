# Path: modules/bootstrap/bootstrap_helpers.py
"""
Helper utilities for the Bootstrap module.
(Loading templates, parsing config)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from .bootstrap_config import TEMPLATE_DIR

# --- MODIFIED: Cập nhật __all__ ---
__all__ = [
    "load_template", "get_cli_args",
]
# --- END MODIFIED ---


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

def get_cli_args(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Helper: Lấy danh sách [[cli.args]] từ config."""
    return config.get('cli', {}).get('args', [])

# --- REMOVED: build_path_expands (Đã chuyển sang bootstrap_argparse_builder.py) ---
# --- REMOVED: build_args_pass_to_core (Đã chuyển sang bootstrap_argparse_builder.py) ---