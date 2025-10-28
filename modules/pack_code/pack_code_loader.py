# Path: modules/pack_code/pack_code_loader.py

"""
File Loading logic for pack_code.
(Responsible for all read I/O)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- MODIFIED: Cập nhật __all__ ---
__all__ = ["load_files_content"]
# --- END MODIFIED ---

# --- MODIFIED: Thay đổi hàm 'load_data' ---
def load_files_content(
    logger: logging.Logger, 
    file_paths: List[Path],
    base_dir: Path
) -> Dict[Path, str]:
    """
    Tải nội dung của tất cả các file được yêu cầu.
    Bỏ qua các file không thể đọc (ví dụ: binary, encoding lỗi).
    """
    logger.info(f"Đang đọc nội dung từ {len(file_paths)} file...")
    content_map: Dict[Path, str] = {}
    
    skipped_count = 0
    for file_path in file_paths:
        try:
            # Đọc nội dung file
            content = file_path.read_text(encoding='utf-8')
            content_map[file_path] = content
        except UnicodeDecodeError:
            logger.warning(f"   -> Bỏ qua (lỗi encoding): {file_path.relative_to(base_dir).as_posix()}")
            skipped_count += 1
        except IOError as e:
            logger.warning(f"   -> Bỏ qua (lỗi I/O: {e}): {file_path.relative_to(base_dir).as_posix()}")
            skipped_count += 1
        except Exception as e:
            logger.warning(f"   -> Bỏ qua (lỗi: {e}): {file_path.relative_to(base_dir).as_posix()}")
            skipped_count += 1
            
    if skipped_count > 0:
        logger.warning(f"Đã bỏ qua tổng cộng {skipped_count} file không thể đọc.")
        
    return content_map
# --- END MODIFIED ---