# Path: utils/core/file_helpers.py

"""
Các tiện ích I/O file thuần túy (Đọc file văn bản).
(Module nội bộ, được import bởi utils/core)
"""

import logging
from pathlib import Path
from typing import Dict, Any

__all__ = ["load_text_template"]

def load_text_template(template_path: Path, logger: logging.Logger) -> str:
    """
    Đọc nội dung thô của một file template (dạng text).

    Args:
        template_path: Đường dẫn đến file template.
        logger: Logger để ghi log lỗi.

    Returns:
        Nội dung file dưới dạng string.

    Raises:
        FileNotFoundError: Nếu file template không tồn tại.
        Exception: Nếu có lỗi khác khi đọc file.
    """
    try:
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không tìm thấy file template tại: {template_path.as_posix()}") #
        raise # Ném lại lỗi để dừng chương trình
    except Exception as e:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không thể đọc file template '{template_path.name}': {e}") #
        raise # Ném lại lỗi