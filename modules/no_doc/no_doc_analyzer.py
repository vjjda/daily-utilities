# Path: modules/no_doc/no_doc_analyzer.py
"""
Logic Phân tích File cho ndoc, sử dụng tiện ích làm sạch code từ utils.core.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import tiện ích làm sạch code
from utils.core import clean_code
# SỬA: Import EXTENSIONS_LANG_MAP mới
from .no_doc_config import EXTENSIONS_LANG_MAP

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
    # SỬA: Sử dụng EXTENSIONS_LANG_MAP để tra cứu
    language_id = EXTENSIONS_LANG_MAP.get(file_ext)

    if not language_id:
        # Lỗi này không nên xảy ra nếu logic filter hoạt động đúng,
        # nhưng vẫn kiểm tra để đảm bảo an toàn.
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}'. Không tìm thấy ánh xạ ngôn ngữ cho đuôi '.{file_ext}' trong EXTENSIONS_LANG_MAP.")
        return None

    # Gọi hàm tiện ích để làm sạch code
    new_content = clean_code(
        code_content=original_content,
        language=language_id, # Truyền ngôn ngữ đã tìm được
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