# Path: modules/pack_code/pack_code_internal/pack_code_loader.py
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from utils.core import load_and_merge_configs, clean_code, format_code
    from utils.constants import DEFAULT_EXTENSIONS_LANG_MAP
except ImportError:
    print("Lỗi: Không thể import utils.core hoặc utils.constants.", file=sys.stderr)
    sys.exit(1)

from ..pack_code_config import (
    PROJECT_CONFIG_FILENAME,
    CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
)

__all__ = ["load_files_content", "load_config_files"]


def load_config_files(start_dir: Path, logger: logging.Logger) -> Dict[str, Any]:
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
    format_flag: bool,
    format_extensions_set: Set[str],
) -> Dict[Path, str]:
    logger.info(f"Đang đọc nội dung từ {len(file_paths)} file (song song)...")
    content_map: Dict[Path, str] = {}
    skipped_count = 0
    cleaned_count = 0
    formatted_count = 0

    def _process_single_file(file_path: Path) -> Tuple[Path, Optional[str], str, str]:

        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            file_was_cleaned = False
            file_was_formatted = False

            file_ext = "".join(file_path.suffixes).lstrip(".")
            language_id = DEFAULT_EXTENSIONS_LANG_MAP.get(file_ext)

            if all_clean and file_ext in clean_extensions_set:
                if language_id:
                    logger.debug(
                        f"   -> Đang làm sạch '{file_path.relative_to(base_dir).as_posix()}' (ngôn ngữ: {language_id})..."
                    )
                    cleaned_content = clean_code(
                        code_content=content,
                        language=language_id,
                        logger=logger,
                        all_clean=True,
                    )
                    if cleaned_content != content:
                        file_was_cleaned = True
                        content = cleaned_content
                else:
                    logger.debug(
                        f"   -> Bỏ qua làm sạch '{file_path.relative_to(base_dir).as_posix()}': Không tìm thấy language ID cho extension '{file_ext}'."
                    )

            if format_flag and file_ext in format_extensions_set:
                if language_id:
                    logger.debug(
                        f"   -> Đang định dạng '{file_path.relative_to(base_dir).as_posix()}' (ngôn ngữ: {language_id})..."
                    )

                    formatted_content = format_code(
                        code_content=content,
                        language=language_id,
                        logger=logger,
                        file_path=file_path,
                    )
                    if formatted_content != content:

                        if not (all_clean and content == original_content):
                            file_was_formatted = True
                        content = formatted_content
                else:
                    logger.debug(
                        f"   -> Bỏ qua định dạng '{file_path.relative_to(base_dir).as_posix()}': Không tìm thấy language ID cho extension '{file_ext}'."
                    )

            status = "ok"
            if file_was_cleaned:
                status = "cleaned"
            if file_was_formatted:
                status = "formatted"

            return file_path, content, status, ""

        except UnicodeDecodeError:
            return (
                file_path,
                None,
                "skipped",
                f"   -> Bỏ qua (lỗi encoding): {file_path.relative_to(base_dir).as_posix()}",
            )
        except IOError as e:
            return (
                file_path,
                None,
                "skipped",
                f"   -> Bỏ qua (lỗi I/O: {e}): {file_path.relative_to(base_dir).as_posix()}",
            )
        except Exception as e:
            return (
                file_path,
                None,
                "skipped",
                f"    -> Bỏ qua (lỗi không xác định: {e}): {file_path.relative_to(base_dir).as_posix()}",
            )

    max_workers = os.cpu_count() or 4
    logger.debug(f"Sử dụng ThreadPoolExecutor với max_workers={max_workers}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_process_single_file, file_path) for file_path in file_paths
        ]

        for future in as_completed(futures):
            f_path, f_content, f_status, log_msg = future.result()

            if f_status == "skipped":
                logger.warning(log_msg)
                skipped_count += 1
            elif f_status == "cleaned":
                cleaned_count += 1
                content_map[f_path] = f_content
            elif f_status == "formatted":
                formatted_count += 1
                content_map[f_path] = f_content
            elif f_status == "ok":
                content_map[f_path] = f_content

    if skipped_count > 0:
        logger.warning(f"Đã bỏ qua tổng cộng {skipped_count} file không thể đọc.")
    if all_clean and cleaned_count > 0:
        logger.info(f"Đã làm sạch nội dung của {cleaned_count} file.")
    if format_flag and formatted_count > 0:
        logger.info(f"Đã định dạng nội dung của {formatted_count} file.")

    return content_map
