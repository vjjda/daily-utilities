# Path: modules/pack_code/pack_code_internal/pack_code_loader.py
"""
Logic tải file cho pack_code.
(Internal module, imported by pack_code_core)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

try:
    # SỬA: Import 'format_code'
    from utils.core import load_and_merge_configs, clean_code, format_code
    from utils.constants import DEFAULT_EXTENSIONS_LANG_MAP
except ImportError:
    print("Lỗi: Không thể import utils.core hoặc utils.constants.", file=sys.stderr)
    sys.exit(1)

from ..pack_code_config import (
    PROJECT_CONFIG_FILENAME,
    CONFIG_FILENAME,
    CONFIG_SECTION_NAME
)

__all__ = ["load_files_content", "load_config_files"]


def load_config_files(
    start_dir: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải và hợp nhất cấu hình từ .project.toml và .pcode.toml.
    ...
    """
    return load_and_merge_configs(
        start_dir=start_dir,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
    )


def load_files_content(
    logger: logging.Logger,
    file_paths: List[Path],
    base_dir: Path,
    all_clean: bool,
    clean_extensions_set: Set[str],
    # SỬA: Thêm tham số cho logic format
    format_flag: bool,
    format_extensions_set: Set[str]
) -> Dict[Path, str]:
    """
    Tải nội dung text, tùy chọn LÀM SẠCH, sau đó tùy chọn ĐỊNH DẠNG.
    """
    logger.info(f"Đang đọc nội dung từ {len(file_paths)} file...")
    content_map: Dict[Path, str] = {}
    skipped_count = 0
    cleaned_count = 0
    formatted_count = 0 # SỬA: Thêm bộ đếm

    for file_path in file_paths:
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content # Giữ bản gốc để so sánh

            # Xác định ngôn ngữ
            file_ext = "".join(file_path.suffixes).lstrip('.')
            language_id = DEFAULT_EXTENSIONS_LANG_MAP.get(file_ext)

            # --- BƯỚC 1: LÀM SẠCH (Clean) ---
            if all_clean and file_ext in clean_extensions_set:
                if language_id:
                    logger.debug(f"   -> Đang làm sạch '{file_path.relative_to(base_dir).as_posix()}' (ngôn ngữ: {language_id})...")
                    cleaned_content = clean_code(
                        code_content=content,
                        language=language_id,
                        logger=logger,
                        all_clean=True 
                    )
                    if cleaned_content != content:
                        cleaned_count += 1
                        content = cleaned_content # Cập nhật nội dung để format
                else:
                    logger.debug(f"   -> Bỏ qua làm sạch '{file_path.relative_to(base_dir).as_posix()}': Không tìm thấy language ID cho extension '{file_ext}'.")

            # --- BƯỚC 2: ĐỊNH DẠNG (Format) ---
            # (Thực thi *sau* khi clean, theo yêu cầu)
            if format_flag and file_ext in format_extensions_set:
                if language_id:
                    logger.debug(f"   -> Đang định dạng '{file_path.relative_to(base_dir).as_posix()}' (ngôn ngữ: {language_id})...")
                    # Truyền file_path để Black tìm pyproject.toml
                    formatted_content = format_code(
                        code_content=content,
                        language=language_id,
                        logger=logger,
                        file_path=file_path 
                    )
                    if formatted_content != content:
                        # Chỉ đếm nếu format thay đổi nội dung (sau khi clean)
                        if not (all_clean and content == original_content):
                             formatted_count += 1
                        content = formatted_content
                else:
                    logger.debug(f"   -> Bỏ qua định dạng '{file_path.relative_to(base_dir).as_posix()}': Không tìm thấy language ID cho extension '{file_ext}'.")
            
            # --- KẾT THÚC ---
            content_map[file_path] = content
            
        except UnicodeDecodeError:
            logger.warning(f"   -> Bỏ qua (lỗi encoding): {file_path.relative_to(base_dir).as_posix()}")
            skipped_count += 1
        except IOError as e:
            logger.warning(f"   -> Bỏ qua (lỗi I/O: {e}): {file_path.relative_to(base_dir).as_posix()}")
            skipped_count += 1
        except Exception as e:
            logger.warning(f"    -> Bỏ qua (lỗi không xác định: {e}): {file_path.relative_to(base_dir).as_posix()}")
            skipped_count += 1

    if skipped_count > 0:
        logger.warning(f"Đã bỏ qua tổng cộng {skipped_count} file không thể đọc.")
    if all_clean and cleaned_count > 0:
        logger.info(f"Đã làm sạch nội dung của {cleaned_count} file.")
    # SỬA: Thêm log format
    if format_flag and formatted_count > 0:
        logger.info(f"Đã định dạng nội dung của {formatted_count} file.")

    return content_map