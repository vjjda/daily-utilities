# Path: modules/no_doc/no_doc_core.py

"""
Core Orchestration logic for the no_doc module.
"""

import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set
import sys  # <-- SỬA LỖI: Thêm import sys

# Thiết lập sys.path
if not 'PROJECT_ROOT' in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from utils.core import find_git_root
try:
    # Tạm thời dùng Tuple nếu ScanTask chưa được export
    from utils.cli import ScanTask
except ImportError:
    ScanTask = Tuple[Path, Path] # type: ignore

from .no_doc_loader import load_config_files
from .no_doc_merger import merge_ndoc_configs
from .no_doc_analyzer import analyze_file_content
from .no_doc_scanner import scan_files

__all__ = ["process_no_doc_logic"]

FileResult = Dict[str, Any] # Type alias

def process_no_doc_logic(
    logger: logging.Logger,
    scan_tasks: List[ScanTask], # <-- THAY ĐỔI: Nhận List[ScanTask]
    cli_args: argparse.Namespace,
    script_file_path: Path
) -> List[FileResult]:
    """
    Điều phối toàn bộ quá trình xóa docstring (Orchestrator).
    """

    # 1. Tải và Hợp nhất Cấu hình
    # Tải config từ thư mục làm việc hiện tại (hoặc gốc của tác vụ đầu tiên)
    config_load_dir = scan_tasks[0].scan_root if scan_tasks else Path.cwd()
    file_config_data = load_config_files(config_load_dir, logger)

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

    # 2. Quét file (THAY ĐỔI: Lặp qua các tác vụ)
    processed_files: Set[Path] = set()
    all_files_to_process: List[Path] = []

    logger.info(f"Đang xử lý {len(scan_tasks)} tác vụ quét...")

    for task in scan_tasks:
        start_path, scan_root = task  # Giải nén ScanTask
        
        logger.debug(f"Đang quét tác vụ: start_path='{start_path.name}', scan_root='{scan_root.name}'")
        
        files_for_task = scan_files(
             logger=logger,
             start_path=start_path,
             ignore_list=final_ignore_list, # Config dùng chung
             extensions=final_extensions_list,
             scan_root=scan_root, # Gốc riêng của tác vụ
             script_file_path=script_file_path
        )
        
        for file_path in files_for_task:
            resolved_file = file_path.resolve()
            if resolved_file not in processed_files:
                processed_files.add(resolved_file)
                all_files_to_process.append(file_path)

    if not all_files_to_process:
        logger.warning("Không tìm thấy file nào khớp với tiêu chí để xử lý.")
        return []

    logger.info(f"Tổng cộng tìm thấy {len(all_files_to_process)} file duy nhất để phân tích...")

    # 3. Phân tích file (Không đổi)
    files_needing_fix: List[FileResult] = []
    all_clean: bool = getattr(cli_args, 'all_clean', False)
    if all_clean:
        logger.info("⚠️ Chế độ ALL-CLEAN đã bật: Sẽ loại bỏ cả Docstring VÀ Comments (nếu cleaner hỗ trợ).")

    for file_path in all_files_to_process:
        result = analyze_file_content(file_path, logger, all_clean)
        if result:
            files_needing_fix.append(result)

    return files_needing_fix