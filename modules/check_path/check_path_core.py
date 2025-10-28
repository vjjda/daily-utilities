# Path: modules/check_path/check_path_core.py

"""
Core Orchestration logic for the Path Checker (cpath) module.
"""

import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any

from .check_path_loader import load_config_files
from .check_path_merger import merge_check_path_configs
from .check_path_scanner import scan_for_files
from .check_path_analyzer import analyze_files_for_path_comments

__all__ = ["process_check_path_logic"]

def process_check_path_logic(
    logger: logging.Logger,
    project_root: Path,
    cli_args: argparse.Namespace,
    script_file_path: Path
) -> List[Dict[str, Any]]: 
    """
    Điều phối toàn bộ quá trình kiểm tra đường dẫn (Orchestrator).

    Luồng xử lý:
    1. Tải Config (gọi Loader)
    2. Hợp nhất Config (gọi Merger)
    3. Quét File (gọi Scanner)
    4. Phân tích File (gọi Analyzer)

    Args:
        logger: Logger.
        project_root: Gốc dự án đã xác thực.
        cli_args: Namespace đối số thô từ entrypoint.
        script_file_path: Đường dẫn của chính script cpath (để bỏ qua).

    Returns:
        Danh sách các dict (files_needing_fix) từ Analyzer.
    """
    
    # 1. Tải Config
    file_config_data = load_config_files(project_root, logger)
    
    # 2. Hợp nhất Cấu hình
    cli_extensions: Optional[str] = getattr(cli_args, 'extensions', None)
    cli_ignore: Optional[str] = getattr(cli_args, 'ignore', None)
    
    merged_config = merge_check_path_configs(
         logger=logger,
        cli_extensions=cli_extensions,
        cli_ignore=cli_ignore,
        file_config_data=file_config_data
    )
    
    final_extensions_list = merged_config["final_extensions_list"]
    final_ignore_list = merged_config["final_ignore_list"]
    
    # 3. Quét file
    target_dir_str: Optional[str] = getattr(cli_args, 'target_directory_arg', None)
    check_mode: bool = getattr(cli_args, 'dry_run', False) # 'check_mode' là tên cũ, 'dry_run' là cờ

    files_to_process = scan_for_files(
         logger=logger,
        project_root=project_root,
        # Chỉ truyền target_dir_str nếu nó khác default (".")
        target_dir_str=target_dir_str if target_dir_str != "." else None,
        extensions=final_extensions_list,
        ignore_list=final_ignore_list,
        script_file_path=script_file_path,
        check_mode=check_mode
    )
    
    # 4. Phân tích file
    return analyze_files_for_path_comments(
        files_to_process, 
        project_root, 
        logger
    )