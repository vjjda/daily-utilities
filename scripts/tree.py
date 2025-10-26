# Path: scripts/tree.py

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Set, Dict, Any

try:
    import tomllib 
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
# --- END BOOTSTRAPPING ---

import typer

# Common utilities
from utils.logging_config import setup_logging, log_success
# --- MODIFIED: Xóa load_project_config_section ---
from utils.core import (
    is_git_repository
)
# --- END MODIFIED ---
from utils.cli import handle_config_init_request

# Module Imports
from modules.tree import (
    CONFIG_FILENAME,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE,

    load_config_files, 

    merge_config_sources,

    generate_tree,
    print_status_header,
    print_final_result,
)

# --- CONSTANTS ---
MODULE_DIR = PROJECT_ROOT / "modules" / "tree"
TEMPLATE_FILENAME = "tree.toml.template" 
TREE_DEFAULTS: Dict[str, Any] = {
    "level": DEFAULT_MAX_LEVEL,
    "show-submodules": FALLBACK_SHOW_SUBMODULES,
    "use-gitignore": FALLBACK_USE_GITIGNORE,
    "ignore": DEFAULT_IGNORE,
    "prune": DEFAULT_PRUNE,
    "dirs-only": DEFAULT_DIRS_ONLY_LOGIC
}

# (Typer app giữ nguyên)
app = typer.Typer(
    help="Một công cụ tạo cây thư mục thông minh hỗ trợ file cấu hình .tree.toml.",
    add_completion=False,
    context_settings={"help_option_names": ["--help", "-h"]}
)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    
    # (Các cờ config_project và config_local giữ nguyên)
    config_project: bool = typer.Option(
        False, "-c", "--config-project",
        help="Khởi tạo/cập nhật file .project.toml (scope 'project').",
        show_default=False,
    ),
    config_local: bool = typer.Option(
        False, "-C", "--config-local", 
        help="Khởi tạo/cập nhật file .tree.toml (scope 'local').",
        show_default=False,
    ),
    
    # (Các tham số Typer khác giữ nguyên)
    start_path_arg: Path = typer.Argument(
        Path("."),
        help="Đường dẫn bắt đầu (file hoặc thư mục). Dùng '~' cho thư mục home.",
    ),
    level: Optional[int] = typer.Option( None, "-L", "--level", help="Giới hạn độ sâu hiển thị.", min=1 ),
    ignore: Optional[str] = typer.Option( None, "-I", "--ignore", help="Danh sách pattern (phân cách bởi dấu phẩy) để bỏ qua." ),
    prune: Optional[str] = typer.Option( None, "-P", "--prune", help="Danh sách pattern (phân cách bởi dấu phẩy) để cắt tỉa (prune)." ),
    all_dirs: bool = typer.Option( False, "-d", "--dirs-only", help="Chỉ hiển thị thư mục cho toàn bộ cây." ),
    dirs_patterns: Optional[str] = typer.Option( None, "--dirs-patterns", help="Chỉ hiển thị thư mục con cho các pattern cụ thể (ví dụ: 'assets')." ),
    show_submodules: bool = typer.Option( False, "-s", "--show-submodules", help="Hiển thị nội dung của các submodule." ),
    no_gitignore: bool = typer.Option( False, "--no-gitignore", help="Không tôn trọng file .gitignore." ),
    full_view: bool = typer.Option( False, "-f", "--full-view", help="Bỏ qua tất cả bộ lọc (.gitignore, rules, level) và hiển thị tất cả." )
):
    """ Hàm điều phối chính: Phân tích đối số, gọi xử lý config, và chạy tạo cây. """
    if ctx.invoked_subcommand: return

    # --- Logic khởi tạo Config (ĐÃ REFACTOR) ---
    logger = setup_logging(script_name="CTree")

    # --- MODIFIED: Đơn giản hóa logic gọi ---
    try:
        # Xóa logic tải .project_config_section ở đây
        
        config_action_taken = handle_config_init_request(
            logger=logger,
            config_project=config_project,
            config_local=config_local,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename=CONFIG_FILENAME,
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            base_defaults=TREE_DEFAULTS # <-- Chỉ cần truyền base defaults
        )
        
        if config_action_taken:
            raise typer.Exit(code=0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise typer.Exit(code=1)
    # --- END MODIFIED ---

    start_path = start_path_arg.expanduser()
    if not start_path.exists():
        logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path}")
        raise typer.Exit(code=1)
    
    # (Phần còn lại của file giữ nguyên)
    cli_dirs_only = "_ALL_" if all_dirs else dirs_patterns
    args = argparse.Namespace(
        level=level, ignore=ignore, prune=prune, dirs_only=cli_dirs_only,
        show_submodules=show_submodules, no_gitignore=no_gitignore, full_view=full_view,
        init=False, start_path=str(start_path)
    )

    initial_path: Path = start_path
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)

    try:
        file_config = load_config_files(start_dir, logger)
        config_params = merge_config_sources(
            args=args,
            file_config=file_config,
            start_dir=start_dir,
            logger=logger,
            is_git_repo=is_git_repo
        )
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
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    try: app()
    except KeyboardInterrupt: print("\n\n❌ [Lệnh dừng] Đã dừng tạo cây."); sys.exit(1)