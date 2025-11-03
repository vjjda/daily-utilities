# Path: tools/tree.py
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


try:
    import argcomplete
except ImportError:
    argcomplete = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))


from utils.logging_config import setup_logging, log_success
from utils.cli import ConfigInitializer

from modules.tree import (
    CONFIG_FILENAME,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    MODULE_DIR,
    TEMPLATE_FILENAME,
    TREE_DEFAULTS,
    orchestrate_tree,
)


def main():

    parser = argparse.ArgumentParser(
        description="Một công cụ tạo cây thư mục thông minh hỗ trợ file cấu hình .tree.toml (Phiên bản Argparse).",
        epilog="Ví dụ: tree . -L 3 -I '*.log' -e 'py,md'",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    tree_group = parser.add_argument_group("Tree Generation Options")
    tree_group.add_argument(
        "start_path",
        nargs="?",
        default=".",
        help="Đường dẫn bắt đầu (file hoặc thư mục). Mặc định là thư mục hiện tại (.).",
    )
    tree_group.add_argument("-L", "--level", type=int, help="Giới hạn độ sâu hiển thị.")

    tree_group.add_argument(
        "-e",
        "--extensions",
        type=str,
        default=None,
        help="Danh sách đuôi file (phân cách bởi dấu phẩy) để hiển thị. Hỗ trợ + (thêm) hoặc ~ (bớt). Ví dụ: 'py,js', '+md', '~log'",
    )

    tree_group.add_argument(
        "-I",
        "--ignore",
        help="Danh sách pattern (phân cách bởi dấu phẩy) để bỏ qua. Sẽ được **THÊM** vào danh sách từ config/default.",
    )
    tree_group.add_argument(
        "-P",
        "--prune",
        help="Danh sách pattern (phân cách bởi dấu phẩy) để cắt tỉa (prune). Sẽ được **THÊM** vào danh sách từ config/default.",
    )

    dirs_only_group = tree_group.add_mutually_exclusive_group()
    dirs_only_group.add_argument(
        "-d",
        "--all-dirs",
        action="store_true",
        help="Chỉ hiển thị thư mục cho toàn bộ cây.",
    )
    dirs_only_group.add_argument(
        "-D",
        "--dirs-patterns",
        help="Chỉ hiển thị thư mục con cho các pattern cụ thể (ví dụ: 'assets').",
    )

    tree_group.add_argument(
        "-s",
        "--show-submodules",
        action="store_true",
        help="Hiển thị nội dung của các submodule.",
    )
    tree_group.add_argument(
        "-N",
        "--no-gitignore",
        action="store_true",
        help="Không tôn trọng file .gitignore.",
    )
    tree_group.add_argument(
        "-f",
        "--full-view",
        action="store_true",
        help="Bỏ qua tất cả bộ lọc (.gitignore, rules, level) và hiển thị tất cả.",
    )

    config_group = parser.add_argument_group("Config Initialization (Chạy riêng lẻ)")
    config_group.add_argument(
        "-c",
        "--config-project",
        action="store_true",
        help="Khởi tạo/cập nhật file .project.toml (scope 'project').",
    )
    config_group.add_argument(
        "-C",
        "--config-local",
        action="store_true",
        help="Khởi tạo/cập nhật file .tree.toml (scope 'local').",
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    logger = setup_logging(script_name="Tree")
    logger.debug("Tree script (argparse) started.")

    config_initializer = ConfigInitializer(
        logger=logger,
        module_dir=MODULE_DIR,
        template_filename=TEMPLATE_FILENAME,
        config_filename=CONFIG_FILENAME,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
        base_defaults=TREE_DEFAULTS,
    )
    config_initializer.check_and_handle_requests(args)

    try:

        orchestrate_tree(logger=logger, cli_args=args)

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
