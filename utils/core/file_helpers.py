# Path: utils/core/file_helpers.py
import logging
from pathlib import Path
from typing import Dict, Any

__all__ = ["load_text_template"]


def load_text_template(template_path: Path, logger: logging.Logger) -> str:
    try:
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(
            f"❌ LỖI NGHIÊM TRỌNG: Không tìm thấy file template tại: {template_path.as_posix()}"
        )
        raise
    except Exception as e:
        logger.error(
            f"❌ LỖI NGHIÊM TRỌNG: Không thể đọc file template '{template_path.name}': {e}"
        )
        raise
