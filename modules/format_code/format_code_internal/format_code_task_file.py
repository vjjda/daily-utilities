# Path: modules/format_code/format_code_internal/format_code_task_file.py
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple


from . import analyze_file_content_for_formatting


from ..format_code_executor import print_dry_run_report_for_group


__all__ = ["process_format_code_task_file"]

FileResult = Dict[str, Any]


def process_format_code_task_file(
    file_path: Path,
    cli_args: argparse.Namespace,
    file_extensions: Set[str],
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
) -> List[FileResult]:
    logger.info(
        f"--- 📄 Đang xử lý file: {file_path.relative_to(reporting_root).as_posix()} ---"
    )

    file_only_results: List[FileResult] = []
    resolved_file = file_path.resolve()
    if resolved_file in processed_files:
        logger.info("   -> Bỏ qua (đã xử lý).")
        logger.info("")
        return []

    file_ext = "".join(file_path.suffixes).lstrip(".")
    if file_ext not in file_extensions:
        logger.warning(
            f"⚠️ Bỏ qua file '{file_path.name}': không khớp extensions (.{file_ext})"
        )
        logger.info("")
        return []

    result = analyze_file_content_for_formatting(file_path, logger)
    if result:
        file_only_results.append(result)
    processed_files.add(resolved_file)

    if file_only_results:
        print_dry_run_report_for_group(
            logger, file_path.name, file_only_results, reporting_root
        )
    else:

        logger.info(f"  -> ✅ File đã được định dạng.")

    logger.info("")
    return file_only_results
