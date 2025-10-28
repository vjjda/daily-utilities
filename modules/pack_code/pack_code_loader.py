# Path: modules/pack_code/pack_code_loader.py

"""
File Loading logic for pack_code.
(Responsible for all read I/O)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# --- MODIFIED: Import thêm ---
import sys
try:
    from utils.core import load_and_merge_configs
except ImportError:
    print("Lỗi: Không thể import utils.core.", file=sys.stderr)
    sys.exit(1)

from .pack_code_config import (
    PROJECT_CONFIG_FILENAME,
    CONFIG_FILENAME,
    CONFIG_SECTION_NAME
)
# --- END MODIFIED ---


# --- MODIFIED: Cập nhật __all__ ---
__all__ = ["load_files_content", "load_config_files"] # <-- MODIFIED
# --- END MODIFIED ---

# --- NEW: Hàm load_config_files (Copy từ tree/cpath) ---
def load_config_files(
    start_dir: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải file .project.toml VÀ .pcode.toml,
    trích xuất và merge section [pcode].
    """
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME
    )
# --- END NEW ---


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