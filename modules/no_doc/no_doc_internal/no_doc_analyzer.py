# Path: modules/no_doc/no_doc_internal/no_doc_analyzer.py
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Set
import sys


if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))


from utils.core import clean_code, format_code
from utils.constants import DEFAULT_EXTENSIONS_LANG_MAP


__all__ = ["analyze_file_for_cleaning_and_formatting"]

FileResult = Dict[str, Any]


def analyze_file_for_cleaning_and_formatting(
    file_path: Path,
    logger: logging.Logger,
    all_clean: bool,
    format_flag: bool,
    format_extensions_set: Set[str],
) -> Optional[FileResult]:
    try:
        original_content = file_path.read_text(encoding="utf-8")
    except (IOError, UnicodeDecodeError) as e:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc/encoding: {e}")
        return None
    except Exception as e:
        logger.warning(
            f"⚠️ Bỏ qua file '{file_path.name}' do lỗi đọc không xác định: {e}"
        )
        return None

    file_ext = "".join(file_path.suffixes).lstrip(".")
    language_id = DEFAULT_EXTENSIONS_LANG_MAP.get(file_ext)

    if not language_id:
        logger.warning(
            f"⚠️ Bỏ qua file '{file_path.name}'. Không tìm thấy ánh xạ ngôn ngữ cho đuôi '.{file_ext}'."
        )
        return None

    cleaned_content = clean_code(
        code_content=original_content,
        language=language_id,
        logger=logger,
        all_clean=all_clean,
    )

    final_content = cleaned_content

    if format_flag and file_ext in format_extensions_set:
        logger.debug(f"   -> Đang định dạng '{file_path.name}' (sau khi làm sạch)...")

        formatted_content = format_code(
            code_content=cleaned_content,
            language=language_id,
            logger=logger,
            file_path=file_path,
        )
        final_content = formatted_content

    if final_content != original_content:
        return {
            "path": file_path,
            "original_content": original_content,
            "new_content": final_content,
        }

    return None
