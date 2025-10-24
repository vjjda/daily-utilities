# Path: scripts/tree.py

import sys
import argparse 
import logging
from pathlib import Path
from typing import Optional, Set

import typer

# Common utilities
from utils.logging_config import setup_logging, log_success
from utils.core import run_command, is_git_repository

# Module Imports
from modules.tree import (
    CONFIG_TEMPLATE, 
    load_and_merge_config,
    generate_tree,
    CONFIG_FILENAME,
    DEFAULT_IGNORE,
    DEFAULT_PRUNE,
    DEFAULT_DIRS_ONLY_LOGIC,
    FALLBACK_SHOW_SUBMODULES,
    DEFAULT_MAX_LEVEL,
    FALLBACK_USE_GITIGNORE,
    CONFIG_SECTION_NAME
)

# Khởi tạo Typer App
app = typer.Typer(
    help="A smart directory tree generator with support for a .treeconfig.ini file.",
    add_completion=False,
    context_settings={"help_option_names": ["--help", "-h"]}
)

# Command 'init' (Không thay đổi)
@app.command(
    name="init",
    help="Create a sample .tree.ini file and open it."
)
def init_command():
    """
    (Hàm này giữ nguyên toàn bộ logic tạo template động)
    """
    
    # 1. Setup Logging (sớm)
    logger = setup_logging(script_name="CTree")
    config_file_path = Path.cwd() / CONFIG_FILENAME
    file_existed = config_file_path.exists()
    should_write = False
    if file_existed:
        should_write = typer.confirm(f"'{CONFIG_FILENAME}' already exists. Overwrite?", abort=True)
        logger.debug(f"User chose to overwrite '{CONFIG_FILENAME}'.")
    else:
        should_write = True
        logger.debug(f"Creating new '{CONFIG_FILENAME}'.")
        
    # --- NEW: Helper function to format sets ---
    def _format_set_to_ini(value_set: Set[str]) -> str:
        """Helper to convert a set to a comma-separated INI string."""
        if not value_set:
            return "" # Trả về chuỗi rỗng nếu set rỗng
        return ", ".join(sorted(list(value_set)))
    # --- END NEW ---
    
    # --- NEW: Build dynamic template ---
    ini_level = (
        f"level = {DEFAULT_MAX_LEVEL}" 
        if DEFAULT_MAX_LEVEL is not None 
        else f"; level = "
    )
    ini_show_submodules = str(FALLBACK_SHOW_SUBMODULES).lower()
    ini_use_gitignore = str(FALLBACK_USE_GITIGNORE).lower()
    ini_ignore = _format_set_to_ini(DEFAULT_IGNORE)
    ini_prune = _format_set_to_ini(DEFAULT_PRUNE)
    ini_dirs_only = _format_set_to_ini(DEFAULT_DIRS_ONLY_LOGIC)

    try:
        dynamic_template = CONFIG_TEMPLATE.format(
            config_section_name=CONFIG_SECTION_NAME,
            ini_level=ini_level,
            ini_show_submodules=ini_show_submodules,
            ini_use_gitignore=ini_use_gitignore,
            ini_ignore=ini_ignore,
            ini_prune=ini_prune,
            ini_dirs_only=ini_dirs_only
        )
    except KeyError as e:
        logger.error(f"❌ Fatal Error: Template key mismatch: {e}")
        logger.error("   The 'modules/tree/tree.ini.template' file is missing a placeholder.")
        raise typer.Exit(code=1)
    # --- END NEW ---
        
    if should_write:
        try:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write(dynamic_template)
            log_msg = f"Successfully created '{CONFIG_FILENAME}'." if not file_existed else f"Successfully overwrote '{CONFIG_FILENAME}'."
            log_success(logger, log_msg)
        except IOError as e:
            logger.error(f"❌ Failed to write file '{config_file_path}': {e}")
            raise typer.Exit(code=1)
    try:
        logger.info(f"Opening '{config_file_path.name}' in default editor...")
        typer.launch(str(config_file_path))
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred while trying to open the file: {e}")
        logger.warning(f"⚠️ Could not automatically open file. Please open it manually.")


