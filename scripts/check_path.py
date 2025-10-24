#!/usr/bin/env python3
# Path: scripts/check_path.py

import sys
import argparse 
import logging
from pathlib import Path
from typing import List, Optional
import shlex

import typer

# Common utilities
from utils.logging_config import setup_logging
from utils.core import parse_comma_list, is_git_repository, find_git_root

# Module Imports
from modules.path_checker import (
    process_path_updates,
    handle_results,
    DEFAULT_EXTENSIONS_STRING
)

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()


def main(
    target_directory_arg: Optional[Path] = typer.Argument( # <-- Đổi tên biến tạm thời
        None, 
        help="Directory to scan (default: current working directory, respects .gitignore). Use '~' for home directory.",
        # --- FIX: Đã xóa resolve_path=True và exists=True ---
        # exists=True,
        # resolve_path=True,
        # --- END FIX ---
        file_okay=False,
        dir_okay=True,
    ),
    extensions: str = typer.Option( DEFAULT_EXTENSIONS_STRING, "-e", "--extensions", help=f"File extensions to scan (default: '{DEFAULT_EXTENSIONS_STRING}')." ),
    ignore: Optional[str] = typer.Option( None, "-I", "--ignore", help="Comma-separated list of additional patterns to ignore." ),
    fix: bool = typer.Option( False, "--fix", help="Fix files in place. (Default is 'check' mode/dry-run)." )
):
    """ Check for (and optionally fix) '# Path:' comments in source files. """
    
    # 1. Setup Logging
    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")

    # --- MODIFIED: Xác định thư mục gốc + Mở rộng ~ thủ công ---
    if target_directory_arg:
        scan_root = target_directory_arg.expanduser()
    else:
        scan_root = Path.cwd().expanduser() 
    # --- END MODIFIED ---

    # --- NEW: KIỂM TRA TỒN TẠI (thủ công) ---
    if not scan_root.exists():
        logger.error(f"❌ Lỗi: Thư mục mục tiêu không tồn tại (sau khi expanduser): {scan_root}")
        raise typer.Exit(code=1)
    if not scan_root.is_dir():
        logger.error(f"❌ Lỗi: Đường dẫn mục tiêu không phải là thư mục: {scan_root}")
        raise typer.Exit(code=1)
    # --- END NEW ---
    
    # --- Logic gợi ý Git Root (Không thay đổi) ---
    git_warning_str = ""
    effective_scan_root = scan_root
    if not is_git_repository(scan_root):
        # ... (logic này giữ nguyên) ...
        suggested_root = find_git_root(scan_root.parent)
        if suggested_root:
            logger.warning(f"⚠️ Current directory '{scan_root.name}/' is not a Git root.")
            logger.warning(f"   Git root found at: {suggested_root.as_posix()}")
            try: confirmation = input("   Do you want to run the scan from the Git root? (Y/n): ")
            except EOFError: confirmation = 'n'
            if confirmation.lower() in ('y', ''):
                effective_scan_root = suggested_root
                logger.info(f"✅ Scanning moved to Git root: {effective_scan_root.as_posix()}")
            else: git_warning_str = f"⚠️ Warning: Running from non-Git root '{scan_root.name}/'. .gitignore rules might be incomplete."
        else: git_warning_str = f"⚠️ Warning: '{scan_root.name}/' does not contain a '.git' directory. Ensure this is the correct project root."
    # --- END Logic gợi ý Git Root ---

    check_mode = not fix

    # --- Xây dựng lệnh "fix" (Không thay đổi) ---
    original_args = sys.argv[1:]
    filtered_args = [shlex.quote(arg) for arg in original_args if arg not in ('--check', '--fix')]
    filtered_args.append('--fix')
    fix_command_str = "cpath " + " ".join(filtered_args)

    # --- Chuẩn bị args cho core (Không thay đổi) ---
    extensions_to_scan = [ext.strip() for ext in extensions.split(',') if ext.strip()]
    cli_ignore_patterns = parse_comma_list(ignore)

    try:
        # 3. Run the core logic
        files_to_fix = process_path_updates(
            logger=logger, project_root=effective_scan_root,
            # (Truyền đường dẫn *gốc* (chưa expand) nếu có, 
            #  vì logic core đã được thiết kế để xử lý 'None')
            target_dir_str=str(target_directory_arg) if target_directory_arg else None,
            extensions=extensions_to_scan, cli_ignore=cli_ignore_patterns,
            script_file_path=THIS_SCRIPT_PATH, check_mode=check_mode
        )

        # 4. Handle Results (Không thay đổi)
        handle_results(
            logger=logger, files_to_fix=files_to_fix, check_mode=check_mode,
            fix_command_str=fix_command_str, scan_root=effective_scan_root, 
            git_warning_str=git_warning_str
        )

    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try: typer.run(main)
    except KeyboardInterrupt: print("\n\n❌ [Stop Command] Path checking stopped."); sys.exit(1)