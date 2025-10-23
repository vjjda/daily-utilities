#!/usr/bin/env python3
# Path: scripts/tree.py

import sys
import argparse
import logging
from pathlib import Path

# Common utilities
from utils.logging_config import setup_logging, log_success
from utils.core import run_command, is_git_repository

# --- MODULE IMPORTS ---
# --- MODIFIED: Import `load_and_merge_config` from tree_core ---
from modules.tree.tree_core import (
    generate_tree, CONFIG_TEMPLATE, load_and_merge_config
)
# --- END MODIFIED ---
# --- MODIFIED: Import argparse defaults from SSOT ---
from modules.tree.tree_config import (
    CONFIG_FILENAME,
    DEFAULT_MAX_LEVEL_ARG,
    DEFAULT_SHOW_SUBMODULES_ARG,
    DEFAULT_DIRS_ONLY_ARG
)
# --- END MODIFIED ---
# ---------------------

def handle_init_command(logger: logging.Logger) -> None:
    """Handles the logic for the --init flag."""
    config_file_path = Path.cwd() / CONFIG_FILENAME
    file_existed = config_file_path.exists()
    
    should_write = False
    
    if file_existed:
        overwrite = input(f"'{CONFIG_FILENAME}' already exists. Overwrite? (y/n): ").lower() 
        if overwrite == 'y':
            should_write = True
            logger.debug(f"User chose to overwrite '{CONFIG_FILENAME}'.")
        else:
            logger.info(f"Skipped overwrite for existing '{CONFIG_FILENAME}'.")
    else:
        should_write = True
        logger.debug(f"Creating new '{CONFIG_FILENAME}'.")

    if should_write:
        try:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write(CONFIG_TEMPLATE)
            
            log_msg = f"Successfully created '{CONFIG_FILENAME}'."
            if file_existed: # This means it was an overwrite
                log_msg = f"Successfully overwrote '{CONFIG_FILENAME}'."
            log_success(logger, log_msg)
            
        except IOError as e:
            logger.error(f"❌ Failed to write file '{config_file_path}': {e}")
            return # Don't try to open if write failed
    
    # Open the file
    try:
        logger.info(f"Opening '{config_file_path.name}' in default editor...")
        success, output = run_command(
            ["open", str(config_file_path)], 
            logger, 
            description=f"Opening {CONFIG_FILENAME}"
        )
        if not success:
            logger.warning(f"⚠️ Could not automatically open file. Please open it manually.")
            logger.debug(f"Error opening file: {output}")
            
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred while trying to open the file: {e}")

def main():
    """Main orchestration function: Parses args, calls config processing, and runs the tree."""
    
    parser = argparse.ArgumentParser(description="A smart directory tree generator with support for a .treeconfig.ini file.")
    parser.add_argument("start_path", nargs='?', 
                        default=".", help="Starting path (file or directory).") 
    # --- MODIFIED: Use imported defaults ---
    parser.add_argument("-L", "--level", type=int, default=DEFAULT_MAX_LEVEL_ARG, help="Limit the display depth.")
    parser.add_argument("-I", "--ignore", type=str, help="Comma-separated list of patterns to ignore.")
    parser.add_argument("-P", "--prune", type=str, help="Comma-separated list of patterns to prune.")
    parser.add_argument("-d", "--dirs-only", nargs='?', const='_ALL_', default=DEFAULT_DIRS_ONLY_ARG, type=str, help="Show directories only.")
    parser.add_argument("-s", "--show-submodules", action='store_true', default=DEFAULT_SHOW_SUBMODULES_ARG, help="Show the contents of submodules.")
    # --- END MODIFIED ---
    parser.add_argument("--init", action='store_true', help="Create a sample .treeconfig.ini file and open it.")
    args = parser.parse_args()

    # 1. Setup Logging
    logger = setup_logging(script_name="CTree")
    logger.debug(f"Received start path: {args.start_path}")
    
    # 2. Handle --init flag (separated function)
    if args.init: 
        handle_init_command(logger)
        return # Exit after --init

    # 3. Process Start Path
    initial_path = Path(args.start_path).resolve() 
    if not initial_path.exists():
        logger.error(f"❌ Path does not exist: '{args.start_path}'")
        return
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)
    
    # 4. Load and Merge Configuration (Separated module)
    try:
        # --- MODIFIED: This function is now correctly imported from tree_core ---
        config_params = load_and_merge_config(args, start_dir, logger)
        # --- END MODIFIED ---
    except Exception as e:
        logger.error(f"❌ Critical error during config processing: {e}")
        logger.debug("Traceback:", exc_info=True)
        return

    # 5. Print Status Header
    is_truly_full_view = not any(config_params["filter_lists"].values())
    filter_info = "Full view" if is_truly_full_view else "Filtered view"
    
    level_info = "full depth" if config_params["max_level"] is None else \
                 f"depth limit: {config_params['max_level']}"
    mode_info = ", directories only" if config_params["global_dirs_only_flag"] else ""
    
    # --- MODIFIED: Thêm Git status vào header chỉ khi nó là Git repo ---
    git_info = ", Git project" if is_git_repo else ""
    
    print(f"{start_dir.name}/ [{filter_info}, {level_info}{mode_info}{git_info}]")
    # --- END MODIFIED ---

    # 6. Run Recursive Logic
    counters = {'dirs': 0, 'files': 0}
    
    # Use the processed config dict to pass parameters
    generate_tree(
        start_dir, 
        start_dir, 
        counters=counters,
        max_level=config_params["max_level"],
        ignore_list=config_params["ignore_list"],
        submodules=config_params["submodules"],
        prune_list=config_params["prune_list"],
        dirs_only_list=config_params["dirs_only_list"],
        is_in_dirs_only_zone=config_params["is_in_dirs_only_zone"]
    )

    # 7. Print Final Result
    files_info = "0 files (hidden)" if config_params["global_dirs_only_flag"] and counters['files'] == 0 else \
                 f"{counters['files']} files" 
    print(f"\n{counters['dirs']} directories, {files_info}")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Stop Command] Stop generating tree.")
        sys.exit(1)