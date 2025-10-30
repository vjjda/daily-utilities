# Path: modules/no_doc/no_doc_analyzer.py
"""
Logic Phân tích File cho ndoc, sử dụng tiện ích làm sạch code từ utils.core.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import tiện ích làm sạch code
from utils.core import clean_code
# SỬA: Import bản đồ ngôn ngữ từ utils.constants
from utils.constants import DEFAULT_EXTENSIONS_LANG_MAP # <-- SỬA LẠI IMPORT

__all__ = ["analyze_file_content"]

# --- Hàm Phân tích Chính ---
def analyze_file_content(
    file_path: Path,
    logger: logging.Logger,
    all_clean: bool
) -> Optional[Dict[str, Any]]:
    """
    Phân tích file, đọc nội dung, xác định ngôn ngữ, gọi tiện ích làm sạch,
    và trả về kết quả nếu nội dung thay đổi.
    """
    try:
        original_content = file_path.read_text(encoding='utf-8')
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc/encoding: {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc không xác định: {e}")
        return None

    # Xác định ngôn ngữ từ đuôi file
    file_ext = "".join(file_path.suffixes).lstrip('.')
    # SỬA: Sử dụng đúng tên biến đã import
    language_id = DEFAULT_EXTENSIONS_LANG_MAP.get(file_ext) # <-- SỬA TÊN BIẾN

    if not language_id:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}'. Không tìm thấy ánh xạ ngôn ngữ cho đuôi '.{file_ext}' trong DEFAULT_EXTENSIONS_LANG_MAP.")
        return None

    new_content = clean_code(
        code_content=original_content,
        language=language_id,
        logger=logger,
        all_clean=all_clean
    )

    if new_content != original_content:
        return {
            "path": file_path,
            "original_content": original_content,
            "new_content": new_content,
        }

    return None