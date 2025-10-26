#!/usr/bin/env python3
# Path: scripts/check_path.py

import sys
import logging
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
import shlex

try:
    import tomllib 
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

import typer

# Common utilities
from utils.logging_config import setup_logging, log_success
# --- MODIFIED: Xóa các import logic nghiệp vụ ---
from utils.core import (
    is_git_repository, find_git_root,
)
# --- END MODIFIED ---
from utils.cli import handle_config_init_request, handle_project_root_validation

# Module Imports
from modules.check_path import (
    process_check_path_logic,
    execute_check_path_action,
    DEFAULT_EXTENSIONS_STRING,
    DEFAULT_IGNORE,
    PROJECT_CONFIG_FILENAME, 
    CONFIG_SECTION_NAME,
    CONFIG_FILENAME,
    load_config_files
)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()
MODULE_DIR = THIS_SCRIPT_PATH.parent.parent / "modules" / "check_path" 
TEMPLATE_FILENAME = "check_path.toml.template" 
CPATH_DEFAULTS: Dict[str, Any] = {
    "extensions": DEFAULT_EXTENSIONS_STRING,
    "ignore": DEFAULT_IGNORE
}

app = typer.Typer(
    help="Kiểm tra (và tùy chọn sửa) các comment '# Path:' trong file nguồn.",
    add_completion=False,
    context_settings={"help_option_names": ["--help", "-h"]}
)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    
    # ... (Các tham số Typer giữ nguyên) ...
    config_project: bool = typer.Option(
        False, "-c", "--config-project",
        help="Khởi tạo/cập nhật section [cpath] trong .project.toml.",
    ),
    config_local: bool = typer.Option(
        False, "-C", "--config-local",
        help="Khởi tạo/cập nhật file .cpath.toml (scope 'local').",
    ),
    target_directory_arg: Optional[Path] = typer.Argument(
        None,
        help="Thư mục để quét (mặc định: thư mục làm việc hiện tại, tôn trọng .gitignore). Dùng '~' cho thư mục home.",
        file_okay=False,
        dir_okay=True,
    ),
    extensions: Optional[str] = typer.Option( None, "-e", "--extensions", help=f"Các đuôi file để quét (ghi đè .project.toml)." ),
    ignore: Optional[str] = typer.Option( None, "-I", "--ignore", help="Danh sách pattern (phân cách bởi dấu phẩy) để bỏ qua (thêm vào .project.toml)." ),
    dry_run: bool = typer.Option(
        False,
        "-d", "--dry-run",
        help="Chỉ chạy ở chế độ 'dry-run' (chạy thử). Mặc định là chạy 'fix' (có hỏi xác nhận)."
    )
):
    """ Hàm chính (callback của Typer) """
    if ctx.invoked_subcommand: return

    # 1. Setup Logging
    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")

    # --- Logic khởi tạo Config (Giữ nguyên) ---
    try:
        config_action_taken = handle_config_init_request(
            logger=logger,
            config_project=config_project,
            config_local=config_local,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename=CONFIG_FILENAME,
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            default_values=CPATH_DEFAULTS
        )
        
        if config_action_taken:
            raise typer.Exit(code=0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise typer.Exit(code=1)

    # --- Logic xác định scan_root (Giữ nguyên) ---
    if target_directory_arg:
        scan_root = target_directory_arg.expanduser()
    else:
        scan_root = Path.cwd().expanduser()
    
    if not scan_root.exists():
        logger.error(f"❌ Lỗi: Thư mục mục tiêu không tồn tại (sau khi expanduser): {scan_root}")
        raise typer.Exit(code=1)
    if not scan_root.is_dir():
        logger.error(f"❌ Lỗi: Đường dẫn mục tiêu không phải là thư mục: {scan_root}")
        raise typer.Exit(code=1)

    # --- Logic handle_project_root_validation (Giữ nguyên) ---
    effective_scan_root: Optional[Path]
    effective_scan_root, git_warning_str = handle_project_root_validation(
        logger=logger,
        scan_root=scan_root,
        force_silent=False 
    )
    
    if effective_scan_root is None:
        raise typer.Exit(code=0)

    check_mode = dry_run
    
    # --- Chỉ tải config, không xử lý ---
    file_config_data = load_config_files(effective_scan_root, logger)
    
    # --- Xóa logic merge 'extensions' và 'ignore' khỏi đây ---
    
    # (Logic tạo fix_command_str giữ nguyên)
    original_args = sys.argv[1:]
    filtered_args = [
        shlex.quote(arg) for arg in original_args
        if arg not in ('-d', '--dry-run', '--fix', '-c', '--config-project', '-C', '--config-local')
    ]
    fix_command_str = "cpath " + " ".join(filtered_args)

    try:
        # --- MODIFIED: Thay đổi lời gọi hàm, truyền giá trị thô ---
        files_to_fix = process_check_path_logic(
            logger=logger, project_root=effective_scan_root,
            target_dir_str=str(target_directory_arg) if effective_scan_root == scan_root and target_directory_arg else None,
            cli_extensions=extensions,     # <-- Truyền giá trị thô
            cli_ignore=ignore,           # <-- Truyền giá trị thô
            file_config_data=file_config_data, # <-- Truyền dict config
            script_file_path=THIS_SCRIPT_PATH,
            check_mode=check_mode
        )
        # --- END MODIFIED ---
        
        # (Lệnh gọi execute_check_path_action giữ nguyên)
        execute_check_path_action(
            logger=logger, files_to_fix=files_to_fix, check_mode=check_mode,
            fix_command_str=fix_command_str, scan_root=effective_scan_root,
            git_warning_str=git_warning_str
        )

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng kiểm tra đường dẫn."); sys.exit(1)