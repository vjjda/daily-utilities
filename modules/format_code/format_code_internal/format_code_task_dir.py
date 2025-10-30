# Path: modules/format_code/format_code_internal/format_code_task_dir.py
"""
(Internal Task)
Handles the logic for processing a user-specified directory.
"""

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

# Import internal workers/helpers
from . import (
    load_config_files,
    merge_format_code_configs,
    scan_files,
    analyze_file_content_for_formatting
)

# Import hàm báo cáo từ executor (public)
from ..format_code_executor import print_dry_run_report_for_group

# SỬA: Tên hàm
__all__ = ["process_format_code_task_dir"]

FileResult = Dict[str, Any] # Type alias

# SỬA: Tên hàm
def process_format_code_task_dir(
    scan_dir: Path,
    cli_args: argparse.Namespace,
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
    script_file_path: Path
) -> List[FileResult]:
    """
    Xử lý logic format_code cho một thư mục đầu vào.
    """
    logger.info(f"--- 📁 Quét thư mục: {scan_dir.name} ---")
    
    # 1. Tải/Merge Config (cục bộ)
    file_config_data = load_config_files(scan_dir, logger)
    cli_extensions: Optional[str] = getattr(cli_args, 'extensions', None)
    cli_ignore: Optional[str] = getattr(cli_args, 'ignore', None)
    
    # SỬA: Tên hàm
    merged_config = merge_format_code_configs(
        logger=logger,
        cli_extensions=cli_extensions,
        cli_ignore=cli_ignore,
        file_config_data=file_config_data
    )
    final_extensions_list = merged_config["final_extensions_list"]
    final_ignore_list = merged_config["final_ignore_list"]

    # 2. Quét file
    files_in_dir, scan_status = scan_files(
         logger=logger,
         start_path=scan_dir, 
         ignore_list=final_ignore_list,
         extensions=final_extensions_list,
         scan_root=scan_dir, 
         script_file_path=script_file_path
    )
    
    # 3. In báo cáo cấu hình
    logger.info(f"  [Cấu hình áp dụng]")
    logger.info(f"    - Extensions: {sorted(list(final_extensions_list))}")
    logger.info(f"    - Ignore (từ config/CLI): {final_ignore_list}")
    logger.info(f"    - Tải .gitignore cục bộ: {'Có' if scan_status['gitignore_found'] else 'Không'}")
    logger.info(f"    - Tải .gitmodules cục bộ: {'Có' if scan_status['gitmodules_found'] else 'Không'}")

    if not files_in_dir:
        logger.info(f"  -> 🤷 Không tìm thấy file nào khớp tiêu chí trong: {scan_dir.name}")
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("")
        return []

    logger.info(f"  -> ⚡ Tìm thấy {len(files_in_dir)} file, đang phân tích...")

    # 4. Phân tích file
    dir_results: List[FileResult] = []
    
    for file_path in files_in_dir:
        resolved_file = file_path.resolve()
        if resolved_file in processed_files:
            continue 

        # SỬA: Tên hàm
        result = analyze_file_content_for_formatting(file_path, logger)
        if result:
            dir_results.append(result)
        processed_files.add(resolved_file)
        
    # 5. Báo cáo kết quả nhóm
    if dir_results:
        print_dry_run_report_for_group(logger, scan_dir.name, dir_results, reporting_root)
    else:
        # SỬA: Tên thông báo
        logger.info(f"  -> ✅ Tất cả file trong thư mục đã được định dạng.")

    logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
    logger.info("")
    
    return dir_results