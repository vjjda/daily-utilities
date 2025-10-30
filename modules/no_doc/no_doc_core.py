# Path: modules/no_doc/no_doc_core.py
"""
Core Orchestration logic for the no_doc module.
"""

import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set
from collections import OrderedDict
import sys

# Thiết lập sys.path
if not 'PROJECT_ROOT' in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# SỬA: Import từ facade nội bộ '.ndoc_internal'
from .ndoc_internal import (
    load_config_files,
    merge_ndoc_configs,
    analyze_file_content,
    scan_files
)

from .no_doc_config import DEFAULT_EXTENSIONS
from .no_doc_executor import print_dry_run_report_for_group

__all__ = ["process_no_doc_logic"]

FileResult = Dict[str, Any] # Type alias

# ... (Toàn bộ phần còn lại của file _process_ndoc_task_file,
# _process_ndoc_task_dir, và process_no_doc_logic không thay đổi) ...

# --- 1. HÀM HELPER XỬ LÝ FILE LẺ ---

def _process_ndoc_task_file(
    file_path: Path,
    cli_args: argparse.Namespace,
    file_extensions: Set[str], # Set extensions đã merge
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path
) -> List[FileResult]:
    """
    (HELPER 1)
    Xử lý logic ndoc cho một file riêng lẻ.
    """
    logger.info(f"--- 📄 Đang xử lý file: {file_path.relative_to(reporting_root).as_posix()} ---")
    
    file_only_results: List[FileResult] = []
    resolved_file = file_path.resolve()
    if resolved_file in processed_files:
        logger.info("   -> Bỏ qua (đã xử lý).")
        logger.info("")
        return []
        
    # 1. Kiểm tra extension
    file_ext = "".join(file_path.suffixes).lstrip('.')
    if file_ext not in file_extensions:
        logger.warning(f"⚠️ Bỏ qua file '{file_path.name}': không khớp extensions (.{file_ext})")
        logger.info("")
        return []

    # 2. Phân tích
    all_clean: bool = getattr(cli_args, 'all_clean', False)
    result = analyze_file_content(file_path, logger, all_clean)
    if result:
        file_only_results.append(result)
    processed_files.add(resolved_file)
    
    # 3. Báo cáo
    if file_only_results:
        print_dry_run_report_for_group(logger, file_path.name, file_only_results, reporting_root)
    else:
        logger.info(f"  -> 🤷 Không tìm thấy thay đổi nào cần thiết.")

    logger.info("") # Dòng trống
    return file_only_results


# --- 2. HÀM HELPER XỬ LÝ THƯ MỤC ---

def _process_ndoc_task_dir(
    scan_dir: Path,
    cli_args: argparse.Namespace,
    logger: logging.Logger,
    processed_files: Set[Path],
    reporting_root: Path,
    script_file_path: Path
) -> List[FileResult]:
    """
    (HELPER 2)
    Xử lý logic ndoc cho một thư mục đầu vào.
    """
    logger.info(f"--- 📁 Quét thư mục: {scan_dir.name} ---")
    
    # 1. Tải/Merge Config (cục bộ)
    file_config_data = load_config_files(scan_dir, logger)
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

    # 2. Quét file (dùng scan_dir làm cả start_path và scan_root)
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
    all_clean: bool = getattr(cli_args, 'all_clean', False)
    
    for file_path in files_in_dir:
        resolved_file = file_path.resolve()
        if resolved_file in processed_files:
            continue 

        result = analyze_file_content(file_path, logger, all_clean)
        if result:
            dir_results.append(result)
        processed_files.add(resolved_file)
        
    # 5. Báo cáo kết quả nhóm
    if dir_results:
        print_dry_run_report_for_group(logger, scan_dir.name, dir_results, reporting_root)
        
    logger.info(f"--- ✅ Kết thúc {scan_dir.name} ---")
    logger.info("")
    
    return dir_results


# --- 3. HÀM ĐIỀU PHỐI CHÍNH (REFACTORED) ---

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
    
    all_results: List[FileResult] = []
    processed_files: Set[Path] = set()
    reporting_root = Path.cwd()

    all_clean: bool = getattr(cli_args, 'all_clean', False)
    if all_clean:
        logger.info("⚠️ Chế độ ALL-CLEAN đã bật: Sẽ loại bỏ cả Docstring VÀ Comments (nếu cleaner hỗ trợ).")

    # 1. Hợp nhất config MỘT LẦN cho các file lẻ
    cli_extensions_str: Optional[str] = getattr(cli_args, 'extensions', None)
    default_file_config = merge_ndoc_configs(
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
            results = _process_ndoc_task_file(
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
            results = _process_ndoc_task_dir(
                scan_dir=scan_dir,
                cli_args=cli_args,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
                script_file_path=script_file_path
            )
            all_results.extend(results)

    if not all_results and (files_to_process or dirs_to_scan):
        logger.info("Quét hoàn tất. Không tìm thấy file nào cần thay đổi.")
        
    return all_results