# Path: modules/format_code/format_code_core.py
"""
Core Orchestration logic for the format_code (Format Code) module.
"""

import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set
import sys

# Thiết lập sys.path
if not 'PROJECT_ROOT' in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# SỬA: Import từ internal
from .format_code_internal import (
    merge_format_code_configs,
    process_format_code_task_file,
    process_format_code_task_dir
)

# SỬA: Tên hàm
__all__ = ["process_format_code_logic"]

FileResult = Dict[str, Any] # Type alias

# SỬA: Tên hàm
def process_format_code_logic(
    logger: logging.Logger,
    files_to_process: List[Path],
    dirs_to_scan: List[Path],
    cli_args: argparse.Namespace,
    script_file_path: Path
) -> List[FileResult]:
    """
    Điều phối toàn bộ quá trình định dạng code (Orchestrator).
    """
    
    all_results: List[FileResult] = []
    processed_files: Set[Path] = set()
    reporting_root = Path.cwd()

    # 1. Hợp nhất config MỘT LẦN cho các file lẻ
    cli_extensions_str: Optional[str] = getattr(cli_args, 'extensions', None)
    # SỬA: Tên hàm
    default_file_config = merge_format_code_configs(
        logger=logger,
        cli_extensions=cli_extensions_str,
        cli_ignore=None, 
        file_config_data={} 
    )
    file_extensions = set(default_file_config["final_extensions_list"])

    # 2. XỬ LÝ CÁC FILE RIÊNG LẺ
    if files_to_process:
        logger.info(f"Đang xử lý {len(files_to_process)} file riêng lẻ...")
        logger.info(f"  [Cấu hình áp dụng cho file lẻ]")
        logger.info(f"    - Extensions: {sorted(list(file_extensions))}")
        logger.info(f"    - (Bỏ qua .gitignore và config file)")
        
        for file_path in files_to_process:
            # SỬA: Tên hàm
            results = process_format_code_task_file(
                file_path=file_path,
                cli_args=cli_args,
                file_extensions=file_extensions,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root
            )
            all_results.extend(results)

    # 3. XỬ LÝ CÁC THƯ MỤC
    if dirs_to_scan:
        logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")
        for scan_dir in dirs_to_scan:
            # SỬA: Tên hàm
            results = process_format_code_task_dir(
                scan_dir=scan_dir,
                cli_args=cli_args,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
                script_file_path=script_file_path
            )
            all_results.extend(results)

    if not all_results and (files_to_process or dirs_to_scan):
        logger.info("Quét hoàn tất. Không tìm thấy file nào cần định dạng.")
        
    return all_results