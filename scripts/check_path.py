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
# Determine Project Root (since this file is in 'scripts/', root is parent.parent)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Get the path to this script file itself, to avoid processing it
THIS_SCRIPT_PATH = Path(__file__).resolve()

def main():
    """Main orchestration function: Parses args and runs the path checker."""
    
    parser = argparse.ArgumentParser(
        description="Automatically update or add '# Path:' comments to source files.",
        epilog="Default mode (no target_directory) respects .gitignore."
    )
    parser.add_argument(
        "target_directory", 
        nargs='?', 
        default=None, 
        help="Directory to scan (default: entire project, respecting .gitignore)."
    )
    parser.add_argument(
        "-e", "--extensions", 
        default="py,js,ts,css,scss,md,zsh,sh", 
        help="File extensions to scan (default: 'py,js,ts,css,scss,md,zsh,sh')."
    )
    parser.add_argument(
        "-I", "--ignore", 
        type=str, 
        help="Comma-separated list of additional patterns to ignore."
    )
    args = parser.parse_args()

    # 1. Setup Logging
    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")
    
    # 2. Prepare arguments for the core logic
    extensions_to_scan = [ext.strip() for ext in args.extensions.split(',') if ext.strip()]
    cli_ignore_patterns = parse_comma_list(args.ignore)

    try:
        # 3. Run the core logic
        processed_count = process_path_updates(
            logger=logger,
            project_root=PROJECT_ROOT,
            target_dir_str=args.target_directory,
            extensions=extensions_to_scan,
            cli_ignore=cli_ignore_patterns,
            script_file_path=THIS_SCRIPT_PATH
        )

        # 4. Report results
        if processed_count > 0:
            log_success(logger, f"Done! Processed {processed_count} files.")
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