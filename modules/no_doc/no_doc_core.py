# Path: modules/no_doc/no_doc_core.py
"""
Core Orchestration logic for the no_doc module.
"""

import logging
import argparse
from pathlib import Path
# SỬA: Import OrderedDict
from typing import List, Optional, Dict, Any, Tuple, Set
from collections import OrderedDict
import sys

# Thiết lập sys.path
if not 'PROJECT_ROOT' in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from .no_doc_loader import load_config_files
from .no_doc_merger import merge_ndoc_configs
from .no_doc_analyzer import analyze_file_content
from .no_doc_scanner import scan_files
from .no_doc_config import DEFAULT_EXTENSIONS
# SỬA: Import hàm in báo cáo từ Executor
from .no_doc_executor import print_dry_run_report_for_group

__all__ = ["process_no_doc_logic"]

FileResult = Dict[str, Any] # Type alias

# SỬA: Thay đổi kiểu trả về của hàm
def process_no_doc_logic(
    logger: logging.Logger,
    files_to_process: List[Path],
    dirs_to_scan: List[Path],
    cli_args: argparse.Namespace,
    script_file_path: Path
) -> List[FileResult]:
    """
    Điều phối toàn bộ quá trình xóa docstring (Orchestrator).
    Xử lý file và thư mục, in báo cáo xen kẽ.
    
    Returns:
        Một danh sách phẳng (flat list) chứa tất cả FileResult
        cần được ghi bởi Executor.
    """
    
    # SỬA: Dùng danh sách phẳng
    all_results: List[FileResult] = []
    processed_files: Set[Path] = set() # Tránh xử lý file trùng lặp

    # Dùng CWD để in đường dẫn tương đối
    reporting_root = Path.cwd()

    all_clean: bool = getattr(cli_args, 'all_clean', False)
    if all_clean:
        logger.info("⚠️ Chế độ ALL-CLEAN đã bật: Sẽ loại bỏ cả Docstring VÀ Comments (nếu cleaner hỗ trợ).")

    # --- 1. XỬ LÝ CÁC FILE RIÊNG LẺ ---
    cli_extensions_str: Optional[str] = getattr(cli_args, 'extensions', None)
    default_file_config = merge_ndoc_configs(
        logger=logger,
        cli_extensions=cli_extensions_str,
        cli_ignore=None, 
        file_config_data={} 
    )
    file_extensions = set(default_file_config["final_extensions_list"])

    if files_to_process:
        # SỬA: Thêm emoji 📄
        logger.info(f"--- 📄 Đang xử lý {len(files_to_process)} file riêng lẻ ---")
        logger.info(f"  [Cấu hình áp dụng]")
        logger.info(f"    - Extensions: {sorted(list(file_extensions))}")
        logger.info(f"    - (Bỏ qua .gitignore và config file)")
        
        file_only_results: List[FileResult] = []
        for file_path in files_to_process:
            resolved_file = file_path.resolve()
            if resolved_file in processed_files:
                continue
                
            file_ext = "".join(file_path.suffixes).lstrip('.')
            if file_ext not in file_extensions:
                logger.warning(f"⚠️ Bỏ qua file '{file_path.name}': không khớp extensions (.{file_ext})")
                continue

            result = analyze_file_content(file_path, logger, all_clean)
            if result:
                file_only_results.append(result)
            processed_files.add(resolved_file)
            
        if file_only_results:
            print_dry_run_report_for_group(logger, "Files Lẻ", file_only_results, reporting_root)
            all_results.extend(file_only_results)
        
        # SỬA: Thêm dòng trống sau khi xử lý xong nhóm file lẻ
        logger.info("") 

    # --- 2. XỬ LÝ CÁC THƯ MỤC ---
    if dirs_to_scan:
        logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")

    for scan_dir in dirs_to_scan:
        # 2a. Tải config
        file_config_data = load_config_files(scan_dir, logger)

        # 2b. Hợp nhất config
        cli_extensions: Optional[str] = getattr(cli_args, 'extensions', None)
        cli_ignore: Optional[str] = getattr(cli_args, 'ignore', None)
        
        merged_config = merge_ndoc_configs(
            logger=logger,
            cli_extensions=cli_extensions,
            cli_ignore=cli_ignore,
            file_config_data=file_config_data
        )
        final_extensions_list = merged_config["final_extensions_list"]
        final_ignore_list = merged_config["final_ignore_list"]

        # 2c. Quét file
        files_in_dir, scan_status = scan_files(
             logger=logger,
             start_path=scan_dir, 
             ignore_list=final_ignore_list,
             extensions=final_extensions_list,
             scan_root=scan_dir, 
             script_file_path=script_file_path
        )
        
        # SỬA: Thêm emoji 📁
        logger.info(f"--- 📁 Quét thư mục: {scan_dir.name} ---")
        logger.info(f"  [Cấu hình áp dụng]")
        logger.info(f"    - Extensions: {sorted(list(final_extensions_list))}")
        logger.info(f"    - Ignore (từ config/CLI): {final_ignore_list}")
        logger.info(f"    - Tải .gitignore cục bộ: {'Có' if scan_status['gitignore_found'] else 'Không'}")
        logger.info(f"    - Tải .gitmodules cục bộ: {'Có' if scan_status['gitmodules_found'] else 'Không'}")

        if not files_in_dir:
            # SỬA: Thêm emoji 🤷
            logger.info(f"  -> 🤷 Không tìm thấy file nào khớp tiêu chí trong: {scan_dir.name}")
            # SỬA: Thêm emoji ✅ và dòng trống
            logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
            logger.info("") # Thêm dòng trống
            continue

        # SỬA: Thêm emoji ⚡
        logger.info(f"  -> ⚡ Tìm thấy {len(files_in_dir)} file, đang phân tích...")

        # 2d. Phân tích file
        dir_results: List[FileResult] = []
        for file_path in files_in_dir:
            resolved_file = file_path.resolve()
            if resolved_file in processed_files:
                continue 

            result = analyze_file_content(file_path, logger, all_clean)
            if result:
                dir_results.append(result)
            processed_files.add(resolved_file)
            
        if dir_results:
            print_dry_run_report_for_group(logger, scan_dir.name, dir_results, reporting_root)
            all_results.extend(dir_results)
            
        # SỬA: Thêm emoji ✅ và dòng trống
        logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
        logger.info("") # Thêm dòng trống

    if not all_results and (files_to_process or dirs_to_scan):
        logger.info("Quét hoàn tất. Không tìm thấy file nào cần thay đổi.")
        
    return all_results