# Path: scripts/tree.py

"""
Entrypoint (cổng vào) cho ctree (phiên bản Argparse).

Script này chịu trách nhiệm:
1. Thiết lập `sys.path` để import `utils` và `modules`.
2. Phân tích đối số dòng lệnh (Argparse).
3. Cấu hình logging.
4. Xử lý các yêu cầu khởi tạo config (`--config-local`, `--config-project`).
5. Gọi `process_tree_logic` (từ Core) để lấy các tham số đã hợp nhất.
6. Gọi các hàm `Executor` (`print_status_header`, `generate_tree`, `print_final_result`)
   để thực hiện side-effect (in ra console).
"""

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

# Thiết lập `sys.path` để import các module của dự án
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import các tiện ích chung
from utils.logging_config import setup_logging, log_success
from utils.cli import handle_config_init_request

# Import các thành phần của module 'tree'
from modules.tree import (
    CONFIG_FILENAME,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    DEFAULT_IGNORE, DEFAULT_PRUNE, DEFAULT_DIRS_ONLY_LOGIC,
    DEFAULT_MAX_LEVEL, FALLBACK_SHOW_SUBMODULES, FALLBACK_USE_GITIGNORE,
    DEFAULT_EXTENSIONS,

    # Các hàm chức năng SRP
    process_tree_logic,
    generate_tree,
    print_status_header,
    print_final_result,
)

# --- HẰNG SỐ CỤ THỂ CHO ENTRYPOINT ---

# Đường dẫn đến module 'tree' để tải template config
MODULE_DIR = PROJECT_ROOT / "modules" / "tree"
TEMPLATE_FILENAME = "tree.toml.template"

# Cấu hình mặc định để điền vào file template .toml khi khởi tạo
TREE_DEFAULTS: Dict[str, Any] = {
    "level": DEFAULT_MAX_LEVEL,
    "show-submodules": FALLBACK_SHOW_SUBMODULES,
    "use-gitignore": FALLBACK_USE_GITIGNORE,
    "ignore": DEFAULT_IGNORE,
    "prune": DEFAULT_PRUNE,
    "dirs-only": DEFAULT_DIRS_ONLY_LOGIC,
    "extensions": DEFAULT_EXTENSIONS
}


def main():
    """ Hàm điều phối chính (phiên bản Argparse) """

    # --- 1. Định nghĩa Argparse ---
    parser = argparse.ArgumentParser(
        description="Một công cụ tạo cây thư mục thông minh hỗ trợ file cấu hình .tree.toml (Phiên bản Argparse).",
        epilog="Ví dụ: tree . -L 3 -I '*.log' -e 'py,md'", 
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

    tree_group.add_argument(
         "-e", "--extensions",
        type=str,
        default=None,
        help="Danh sách đuôi file (phân cách bởi dấu phẩy) để hiển thị. Hỗ trợ + (thêm) hoặc ~ (bớt). Ví dụ: 'py,js', '+md', '~log'"
    )

    tree_group.add_argument(
        "-I", "--ignore",
        help="Danh sách pattern (phân cách bởi dấu phẩy) để bỏ qua. Sẽ được **THÊM** vào danh sách từ config/default."
    )
    tree_group.add_argument(
        "-P", "--prune",
        help="Danh sách pattern (phân cách bởi dấu phẩy) để cắt tỉa (prune). Sẽ được **THÊM** vào danh sách từ config/default."
    )

    dirs_only_group = tree_group.add_mutually_exclusive_group()
    dirs_only_group.add_argument(
        "-d", "--all-dirs",
        action="store_true",
        help="Chỉ hiển thị thư mục cho toàn bộ cây."
    )
    dirs_only_group.add_argument(
         "-D", "--dirs-patterns",
        help="Chỉ hiển thị thư mục con cho các pattern cụ thể (ví dụ: 'assets')."
    )

    tree_group.add_argument("-s", "--show-submodules", action="store_true", help="Hiển thị nội dung của các submodule.")
    tree_group.add_argument(
        "-N", "--no-gitignore", 
        action="store_true",
        help="Không tôn trọng file .gitignore."
    )
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
    logger = setup_logging(script_name="tree")
    logger.debug("Tree script (argparse) started.")

    # --- 3. Xử lý Config Init ---
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

    # --- 4. Logic chạy ctree ---
    start_path_obj = Path(args.start_path).expanduser()
    if not start_path_obj.exists():
        logger.error(f"❌ Lỗi: Đường dẫn bắt đầu không tồn tại: {start_path_obj}")
        sys.exit(1)

    try:
        # 1. Gọi Core Logic (truyền args thô)
        # Core sẽ chịu trách nhiệm tải config, hợp nhất, và trả về kết quả
        result_data = process_tree_logic(
            logger=logger,
            cli_args=args,
            start_path_obj=start_path_obj
        )
        
        if result_data is None:
            # Lỗi đã được log bên trong core
            sys.exit(1)
        
        # 2. Giải nén Result Object
        config_params = result_data["config_params"]
        start_dir = result_data["start_dir"]
        is_git_repo = result_data["is_git_repo"]
        cli_no_gitignore = result_data["cli_no_gitignore"]
        
        # 3. Gọi Executor (In kết quả ra console)
        print_status_header(
            config_params=config_params,
            start_dir=start_dir,
            is_git_repo=is_git_repo,
            cli_no_gitignore=cli_no_gitignore
        )
        
        counters = {'dirs': 0, 'files': 0}

        # Gọi hàm đệ quy chính
        generate_tree(
            start_dir, start_dir, counters=counters,
            max_level=config_params["max_level"],
            ignore_spec=config_params["ignore_spec"],
            submodules=config_params["submodules"],
            prune_spec=config_params["prune_spec"],
            dirs_only_spec=config_params["dirs_only_spec"],
            extensions_filter=config_params["extensions_filter"],
            is_in_dirs_only_zone=config_params["is_in_dirs_only_zone"]
        )

        # In tổng kết
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
        print("\n\n❌ [Lệnh dừng] Đã dừng tạo cây.")
        sys.exit(1)