#!/usr/bin/env python3
# Path: scripts/check_path.py

import sys
import argparse
import logging
from pathlib import Path
from typing import List # <--- Thêm List

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
    
    # --- MODIFIED: Thêm css, md vào default ---
    parser.add_argument(
        "-e", "--extensions", 
        default="py,js,ts,css,scss,zsh,sh,md", 
        help="File extensions to scan (default: 'py,js,ts,css,scss,zsh,sh,md')."
    )
    # --- END MODIFIED ---
    
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
        
    check_mode = not args.fix

    # 2. Prepare arguments for the core logic
    extensions_to_scan = [ext.strip() for ext in args.extensions.split(',') if ext.strip()]
    cli_ignore_patterns = parse_comma_list(args.ignore)

    try:
        # 3. Run the core logic
        # files_to_fix giờ là List[Dict[str, Any]]
        files_to_fix = process_path_updates(
            logger=logger,
            project_root=scan_root,
            target_dir_str=args.target_directory,
            extensions=extensions_to_scan,
            cli_ignore=cli_ignore_patterns,
            script_file_path=THIS_SCRIPT_PATH,
            check_mode=check_mode 
        )

        processed_count = len(files_to_fix)

        # 4. Report results
        if processed_count > 0:
            
            # --- MODIFIED: Luôn in báo cáo chi tiết ---
            logger.warning(f"⚠️ {processed_count} files do not conform to the path convention:")
            for info in files_to_fix:
                file_path = info["path"]
                first_line = info["line"]
                logger.warning(f"   -> {file_path.relative_to(scan_root).as_posix()}")
                logger.warning(f"      (L1: {first_line})")
            # --- END MODIFIED ---

            if check_mode:
                # --- Chế độ "check" (mặc định) ---
                logger.warning("\n-> Run 'cpath --fix' to fix them automatically.")
                sys.exit(1) 
            else:
                # --- Chế độ "--fix" ---
                # --- NEW: Thêm bước xác nhận ---
                try:
                    confirmation = input("\nProceed to fix these files? (y/n): ")
                except EOFError:
                    confirmation = 'n' # Coi Ctrl+D (EOF) là 'n'
                
                if confirmation.lower() == 'y':
                    logger.debug("User confirmed fix. Proceeding to write files.")
                    written_count = 0
                    for info in files_to_fix:
                        file_path: Path = info["path"]
                        new_lines: List[str] = info["new_lines"]
                        try:
                            # Đây là nơi duy nhất script ghi file
                            with file_path.open('w', encoding='utf-8') as f:
                                f.writelines(new_lines)
                            logger.info(f"Fixed: {file_path.relative_to(scan_root).as_posix()}")
                            written_count += 1
                        except IOError as e:
                            logger.error(f"❌ Failed to write file {file_path.relative_to(scan_root).as_posix()}: {e}")
                    
                    log_success(logger, f"Done! Fixed {written_count} files.")
                
                else:
                    logger.warning("Fix operation cancelled by user.")
                    sys.exit(0) # Thoát (không lỗi) vì người dùng chủ động hủy
                # --- END NEW ---
                
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