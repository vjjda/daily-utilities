# Path: utils/core/file_helpers.py

"""
Tiện ích I/O file thuần túy (Đọc/Ghi file văn bản).
(Internal module, imported by utils/core.py)
"""

import logging
from pathlib import Path
from typing import Dict, Any

__all__ = ["load_text_template"]

def load_text_template(template_path: Path, logger: logging.Logger) -> str:
    """
    Đọc nội dung thô của một file template (text file).
    Báo lỗi và ném (raise) exception nếu file không tìm thấy.
    """
    try:
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không tìm thấy file template tại: {template_path.as_posix()}")
        raise
    except Exception as e:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không thể đọc file template '{template_path.name}': {e}")
        raise