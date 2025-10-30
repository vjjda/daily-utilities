# Path: modules/stubgen/stubgen_core.py
"""
Core logic for the Stub Generator (sgen) module.
Handles Orchestration (Pure Logic).
"""

import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple

# SỬA: Import các hàm Task từ facade nội bộ
from .stubgen_internal import (
    process_stubgen_task_file,
    process_stubgen_task_dir
)

# Import tiện ích chung
from utils.core import load_text_template

MODULE_DIR = Path(__file__).parent
TEMPLATE_FILENAME = "pyi.py.template"

StubResult = Dict[str, Any]

__all__ = ["process_stubgen_logic"]

# (ĐÃ XÓA: _process_single_gateway)
# (ĐÃ XÓA: _process_stubgen_task_file)
# (ĐÃ XÓA: _process_stubgen_task_dir)

def process_stubgen_logic(
    logger: logging.Logger, 
    cli_args: argparse.Namespace,
    script_file_path: Path,
    files_to_process: List[Path],
    dirs_to_scan: List[Path]
) -> Tuple[List[StubResult], List[StubResult]]:
    """
    Điều phối toàn bộ quá trình tạo stub (Logic thuần túy, không I/O ghi).
    Xử lý các file và thư mục đầu vào theo logic cục bộ.
    
    Returns:
        Tuple[List[StubResult], List[StubResult]]:
            - all_files_to_create
            - all_files_to_overwrite
    """
    
    # 1. Load Template (một lần)
    try:
        template_path = MODULE_DIR / TEMPLATE_FILENAME
        stub_template_str = load_text_template(template_path, logger)
    except Exception as e:
        logger.error(f"❌ Không thể tải PYI template: {e}")
        raise

    total_files_to_create: List[StubResult] = []
    total_files_to_overwrite: List[StubResult] = []
    processed_files: Set[Path] = set()
    reporting_root = Path.cwd()

    # 2. XỬ LÝ CÁC FILE RIÊNG LẺ
    if files_to_process:
        for file_path in files_to_process:
            # SỬA: Gọi hàm task đã import
            create, overwrite = process_stubgen_task_file(
                file_path=file_path,
                cli_args=cli_args,
                stub_template_str=stub_template_str,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root
            )
            total_files_to_create.extend(create)
            total_files_to_overwrite.extend(overwrite)

    # 3. XỬ LÝ CÁC THƯ MỤC
    if dirs_to_scan:
        logger.info(f"Đang xử lý {len(dirs_to_scan)} thư mục...")
        for scan_dir in dirs_to_scan:
            # SỬA: Gọi hàm task đã import
            create, overwrite = process_stubgen_task_dir(
                scan_dir=scan_dir,
                cli_args=cli_args,
                stub_template_str=stub_template_str,
                logger=logger,
                processed_files=processed_files,
                reporting_root=reporting_root,
                script_file_path=script_file_path
            )
            total_files_to_create.extend(create)
            total_files_to_overwrite.extend(overwrite)

    return total_files_to_create, total_files_to_overwrite