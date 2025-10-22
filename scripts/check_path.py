#!/usr/bin/env python3
# Path: scripts/check_path.py

import sys
import argparse
import logging
from pathlib import Path
from typing import List
import shlex

# Common utilities
from utils.logging_config import setup_logging
# --- MODIFIED: Import is_git_repository ---
from utils.core import parse_comma_list, is_git_repository
# --- END MODIFIED ---

# Import the main logic
from modules.path_checker.path_checker_core import process_path_updates
from modules.path_checker.path_checker_executor import handle_results

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()

def main():
    """
    Main orchestration function.
    Parses args, calls core analysis, and calls executor to handle results.
    """
    
    # --- 1. Phân tích đối số (Parse args) ---
    parser = argparse.ArgumentParser(
        description="Check for (and optionally fix) '# Path:' comments in source files.",
        epilog="Default mode is a 'dry-run' (check only). Use --fix to apply changes."
    )
    parser.add_argument(
        "target_directory", 
        nargs='?', 
        default=None, 
        help="Directory to scan (default: current working directory, respects .gitignore)."
    )
    parser.add_argument(
        "-e", "--extensions", 
        default="py,js,ts,css,scss,zsh,sh,md", 
        help="File extensions to scan (default: 'py,js,ts,css,scss,zsh,sh,md')."
    )
    parser.add_argument(
        "-I", "--ignore", 
        type=str, 
        help="Comma-separated list of additional patterns to ignore."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix files in place. (Default is 'check' mode/dry-run)."
    )
    args = parser.parse_args()

    # 1. Setup Logging
    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")

    # --- Xác định thư mục gốc ---
    if args.target_directory:
        scan_root = Path(args.target_directory).resolve()
    else:
        scan_root = Path.cwd()

    if not scan_root.exists():
        logger.error(f"❌ Path does not exist: '{args.target_directory or scan_root}'")
        sys.exit(1)
        
    # --- NEW: Get Git warning, but don't print yet ---
    git_warning_str = ""
    if not is_git_repository(scan_root):
        git_warning_str = f"⚠️ Warning: '{scan_root.name}/' does not contain a '.git' directory. Ensure this is the correct project root."
    # --- END NEW ---

    check_mode = not args.fix

    # Xây dựng lệnh "fix"
    original_args = sys.argv[1:]
    filtered_args = []
    for arg in original_args:
        if arg not in ('--check', '--fix'):
            filtered_args.append(shlex.quote(arg))
    filtered_args.append('--fix')
    fix_command_str = "cpath " + " ".join(filtered_args)

    extensions_to_scan = [ext.strip() for ext in args.extensions.split(',') if ext.strip()]
    cli_ignore_patterns = parse_comma_list(args.ignore)

    try:
        # --- 3. Gọi Core (Run Core Analysis) ---
        files_to_fix = process_path_updates(
            logger=logger,
            project_root=scan_root,
            target_dir_str=args.target_directory,
            extensions=extensions_to_scan,
            cli_ignore=cli_ignore_patterns,
            script_file_path=THIS_SCRIPT_PATH,
            check_mode=check_mode
        )

        # --- 4. Gọi Executor (Handle Results) ---
        # (Toàn bộ logic báo cáo/ghi file đã chuyển vào đây)
        handle_results(
            logger=logger,
            files_to_fix=files_to_fix,
            check_mode=check_mode,
            fix_command_str=fix_command_str,
            scan_root=scan_root,
            git_warning_str=git_warning_str # <-- New parameter
        )

    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Stop Command] Path checking stopped.")
        sys.exit(1)