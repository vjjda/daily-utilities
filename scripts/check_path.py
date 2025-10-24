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
from utils.core import parse_comma_list, is_git_repository, find_git_root

# --- MODIFIED: Import from module gateway ---
from modules.path_checker import (
    process_path_updates,
    handle_results,
    DEFAULT_EXTENSIONS_STRING
)
# --- END MODIFIED ---

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
        default=DEFAULT_EXTENSIONS_STRING, 
        help=f"File extensions to scan (default: '{DEFAULT_EXTENSIONS_STRING}')."
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
    
    # --- NEW: Logic gợi ý Git Root ---
    git_warning_str = ""
    effective_scan_root = scan_root # Biến này sẽ được dùng để quét
    
    # 1. Nếu thư mục hiện tại không phải là Git root
    if not is_git_repository(scan_root):
        
        # 2. Tìm kiếm thư mục Git root gần nhất
        suggested_root = find_git_root(scan_root.parent)
        
        if suggested_root:
            # Gợi ý chuyển sang thư mục Git root
            logger.warning(f"⚠️ Current directory '{scan_root.name}/' is not a Git root.")
            logger.warning(f"   Git root found at: {suggested_root.as_posix()}")
            
            try:
                # Hỏi người dùng
                confirmation = input("   Do you want to run the scan from the Git root? (Y/n): ")
            except EOFError:
                confirmation = 'n'
            
            if confirmation.lower() in ('y', ''): # Mặc định là 'y'
                # Chuyển scan_root sang thư mục được đề xuất
                effective_scan_root = suggested_root
                logger.info(f"✅ Scanning moved to Git root: {effective_scan_root.as_posix()}")
            else:
                # Nếu không đồng ý, vẫn tiếp tục, nhưng đưa ra cảnh báo
                git_warning_str = f"⚠️ Warning: Running from non-Git root '{scan_root.name}/'. .gitignore rules might be incomplete."
        else:
            # Không tìm thấy Git root, đưa ra cảnh báo chung
            git_warning_str = f"⚠️ Warning: '{scan_root.name}/' does not contain a '.git' directory. Ensure this is the correct project root."
    
    # Nếu đã là Git root, không cần làm gì
    
    # --- END NEW: Logic gợi ý Git Root ---

    check_mode = not args.fix

    # --- Xây dựng lệnh "fix" ---
    original_args = sys.argv[1:]
    # ... (logic xây dựng fix_command_str giữ nguyên) ...
    filtered_args = []
    for arg in original_args:
        if arg not in ('--check', '--fix'):
            filtered_args.append(shlex.quote(arg))
    filtered_args.append('--fix')
    fix_command_str = "cpath " + " ".join(filtered_args)

    # 2. Prepare arguments for the core logic
    extensions_to_scan = [ext.strip() for ext in args.extensions.split(',') if ext.strip()]
    cli_ignore_patterns = parse_comma_list(args.ignore)

    try:
        # 3. Run the core logic
        files_to_fix = process_path_updates(
            logger=logger,
            project_root=effective_scan_root,
            target_dir_str=args.target_directory,
            extensions=extensions_to_scan,
            cli_ignore=cli_ignore_patterns,
            script_file_path=THIS_SCRIPT_PATH,
            check_mode=check_mode
        )

        # 4. Handle Results
        handle_results(
            logger=logger,
            files_to_fix=files_to_fix,
            check_mode=check_mode,
            fix_command_str=fix_command_str,
            scan_root=effective_scan_root, 
            git_warning_str=git_warning_str
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