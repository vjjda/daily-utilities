#!/usr/bin/env python3
# Path: scripts/check_path.py

"""
Entrypoint (cổng vào) cho cpath (Check Path).

Script này chịu trách nhiệm:
1. Thiết lập `sys.path` để import `utils` và `modules`.
2. Phân tích đối số dòng lệnh (Argparse).
3. Cấu hình logging.
4. Xử lý các yêu cầu khởi tạo config (`--config-local`, `--config-project`).
5. Xác thực đường dẫn quét (`target_directory_arg`) và gốc Git.
6. Gọi `process_check_path_logic` (từ Core) để lấy danh sách file cần sửa.
7. Gọi `execute_check_path_action` (từ Executor) để thực hiện side-effects.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional, Set, Dict, Any, Final
import shlex

try: import tomllib 
except ImportError:
    try: import toml as tomllib
    except ImportError: tomllib = None

# Thiết lập `sys.path` để import các module của dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import các tiện ích chung
from utils.logging_config import setup_logging, log_success
from utils.core import is_git_repository, find_git_root
from utils.cli import handle_config_init_request, handle_project_root_validation

# Import các thành phần của module 'check_path'
from modules.check_path import (
    process_check_path_logic,
    execute_check_path_action,
    DEFAULT_EXTENSIONS, 
    DEFAULT_IGNORE,
    PROJECT_CONFIG_FILENAME, 
    CONFIG_SECTION_NAME,
    CONFIG_FILENAME
)

# --- HẰNG SỐ CỤ THỂ CHO ENTRYPOINT ---
THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()
MODULE_DIR: Final[Path] = THIS_SCRIPT_PATH.parent.parent / "modules" / "check_path" 
TEMPLATE_FILENAME: Final[str] = "check_path.toml.template" 

# Cấu hình mặc định để điền vào file template .toml khi khởi tạo
CPATH_DEFAULTS: Final[Dict[str, Any]] = {
    "extensions": DEFAULT_EXTENSIONS, 
    "ignore": DEFAULT_IGNORE
}


def main():
    """ Hàm điều phối chính (phiên bản Argparse) """
    
    # 1. Định nghĩa Parser
    parser = argparse.ArgumentParser(
        description="Kiểm tra (và tùy chọn sửa) các comment '# Path:' trong file nguồn.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    path_check_group = parser.add_argument_group("Path Checking Options")
    path_check_group.add_argument(
        "target_directory_arg",
        nargs='?',
        default=".",
        help="Thư mục để quét (mặc định: thư mục làm việc hiện tại).",
    )
    path_check_group.add_argument(
        "-e", "--extensions",
        type=str,
        default=None,
        help="Các đuôi file.\nMặc định (không có +/-): Ghi đè config/default.\nDùng + (thêm) hoặc ~ (bớt) để chỉnh sửa.\nVí dụ: 'py,js' (ghi đè), '+ts,md' (thêm), '~py' (bớt)."
    )
    path_check_group.add_argument(
        "-I", "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern để bỏ qua (THÊM vào config/default)."
    )
    path_check_group.add_argument(
        "-d", "--dry-run",
        action="store_true", 
        help="Chỉ chạy ở chế độ 'dry-run' (kiểm tra). Mặc định là chạy 'fix'."
    )
    
    config_group = parser.add_argument_group("Config Initialization (Chạy riêng lẻ)")
    config_group.add_argument(
        "-c", "--config-project",
        action="store_true",
        help=f"Khởi tạo/cập nhật section [{CONFIG_SECTION_NAME}] trong {PROJECT_CONFIG_FILENAME}."
    )
    config_group.add_argument(
        "-C", "--config-local", 
        action="store_true",
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} (scope 'local')."
    )
    
    args = parser.parse_args()

    # 2. Setup Logging
    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")

    # 3. Xử lý Config Init
    try:
        config_action_taken = handle_config_init_request(
            logger=logger,
            config_project=args.config_project,
            config_local=args.config_local,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename=CONFIG_FILENAME,
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            base_defaults=CPATH_DEFAULTS
        )
        if config_action_taken:
            sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # 4. Xử lý Path và Validation
    scan_root_str = args.target_directory_arg 
    scan_root = Path(scan_root_str).expanduser().resolve()
    
    if not scan_root.exists():
        logger.error(f"❌ Lỗi: Thư mục mục tiêu không tồn tại: {scan_root}")
        sys.exit(1)
    if not scan_root.is_dir():
        logger.error(f"❌ Lỗi: Đường dẫn mục tiêu không phải là thư mục: {scan_root}")
        sys.exit(1)

    # Xác thực xem đây có phải là gốc Git không (hoặc hỏi người dùng)
    effective_scan_root: Optional[Path]
    effective_scan_root, git_warning_str = handle_project_root_validation(
        logger=logger, 
        scan_root=scan_root, 
        force_silent=False # cpath không có cờ --force
    )
    
    if effective_scan_root is None:
        # Người dùng đã chọn 'Quit' trong handle_project_root_validation
        sys.exit(0)

    # 5. Chuẩn bị và Chạy Core Logic
    
    # Chế độ 'check' (dry-run) hay 'fix' (default)
    check_mode = args.dry_run

    # Tái tạo chuỗi lệnh fix_command_str cho output của executor
    original_args = sys.argv[1:]
    excluded_flags = ['-d', '--dry-run', '-c', '--config-project', '-C', '--config-local']
    
    fix_command_args = [
        shlex.quote(arg) for arg in original_args 
        if arg not in excluded_flags
    ]
    fix_command_str = "cpath " + " ".join(fix_command_args)

    try:
        # Core sẽ tự load config, merge, scan, và analyze
        files_to_fix = process_check_path_logic(
            logger=logger, 
            project_root=effective_scan_root,
            cli_args=args, # Truyền thẳng namespace vào core
            script_file_path=THIS_SCRIPT_PATH
        )
        
        # Executor thực hiện side-effect (báo cáo, ghi file)
        execute_check_path_action(
            logger=logger, 
            files_to_fix=files_to_fix, 
            check_mode=check_mode,
            fix_command_str=fix_command_str, 
            scan_root=effective_scan_root,
            git_warning_str=git_warning_str
        )

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng kiểm tra đường dẫn.")
        sys.exit(1)