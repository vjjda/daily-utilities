#!/usr/bin/env python3
# Path: scripts/check_path.py

import sys
import logging
from pathlib import Path
from typing import List, Optional, Set, Dict, Any
import shlex

try: import tomllib 
except ImportError:
    try: import toml as tomllib
    except ImportError: tomllib = None

import typer

from utils.logging_config import setup_logging, log_success
from utils.core import is_git_repository, find_git_root
from utils.cli import handle_config_init_request, handle_project_root_validation

# --- MODIFIED: Import hằng số mới ---
from modules.check_path import (
    process_check_path_logic,
    execute_check_path_action,
    DEFAULT_EXTENSIONS, # <-- Import Set mới
    DEFAULT_IGNORE,
    PROJECT_CONFIG_FILENAME, 
    CONFIG_SECTION_NAME,
    CONFIG_FILENAME,
    load_config_files
)
# --- END MODIFIED ---

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()
MODULE_DIR = THIS_SCRIPT_PATH.parent.parent / "modules" / "check_path" 
TEMPLATE_FILENAME = "check_path.toml.template" 
# --- MODIFIED: Cập nhật CPATH_DEFAULTS ---
CPATH_DEFAULTS: Dict[str, Any] = {
    "extensions": DEFAULT_EXTENSIONS, # <-- Dùng Set
    "ignore": DEFAULT_IGNORE
}
# --- END MODIFIED ---

app = typer.Typer(
    help="Kiểm tra (và tùy chọn sửa) các comment '# Path:' trong file nguồn.",
    add_completion=False,
    context_settings={"help_option_names": ["--help", "-h"]}
)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    
    config_project: bool = typer.Option(False, "-c", "--config-project", help="Khởi tạo/cập nhật section [cpath] trong .project.toml."),
    config_local: bool = typer.Option(False, "-C", "--config-local", help="Khởi tạo/cập nhật file .cpath.toml (scope 'local')."),
    target_directory_arg: Optional[Path] = typer.Argument(None, help="Thư mục để quét (mặc định: thư mục làm việc hiện tại).", file_okay=False, dir_okay=True),
    # --- MODIFIED: Cập nhật help text cho extensions ---
    extensions: Optional[str] = typer.Option(None, "-e", "--extensions", help="Các đuôi file để quét (THÊM vào config/default)."),
    # --- END MODIFIED ---
    ignore: Optional[str] = typer.Option(None, "-I", "--ignore", help="Danh sách pattern để bỏ qua (THÊM vào config/default)."),
    dry_run: bool = typer.Option(False, "-d", "--dry-run", help="Chỉ chạy ở chế độ 'dry-run'. Mặc định là chạy 'fix'.")
):
    """ Hàm chính (callback của Typer) """
    if ctx.invoked_subcommand: return

    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")

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
            base_defaults=CPATH_DEFAULTS
        )
        if config_action_taken: raise typer.Exit(code=0)
    except typer.Exit as e: raise e
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise typer.Exit(code=1)

    if target_directory_arg: scan_root = target_directory_arg.expanduser()
    else: scan_root = Path.cwd().expanduser()
    
    if not scan_root.exists():
        logger.error(f"❌ Lỗi: Thư mục mục tiêu không tồn tại: {scan_root}")
        raise typer.Exit(code=1)
    if not scan_root.is_dir():
        logger.error(f"❌ Lỗi: Đường dẫn mục tiêu không phải là thư mục: {scan_root}")
        raise typer.Exit(code=1)

    effective_scan_root: Optional[Path]
    effective_scan_root, git_warning_str = handle_project_root_validation(logger=logger, scan_root=scan_root, force_silent=False)
    
    if effective_scan_root is None: raise typer.Exit(code=0)

    # --- Sửa lỗi logic check_mode: Nếu không dry_run thì là fix mode ---
    check_mode = dry_run # True nếu có -d, False nếu không
    # --- End sửa lỗi ---
    
    file_config_data = load_config_files(effective_scan_root, logger)
    
    original_args = sys.argv[1:]
    filtered_args = [ shlex.quote(arg) for arg in original_args if arg not in ('-d', '--dry-run', '-c', '--config-project', '-C', '--config-local')]
    # --- Sửa lỗi tạo fix_command: Bỏ --fix nếu có ---
    fix_command_str = "cpath " + " ".join(arg for arg in filtered_args if arg != '--fix')
    # --- End sửa lỗi ---

    try:
        files_to_fix = process_check_path_logic(
            logger=logger, project_root=effective_scan_root,
            target_dir_str=str(target_directory_arg) if effective_scan_root == scan_root and target_directory_arg else None,
            cli_extensions=extensions,
            cli_ignore=ignore,
            file_config_data=file_config_data,
            script_file_path=THIS_SCRIPT_PATH,
            check_mode=check_mode
        )
        
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
    try: app()
    except KeyboardInterrupt: print("\n\n❌ [Lệnh dừng] Đã dừng kiểm tra đường dẫn."); sys.exit(1)