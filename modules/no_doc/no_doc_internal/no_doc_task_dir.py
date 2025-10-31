# Path: modules/no_doc/no_doc_internal/no_doc_task_dir.py
"""
(Internal Task)
Handles the logic for processing a user-specified directory.
"""

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from . import (
    load_config_files,
    merge_ndoc_configs,
    scan_files,
    # SỬA: Đổi tên analyzer
    analyze_file_for_cleaning_and_formatting,
)

from ..no_doc_executor import print_dry_run_report_for_group

__all__ = ["process_no_doc_task_dir"]

FileResult = Dict[str, Any]

def process_no_doc_task_dir(
    scan_dir: Path,
    cli_args: argparse.Namespace,
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
    script_file_path: Path,
    # SỬA: Thêm tham số format
    format_flag: bool
) -> List[FileResult]:
    logger.info(f"--- 📁 Quét thư mục: {scan_dir.name} ---")

    file_config_data = load_config_files(scan_dir, logger)
    cli_extensions: Optional[str] = getattr(cli_args, "extensions", None)
    cli_ignore: Optional[str] = getattr(cli_args, "ignore", None)

    merged_config = merge_ndoc_configs(
        logger=logger,
        cli_extensions=cli_extensions,
        cli_ignore=cli_ignore,
        file_config_data=file_config_data,
    )
    final_extensions_list = merged_config["final_extensions_list"]
    final_ignore_list = merged_config["final_ignore_list"]
    # SỬA: Lấy set format
    final_format_extensions_set = merged_config["final_format_extensions_set"]

    files_in_dir, scan_status = scan_files(
        logger=logger,
        start_path=scan_dir,
        ignore_list=final_ignore_list,
        extensions=final_extensions_list,
        scan_root=scan_dir,
        script_file_path=script_file_path,
    )

    logger.info(f"  [Cấu hình áp dụng]")
    logger.info(f"    - Extensions: {sorted(list(final_extensions_list))}")
    logger.info(f"    - Ignore (từ config/CLI): {final_ignore_list}")
    # SỬA: Thêm log
    logger.info(f"    - Format Extensions (-f): {sorted(list(final_format_extensions_set))}")
    logger.info(
        f"    - Tải .gitignore cục bộ: {'Có' if scan_status['gitignore_found'] else 'Không'}"
    )
    logger.info(
        f"    - Tải .gitmodules cục bộ: {'Có' if scan_status['gitmodules_found'] else 'Không'}"
    )

    if not files_in_dir:
        logger.info(
            f"  -> 🤷 Không tìm thấy file nào khớp tiêu chí trong: {scan_dir.name}"
        )
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("")
        return []

    logger.info(f"  -> ⚡ Tìm thấy {len(files_in_dir)} file, đang phân tích...")

    dir_results: List[FileResult] = []
    all_clean: bool = getattr(cli_args, "all_clean", False)

    for file_path in files_in_dir:
        resolved_file = file_path.resolve()
        if resolved_file in processed_files:
            continue

        # SỬA: Gọi analyzer mới
        result = analyze_file_for_cleaning_and_formatting(
            file_path=file_path, 
            logger=logger, 
            all_clean=all_clean,
            format_flag=format_flag,
            format_extensions_set=final_format_extensions_set
        )
        if result:
            dir_results.append(result)
        processed_files.add(resolved_file)

    if dir_results:
        print_dry_run_report_for_group(
            logger, scan_dir.name, dir_results, reporting_root
        )
    else:
        logger.info(f"  -> ✅ Tất cả file trong thư mục đã sạch / đã định dạng.") # SỬA

    logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
    logger.info("")

    return dir_results