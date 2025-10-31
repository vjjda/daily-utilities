# Path: modules/check_path/check_path_internal/check_path_task_file.py

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple


from .check_path_merger import merge_check_path_configs
from .check_path_analyzer import analyze_single_file_for_path_comment


from ..check_path_executor import print_dry_run_report_for_group

__all__ = ["process_check_path_task_file"]

FileResult = Dict[str, Any] 

def process_check_path_task_file(
    file_path: Path,
    cli_args: argparse.Namespace,
    file_extensions: Set[str],
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path 
) -> List[FileResult]:
    logger.info(f"--- 📄 Đang xử lý file: {file_path.relative_to(reporting_root).as_posix()} ---")
    
    file_only_results: List[FileResult] = []
    resolved_file = file_path.resolve()
    if resolved_file in processed_files:
        logger.info("   -> Bỏ qua (đã xử lý).")
        logger.info("")
        return []
        
    
    file_ext = "".join(file_path.suffixes) 
    if file_ext not in file_extensions:
        logger.warning(
            f"⚠️ Bỏ qua file '{file_path.name}': không khớp extensions ({file_ext})"
        )
        logger.info("")
        return []

    
    
    result = analyze_single_file_for_path_comment(file_path, reporting_root, logger)
    if result:
        file_only_results.append(result)
    processed_files.add(resolved_file)
    
    
    if file_only_results:
        print_dry_run_report_for_group(logger, file_path.name, file_only_results, reporting_root)
    else:
        logger.info(f"  -> ✅ Path comment đã chính xác.")

    logger.info("") 
    return file_only_results