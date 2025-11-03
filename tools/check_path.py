# Path: tools/check_path.py
import sys
import argparse
from pathlib import Path
from typing import List, Final


try:
    import argcomplete
except ImportError:
    argcomplete = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from utils.logging_config import setup_logging, log_success


from utils.cli import (
    ConfigInitializer,
)


from modules.check_path import (
    orchestrate_check_path,
    MODULE_DIR,
    TEMPLATE_FILENAME,
    CPATH_DEFAULTS,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    CONFIG_FILENAME,
)

THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()


def main():

    parser = argparse.ArgumentParser(
        description="Kiểm tra (và tùy chọn sửa) các comment '# Path:' trong file nguồn.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    path_check_group = parser.add_argument_group("Path Checking Options")
    path_check_group.add_argument(
        "start_paths_arg",
        type=str,
        nargs="*",
        default=[],
        help='Các đường dẫn (file hoặc thư mục) để quét (mặc định: ".").',
    )
    path_check_group.add_argument(
        "-r",
        "--root",
        type=str,
        default=None,
        help="Đường dẫn gốc (Project Root) tường minh để tính toán '# Path:'.\nMặc định: Tự động tìm gốc Git từ các đường dẫn đầu vào.",
    )

    path_check_group.add_argument(
        "-e",
        "--extensions",
        type=str,
        default=None,
        help="Các đuôi file. Hỗ trợ +/-/~.",
    )
    path_check_group.add_argument(
        "-I",
        "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern để bỏ qua (THÊM vào config/default).",
    )
    path_check_group.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Chỉ chạy ở chế độ 'dry-run' (kiểm tra). Mặc định là chạy 'fix'.",
    )
    path_check_group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Tự động sửa file mà không hỏi xác nhận.",
    )

    path_check_group.add_argument(
        "-g",
        "--git-commit",
        action="store_true",
        help="Tự động commit các thay đổi vào Git sau khi hoàn tất.",
    )

    config_group = parser.add_argument_group("Config Initialization (Chạy riêng lẻ)")

    config_group.add_argument(
        "-c",
        "--config-project",
        action="store_true",
        help=f"Khởi tạo/cập nhật section [{CONFIG_SECTION_NAME}] trong {PROJECT_CONFIG_FILENAME}.",
    )
    config_group.add_argument(
        "-C",
        "--config-local",
        action="store_true",
        help=f"Khởi tạo/cập nhật file {CONFIG_FILENAME} (scope 'local').",
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()
    logger = setup_logging(script_name="CPath")
    logger.debug("CPath script started.")

    config_initializer = ConfigInitializer(
        logger=logger,
        module_dir=MODULE_DIR,
        template_filename=TEMPLATE_FILENAME,
        config_filename=CONFIG_FILENAME,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
        base_defaults=CPATH_DEFAULTS,
    )
    config_initializer.check_and_handle_requests(args)

    try:

        orchestrate_check_path(
            logger=logger,
            cli_args=args,
            this_script_path=THIS_SCRIPT_PATH,
        )

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Đã dừng kiểm tra đường dẫn.")
        sys.exit(1)
