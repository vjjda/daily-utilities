# Path: modules/no_doc/no_doc_core.py

"""
Core Orchestration logic for the no_doc module.
"""

import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import sys

# Thiết lập sys.path
if not 'PROJECT_ROOT' in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from utils.core import find_git_root
from .no_doc_loader import load_config_files
from .no_doc_merger import merge_ndoc_configs
# SỬA: Import tên hàm analyzer mới
from .no_doc_analyzer import analyze_file_content
from .no_doc_scanner import scan_files

__all__ = ["process_no_doc_logic"]

FileResult = Dict[str, Any] # Type alias

def process_no_doc_logic(
    logger: logging.Logger,
    project_root: Path,
    cli_args: argparse.Namespace,
    script_file_path: Path
) -> List[FileResult]:
    """
    Điều phối toàn bộ quá trình xóa docstring (Orchestrator).
    """

    # 1. Tải và Hợp nhất Cấu hình (Không đổi)
    file_config_data = load_config_files(project_root, logger)

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

    # 2. Quét file (Không đổi)
    target_path: Path = getattr(cli_args, 'start_path_path')

    files_to_process = scan_files(
         logger=logger,
         start_path=target_path,
         ignore_list=final_ignore_list,
         extensions=final_extensions_list, # Scanner vẫn dùng list extensions
         scan_root=project_root,
         script_file_path=script_file_path
    )

    if not files_to_process:
        logger.warning("Không tìm thấy file nào khớp với tiêu chí để xử lý.")
        return []

    logger.info(f"Tìm thấy {len(files_to_process)} file để phân tích...")

    # 3. Phân tích file (Xóa Docstring/Comment)
    files_needing_fix: List[FileResult] = []

    all_clean: bool = getattr(cli_args, 'all_clean', False)
    if all_clean:
        logger.info("⚠️ Chế độ ALL-CLEAN đã bật: Sẽ loại bỏ cả Docstring VÀ Comments (nếu cleaner hỗ trợ).")

    for file_path in files_to_process:
        # SỬA: Gọi tên hàm analyzer mới
        result = analyze_file_content(file_path, logger, all_clean)
        if result:
            files_needing_fix.append(result)

    return files_needing_fix