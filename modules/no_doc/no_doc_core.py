# Path: modules/no_doc/no_doc_core.py

import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set
import sys

if not "PROJECT_ROOT" in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from .no_doc_internal import (
    merge_ndoc_configs,
    process_no_doc_task_file,
    process_no_doc_task_dir,
)

__all__ = ["process_no_doc_logic"]

FileResult = Dict[str, Any]


def process_no_doc_logic(
    logger: logging.Logger,
    files_to_process: List[Path],
    dirs_to_scan: List[Path],
    cli_args: argparse.Namespace,
    script_file_path: Path,
) -> List[FileResult]:

    all_results: List[FileResult] = []
    processed_files: Set[Path] = set()
    reporting_root = Path.cwd()

    all_clean: bool = getattr(cli_args, "all_clean", False)
    if all_clean:
        logger.info(
            "⚠️ Chế độ ALL-CLEAN đã bật: Sẽ loại bỏ cả Docstring VÀ Comments (nếu cleaner hỗ trợ)."
        )

    format_flag: bool = getattr(cli_args, "format", False)
    if format_flag:
        logger.info(
            "⚡ Chế độ FORMAT (-f) đã bật: Code sẽ được định dạng sau khi làm sạch."
        )

    cli_extensions_str: Optional[str] = getattr(cli_args, "extensions", None)
    default_file_config = merge_ndoc_configs(
        logger=logger,
        cli_extensions=cli_extensions_str,
        cli_ignore=None,
        file_config_data={},
    )
    file_extensions = set(default_file_config["final_extensions_list"])
    file_extensions_with_dot = {
        f".{ext}" if not ext.startswith(".") else ext for ext in file_extensions
    }

    file_format_extensions_set = default_file_config["final_format_extensions_set"]

    if files_to_process:
        logger.info(f"Đang xử lý {len(files_to_process)} file riêng lẻ...")
        logger.info(f"  [Cấu hình áp dụng cho file lẻ]")
        logger.info(f"    - Extensions: {sorted(list(file_extensions))}")
        logger.info(
            f"    - Format Extensions: {sorted(list(file_format_extensions_set))}"
        )
        logger.info(f"    - (Bỏ qua .gitignore và config file)")

        for file_path in files_to_process:
            results = process_no_doc_task_file(
                file_path=file_path,
                cli_args=cli_args,
                file_extensions=file_extensions_with_dot,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
                format_flag=format_flag,
                format_extensions_set=file_format_extensions_set,
            )
            all_results.extend(results)

    if dirs_to_scan:
        logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")
        for scan_dir in dirs_to_scan:
            results = process_no_doc_task_dir(
                scan_dir=scan_dir,
                cli_args=cli_args,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
                script_file_path=script_file_path,
                format_flag=format_flag,
            )
            all_results.extend(results)

    if not all_results and (files_to_process or dirs_to_scan):
        logger.info("Quét hoàn tất. Không tìm thấy file nào cần thay đổi.")

    return all_results