# Command chính (mặc định)
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

    # --- MODIFIED: Thêm logic kiểm tra xung đột 'init' LÊN ĐẦU ---
    # Đây là trường hợp Typer hiểu 'init' là 'start_path_arg'
    # thay vì là một lệnh con (do có default=Path('.'))
    if str(start_path_arg) == "init":
        # Gọi thẳng hàm 'init' để thực thi
        init_command()
        # Thoát hàm 'main' sau khi 'init' chạy xong
        return 
    # --- END MODIFIED ---

    # --- 1. Setup Logging (sớm) ---
    logger = setup_logging(script_name="CTree")
    
    # --- 2. Mở rộng `~` thủ công ---
    start_path = start_path_arg.expanduser()
    
    # --- 3. KIỂM TRA TỒN TẠI (thủ công) ---
    if not start_path.exists():
        # (Đã xóa khối 'if str(start_path_arg) == "init":'
        #  vì nó đã được xử lý ở trên)
            
        # Nếu không phải 'init', đây là lỗi thật
        logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại (sau khi expanduser): {start_path}")
        raise typer.Exit(code=1)
    # --- END ---

    logger.debug(f"Received start path: {start_path}")
    
    # 4. Xây dựng 'args' object giả lập
    # (Toàn bộ logic còn lại của hàm main giữ nguyên)
    cli_dirs_only = "_ALL_" if all_dirs else dirs_patterns
    args = argparse.Namespace(
        level=level, ignore=ignore, prune=prune, dirs_only=cli_dirs_only,
        show_submodules=show_submodules, no_gitignore=no_gitignore, full_view=full_view,
        init=False, start_path=str(start_path) 
    )

    # 5. Process Start Path
    initial_path: Path = start_path
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)
    
    # 6. Load and Merge Configuration
    try: config_params = load_and_merge_config(args, start_dir, logger, is_git_repo)
    except Exception as e:
        logger.error(f"❌ Critical error during config processing: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise typer.Exit(code=1)

    # 7. Print Status Header 
    is_truly_full_view = not any(config_params["filter_lists"].values()) and not config_params["using_gitignore"] and config_params["max_level"] is None
    filter_info = "Full view" if is_truly_full_view else "Filtered view"
    level_info = "full depth" if config_params["max_level"] is None else f"depth limit: {config_params['max_level']}"
    mode_info = ", directories only" if config_params["global_dirs_only_flag"] else ""
    git_info = ""
    if is_git_repo: git_info = ", Git project (.gitignore enabled)" if config_params["using_gitignore"] else (", Git project (.gitignore disabled by flag)" if args.no_gitignore else ", Git project")
    print(f"{start_dir.name}/ [{filter_info}, {level_info}{mode_info}{git_info}]")

    # 8. Run Recursive Logic 
    counters = {'dirs': 0, 'files': 0}
    generate_tree(
        start_dir, start_dir, counters=counters, max_level=config_params["max_level"],
        ignore_list=config_params["ignore_list"], submodules=config_params["submodules"],
        prune_list=config_params["prune_list"], gitignore_spec=config_params["gitignore_spec"],
        dirs_only_list=config_params["dirs_only_list"], is_in_dirs_only_zone=config_params["is_in_dirs_only_zone"]
    )

    # 9. Print Final Result 
    files_info = "0 files (hidden)" if config_params["global_dirs_only_flag"] and counters['files'] == 0 else f"{counters['files']} files" 
    print(f"\n{counters['dirs']} directories, {files_info}")
    
if __name__ == "__main__":
    try: app()
    except KeyboardInterrupt: print("\n\n❌ [Stop Command] Stop generating tree."); sys.exit(1)