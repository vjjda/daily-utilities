#!/usr/bin/env python3
# Path: scripts/check_path.py

import sys
import argparse
import logging
from pathlib import Path

# Common utilities
from utils.logging_config import setup_logging, log_success
from utils.core import parse_comma_list

# Import the main logic
from modules.path_checker.path_checker_core import process_path_updates

# --- CONSTANTS ---
THIS_SCRIPT_PATH = Path(__file__).resolve()

def main():
    """Main orchestration function: Parses args and runs the path checker."""
    
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
        default="py,js,ts,css,scss,zsh,sh", 
        help="File extensions to scan (default: 'py,js,ts,css,scss,zsh,sh')."
    )
    parser.add_argument(
        "-I", "--ignore", 
        type=str, 
        help="Comma-separated list of additional patterns to ignore."
    )
    # --- MODIFIED: Thay --check bằng --fix ---
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix files in place. (Default is 'check' mode/dry-run)."
    )
    # --- END MODIFIED ---
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
        
    # --- MODIFIED: Đảo ngược logic check_mode ---
    # Mặc định, check_mode là True (dry-run)
    # Nếu người dùng chạy `cpath --fix`, args.fix sẽ là True,
    # và check_mode sẽ trở thành False (tức là "đừng check nữa, hãy fix đi")
    check_mode = not args.fix
    # --- END MODIFIED ---

    # 2. Prepare arguments for the core logic
    extensions_to_scan = [ext.strip() for ext in args.extensions.split(',') if ext.strip()]
    cli_ignore_patterns = parse_comma_list(args.ignore)

    try:
        # 3. Run the core logic
        files_to_fix = process_path_updates(
            logger=logger,
            project_root=scan_root,
            target_dir_str=args.target_directory,
            extensions=extensions_to_scan,
            cli_ignore=cli_ignore_patterns,
            script_file_path=THIS_SCRIPT_PATH,
            check_mode=check_mode # Truyền vào logic đã đảo ngược
        )

        processed_count = len(files_to_fix)

        # 4. Report results
        if processed_count > 0:
            # --- MODIFIED: Cập nhật logic báo cáo ---
            if check_mode:
                # Đây là chế độ mặc định (dry-run)
                logger.warning(f"⚠️ [Check Mode] {processed_count} files do not conform to the path convention:")
                for file_path in files_to_fix:
                    logger.warning(f"   -> {file_path.relative_to(scan_root).as_posix()}")
                logger.warning("\n-> Run 'cpath --fix' to fix them automatically.")
                sys.exit(1) # Thoát với mã lỗi 1 cho CI/CD
            else:
                # Đây là chế độ --fix
                log_success(logger, f"Done! Fixed {processed_count} files.")
            # --- END MODIFIED ---
        else:
            log_success(logger, "All files already conform to the convention. No changes needed.")

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