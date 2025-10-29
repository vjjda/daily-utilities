# Path: modules/no_doc/no_doc_analyzer.py
"""
Logic Phân tích File cho ndoc, sử dụng tiện ích làm sạch code từ utils.core.
"""

import logging
from pathlib import Path
# THÊM Dict
from typing import Optional, Dict, Any

# Import tiện ích làm sạch code (không đổi)
from utils.core import clean_code
# THÊM: Import config map để tra cứu ngôn ngữ
from .no_doc_config import DEFAULT_EXTENSIONS_MAP

# ĐỔI TÊN hàm và __all__
__all__ = ["analyze_file_content"]

# --- Hàm Phân tích Chính ---
# ĐỔI TÊN hàm
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

    # THÊM: Xác định ngôn ngữ từ đuôi file
    file_ext = "".join(file_path.suffixes).lstrip('.') # Xử lý đuôi kép
    language_id = DEFAULT_EXTENSIONS_MAP.get(file_ext)

    if not language_id:
        # Nếu không tìm thấy ngôn ngữ cho đuôi file này trong config map
        logger.debug(f"Bỏ qua file '{file_path.name}' vì không có cleaner nào được cấu hình cho đuôi file '.{file_ext}'.")
        return None # Không xử lý file này

    # Gọi hàm tiện ích để làm sạch code (không đổi, chỉ thay đổi tên biến)
    new_content = clean_code(
        code_content=original_content,
        language=language_id, # <-- Truyền ngôn ngữ đã tìm được
        logger=logger,
        all_clean=all_clean
    )

    # Chỉ trả về kết quả nếu nội dung thực sự thay đổi (không đổi)
    if new_content != original_content:
        return {
            "path": file_path,
            "original_content": original_content,
            "new_content": new_content,
        }

    # Trả về None nếu không có thay đổi hoặc có lỗi (không đổi)
    return None