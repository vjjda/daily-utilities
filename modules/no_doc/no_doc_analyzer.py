# Path: modules/no_doc/no_doc_analyzer.py
"""
Logic Phân tích File cho ndoc, sử dụng tiện ích làm sạch code từ utils.core.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import tiện ích làm sạch code
from utils.core import clean_python_code

__all__ = ["analyze_file_for_docstrings"]

# --- Hàm Phân tích Chính ---
def analyze_file_for_docstrings(
    file_path: Path,
    logger: logging.Logger,
    all_clean: bool
) -> Optional[Dict[str, Any]]:
    """
    Phân tích file Python, đọc nội dung, gọi tiện ích làm sạch,
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

    # Gọi hàm tiện ích để làm sạch code
    # Hàm này sẽ tự xử lý lỗi LibCST và trả về nội dung gốc nếu cần
    new_content = clean_python_code(
        code_content=original_content,
        logger=logger, # Truyền logger để hàm tiện ích có thể báo lỗi
        all_clean=all_clean
    )

    # Chỉ trả về kết quả nếu nội dung thực sự thay đổi
    if new_content != original_content:
        return {
            "path": file_path,
            "original_content": original_content, # Giữ lại nội dung gốc để so sánh (tùy chọn)
            "new_content": new_content,
        }

    # Trả về None nếu không có thay đổi hoặc có lỗi xảy ra trong clean_python_code
    return None