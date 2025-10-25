# Path: scripts/tree.py

import sys
import argparse 
import logging
from pathlib import Path
from typing import Optional, Set # (Giữ lại Set để type hint)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
# --- END BOOTSTRAPPING ---

import typer

# Common utilities
from utils.logging_config import setup_logging, log_success
from utils.core import run_command, is_git_repository

# Module Imports
# --- MODIFIED: Import API đã refactor ---
from modules.tree import (
    # --- Configs & Constants ---
    CONFIG_FILENAME,
    PROJECT_CONFIG_FILENAME, # <--- NEW
    
    # --- Loader Functions ---
    load_config_files,
    load_config_template,
    
    # --- Core Functions ---
    merge_config_sources,
    generate_dynamic_config,
    
    # --- Executor Functions ---
    generate_tree,
    print_status_header,
    print_final_result,

    # --- Config I/O Functions ---
    write_config_file,
    overwrite_or_append_project_config_section
)
# --- END MODIFIED ---

# Khởi tạo Typer App
app = typer.Typer(
    help="A smart directory tree generator with support for a .treeconfig.ini file.",
    add_completion=False,
    context_settings={"help_option_names": ["--help", "-h"]}
)

# Command 'init' (Đã refactor)
@app.command(
    name="init",
    help="Create a sample .tree.ini file or initialize .project.ini." # <--- SỬA HELP
)
def init_command(
    scope: str = typer.Option(
        "local", 
        "-s", "--scope", # Thay đổi thành Option với short flag
        help="Scope: 'local' (creates .tree.ini) or 'project' (initializes .project.ini).",
        case_sensitive=False
    )
):
    """
    Handles the 'init' command by calling module functions.
    """
    
    # 1. Setup Logging
    logger = setup_logging(script_name="CTree")
    
    if scope.lower() == "local":
        config_file_path = Path.cwd() / CONFIG_FILENAME # .tree.ini
        file_existed = config_file_path.exists()
        
        # ... (Phần logic local không đổi) ...
        should_write = False
        if file_existed:
            try:
                should_write = typer.confirm(f"'{CONFIG_FILENAME}' already exists. Overwrite?", abort=True)
                logger.debug(f"User chose to overwrite '{CONFIG_FILENAME}'.")
            except typer.Abort:
                logger.warning("Operation cancelled by user.")
                raise typer.Exit(code=0)
        else:
            should_write = True
            logger.debug(f"Creating new '{CONFIG_FILENAME}'.")
            
        if should_write:
            try:
                template_str = load_config_template()
                content = generate_dynamic_config(template_str)
                write_config_file(config_file_path, content, logger, file_existed)
            except (IOError, KeyError) as e:
                logger.error(f"❌ An error occurred during file creation: {e}")
                raise typer.Exit(code=1)
                
    elif scope.lower() == "project":
        config_file_path = Path.cwd() / PROJECT_CONFIG_FILENAME # .project.ini
        
        try:
            template_str = load_config_template()
            content_with_placeholders = generate_dynamic_config(template_str)
            start_index = content_with_placeholders.find(f"[{CONFIG_SECTION_NAME}]") + len(f"[{CONFIG_SECTION_NAME}]")
            content_section_only = content_with_placeholders[start_index:].strip()
            
            overwrite_or_append_project_config_section(
                config_file_path, 
                content_section_only, 
                logger
            )
            
        except (IOError, KeyError) as e:
            logger.error(f"❌ An error occurred during file operation: {e}")
            raise typer.Exit(code=1)
            
    else:
        logger.error(f"❌ Invalid scope argument: '{scope}'. Must be 'local' or 'project'.")
        raise typer.Exit(code=1)


    # 5. Mở file (Áp dụng cho cả local và project)
    try:
        logger.info(f"Opening '{config_file_path.name}' in default editor...")
        typer.launch(str(config_file_path))
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred while trying to open the file: {e}")
        logger.warning(f"⚠️ Could not automatically open file. Please open it manually.")

# Command chính (mặc định) (Đã refactor)
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    start_path_arg: Path = typer.Argument( 
        Path("."), 
        help="Starting path (file or directory). Use '~' for home directory.",
    ),
    level: Optional[int] = typer.Option( None, "-L", "--level", help="Limit the display depth.", min=1 ),
    ignore: Optional[str] = typer.Option( None, "-I", "--ignore", help="Comma-separated list of patterns to ignore." ),
    prune: Optional[str] = typer.Option( None, "-P", "--prune", help="Comma-separated list of patterns to prune." ),
    all_dirs: bool = typer.Option( False, "-d", "--dirs-only", help="Show directories only for the entire tree." ),
    dirs_patterns: Optional[str] = typer.Option( None, "--dirs-patterns", help="Show sub-directories only for specific patterns (e.g., 'assets')." ),
    show_submodules: bool = typer.Option( False, "-s", "--show-submodules", help="Show the contents of submodules." ),
    no_gitignore: bool = typer.Option( False, "--no-gitignore", help="Do not respect .gitignore files." ),
    full_view: bool = typer.Option( False, "-f", "--full-view", help="Bypass all filters (.gitignore, rules, level) and show all files." )
):
    """ Main orchestration function: Parses args, calls config processing, and runs the tree. """
    if ctx.invoked_subcommand: return

    # --- 1. Xử lý xung đột 'init' (Giữ nguyên) ---
    if str(start_path_arg) == "init":
        init_command()
        return 

    # --- 2. Setup & Validate ---
    logger = setup_logging(script_name="CTree")
    start_path = start_path_arg.expanduser()
    
    if not start_path.exists():
        logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại (sau khi expanduser): {start_path}")
        raise typer.Exit(code=1)

    logger.debug(f"Received start path: {start_path}")
    
    # --- 3. Build 'args' object (Giữ nguyên) ---
    cli_dirs_only = "_ALL_" if all_dirs else dirs_patterns
    args = argparse.Namespace(
        level=level, ignore=ignore, prune=prune, dirs_only=cli_dirs_only,
        show_submodules=show_submodules, no_gitignore=no_gitignore, full_view=full_view,
        init=False, start_path=str(start_path) 
    )

    # --- 4. Process Path & Git ---
    initial_path: Path = start_path
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)
    
    # --- 5. Orchestrate Module Calls ---
    try: 
        # 5.1 Load (từ loader)
        file_config = load_config_files(start_dir, logger)
        
        # 5.2 Process (từ core)
        config_params = merge_config_sources(
            args=args, 
            file_config=file_config,
            start_dir=start_dir, 
            logger=logger, 
            is_git_repo=is_git_repo
        )
        
        # 5.3 Execute (từ executor)
        print_status_header(
            config_params=config_params, 
            start_dir=start_dir, 
            is_git_repo=is_git_repo,
            cli_no_gitignore=args.no_gitignore
        )

        counters = {'dirs': 0, 'files': 0}
        generate_tree(
            start_dir, start_dir, counters=counters, 
            max_level=config_params["max_level"],
            ignore_list=config_params["ignore_list"], 
            submodules=config_params["submodules"],
            prune_list=config_params["prune_list"], 
            gitignore_spec=config_params["gitignore_spec"],
            dirs_only_list=config_params["dirs_only_list"], 
            is_in_dirs_only_zone=config_params["is_in_dirs_only_zone"]
        )

        print_final_result(
            counters=counters, 
            global_dirs_only=config_params["global_dirs_only_flag"]
        )
        
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise typer.Exit(code=1)

    
if __name__ == "__main__":
    try: app()
    except KeyboardInterrupt: print("\n\n❌ [Stop Command] Stop generating tree."); sys.exit(1)