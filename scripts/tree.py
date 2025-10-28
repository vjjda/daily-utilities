# Path: scripts/tree.py

"""
Phiên bản Argparse của ctree (aptree).
Mô phỏng 1:1 chức năng của scripts/tree.py
"""

import sys
import argparse
import logging
from pathlib import Path
# --- MODIFIED: Thêm Set ---
from typing import Optional, Set, Dict, Any
# --- END MODIFIED ---

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

# Common utilities
from utils.logging_config import setup_logging, log_success
from utils.core import (
    is_git_repository
)
from utils.cli import handle_config_init_request

# Module Imports (Tái sử dụng 100% logic của tree)
from modules.tree import (
    CONFIG_FILENAME,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    # --- MODIFIED: Import DEFAULT_EXTENSIONS ---
    DEFAULT_MAX_LEVEL, FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE,
    DEFAULT_EXTENSIONS,
    # --- END MODIFIED ---

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
    "dirs-only": DEFAULT_DIRS_ONLY_LOGIC,
    "extensions": DEFAULT_EXTENSIONS # <-- NEW
}


def main():
    """ Hàm điều phối chính (phiên bản Argparse) """

    # --- 1. Định nghĩa Argparse ---
    parser = argparse.ArgumentParser(
        description="Một công cụ tạo cây thư mục thông minh hỗ trợ file cấu hình .tree.toml (Phiên bản Argparse).",
        epilog="Ví dụ: tree . -L 3 -I '*.log' -e 'py,md'", # <-- Sửa ví dụ
        formatter_class=argparse.RawTextHelpFormatter
    )
    tree_group = parser.add_argument_group("Tree Generation Options")
    tree_group.add_argument(
        "start_path",
        nargs="?",
        default=".",
        help="Đường dẫn bắt đầu (file hoặc thư mục). Mặc định là thư mục hiện tại (.)."
    )
    tree_group.add_argument("-L", "--level", type=int, help="Giới hạn độ sâu hiển thị.")

    # --- NEW: Thêm cờ -e/--extensions ---
    tree_group.add_argument(
        "-e", "--extensions",
        type=str,
        default=None,
        help="Danh sách đuôi file (phân cách bởi dấu phẩy) để hiển thị. Hỗ trợ + (thêm) hoặc ~ (bớt). Ví dụ: 'py,js', '+md', '~log'"
    )
    # --- END NEW ---

    # --- MODIFIED: Cập nhật help text cho -I ---
    tree_group.add_argument(
        "-I", "--ignore",
        help="Danh sách pattern (phân cách bởi dấu phẩy) để bỏ qua. Sẽ được **THÊM** vào danh sách từ config/default."
    )
    # --- END MODIFIED ---

    # --- MODIFIED: Cập nhật help text cho -P ---
    tree_group.add_argument(
        "-P", "--prune",
        help="Danh sách pattern (phân cách bởi dấu phẩy) để cắt tỉa (prune). Sẽ được **THÊM** vào danh sách từ config/default."
    )
    # --- END MODIFIED ---

    dirs_only_group = tree_group.add_mutually_exclusive_group()
    dirs_only_group.add_argument(
        "-d", "--all-dirs",
        action="store_true",
        help="Chỉ hiển thị thư mục cho toàn bộ cây."
    )

    # --- MODIFIED: Thêm cờ ngắn -D ---
    dirs_only_group.add_argument(
        "-D", "--dirs-patterns", # <-- Thêm -D
        help="Chỉ hiển thị thư mục con cho các pattern cụ thể (ví dụ: 'assets')."
    )
    # --- END MODIFIED ---

    tree_group.add_argument("-s", "--show-submodules", action="store_true", help="Hiển thị nội dung của các submodule.")

    # --- MODIFIED: Thêm cờ ngắn -N ---
    tree_group.add_argument(
        "-N", "--no-gitignore", # <-- Thêm -N
        action="store_true",
        help="Không tôn trọng file .gitignore."
    )
    # --- END MODIFIED ---

    tree_group.add_argument("-f", "--full-view", action="store_true", help="Bỏ qua tất cả bộ lọc (.gitignore, rules, level) và hiển thị tất cả.")
    config_group = parser.add_argument_group("Config Initialization (Chạy riêng lẻ)")
    config_group.add_argument(
        "-c", "--config-project",
        action="store_true",
        help="Khởi tạo/cập nhật file .project.toml (scope 'project')."
    )
    config_group.add_argument(
        "-C", "--config-local",
        action="store_true",
        help="Khởi tạo/cập nhật file .tree.toml (scope 'local')."
    )
    args = parser.parse_args()

    # --- 2. Setup Logging ---
    logger = setup_logging(script_name="APTree")
    logger.debug("APTree script (argparse) started.")

    # --- 3. Xử lý Config Init (Tái sử dụng 100%) ---
    try:
        config_action_taken = handle_config_init_request(
            logger=logger,
            config_project=args.config_project,
            config_local=args.config_local,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename=CONFIG_FILENAME,
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            base_defaults=TREE_DEFAULTS
        )
        if config_action_taken:
            sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # --- 4. Logic chạy ctree (Giống hệt Typer) ---
    start_path_obj = Path(args.start_path).expanduser()
    if not start_path_obj.exists():
        logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path_obj}")
        sys.exit(1)

    # --- MODIFIED: Lấy đúng tên arg mới ---
    cli_dirs_only = "_ALL_" if args.all_dirs else args.dirs_patterns # <-- Sửa tên biến
    # --- END MODIFIED ---

    cli_args = argparse.Namespace(
        level=args.level,
        extensions=args.extensions, # <-- NEW
        ignore=args.ignore,
        prune=args.prune,
        dirs_only=cli_dirs_only, # <-- Sửa tên biến
        show_submodules=args.show_submodules,
        no_gitignore=args.no_gitignore,
        full_view=args.full_view,
    )

    initial_path: Path = start_path_obj
    start_dir = initial_path.parent if initial_path.is_file() else initial_path
    is_git_repo = is_git_repository(start_dir)

    try:
        file_config = load_config_files(start_dir, logger)
        config_params = merge_config_sources(
            args=cli_args,
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

        # (Lệnh gọi generate_tree giữ nguyên sau lần refactor trước)
        generate_tree(
            start_dir, start_dir, counters=counters,
            max_level=config_params["max_level"],
            ignore_spec=config_params["ignore_spec"],
            submodules=config_params["submodules"],
            prune_spec=config_params["prune_spec"],
            dirs_only_spec=config_params["dirs_only_spec"],
            # --- NEW: Truyền extensions_filter ---
            extensions_filter=config_params["extensions_filter"],
            # --- END NEW ---
            is_in_dirs_only_zone=config_params["is_in_dirs_only_zone"]
        )

        print_final_result(
            counters=counters,
            global_dirs_only=config_params["global_dirs_only_flag"]
        )
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng tạo cây.");
        sys.exit(1)