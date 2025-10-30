# Path: modules/no_doc/ndoc_internal/ndoc_task_file.py
"""
(Internal Task)
Handles the logic for processing a single, user-specified source file.
"""

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

from . import analyze_file_content

from ..no_doc_executor import print_dry_run_report_for_group 

# SỬA: Đổi tên hàm và __all__
__all__ = ["process_ndoc_task_file"]

FileResult = Dict[str, Any] 

# SỬA: Đổi tên hàm
def process_ndoc_task_file(
    file_path: Path,
    cli_args: argparse.Namespace,
    file_extensions: Set[str],
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
) -> List[FileResult]:
    """
    Xử lý logic ndoc cho một file riêng lẻ.
    """
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

    all_clean: bool = getattr(cli_args, "all_clean", False) 
    result = analyze_file_content(file_path, logger, all_clean) 
    if result: 
        file_only_results.append(result) 
    processed_files.add(resolved_file) 

    if file_only_results: 
        print_dry_run_report_for_group(
            logger, file_path.name, file_only_results, reporting_root
        ) 
    else:
        logger.info(f"  -> 🤷 Không tìm thấy thay đổi nào cần thiết.") 

    logger.info("") 
    return file_only_results 