# Path: tools/format_code.py
import sys
import argparse
from pathlib import Path
from typing import Final


try:
    import argcomplete
except ImportError:
    argcomplete = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging

    from utils.cli import (
        ConfigInitializer,
    )
    from modules.format_code import (
        orchestrate_format_code,
        DEFAULT_START_PATH,
        CONFIG_FILENAME,
        PROJECT_CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
        MODULE_DIR,
        TEMPLATE_FILENAME,
        FORC_DEFAULTS,
    )
except ImportError as e:
    print(f"Lỗi: Không thể import project utilities/modules: {e}", file=sys.stderr)
    sys.exit(1)


THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()


def main():

    parser = argparse.ArgumentParser(
        description="Công cụ quét và định dạng (format) file mã nguồn.",
        epilog="Mặc định: Chạy ở chế độ sửa lỗi tương tác. Dùng -d để chạy thử.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    pack_group = parser.add_argument_group("Tùy chọn Định dạng Code")
    pack_group.add_argument(
        "start_path_arg",
        type=str,
        nargs="*",
        default=[],
        help=f'Các đường dẫn (file hoặc thư mục) để quét. Mặc định: "{DEFAULT_START_PATH}".',
    )
    pack_group.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Chỉ chạy ở chế độ kiểm tra (dry-run) và báo cáo các file cần sửa, không thực hiện ghi file.",
    )
    pack_group.add_argument(
        "-e",
        "--extensions",
        type=str,
        default=None,
        help="Danh sách các đuôi file cần quét (phân cách bởi dấu phẩy). Hỗ trợ + (thêm) và ~ (bớt).",
    )
    pack_group.add_argument(
        "-I",
        "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern (giống .gitignore) để bỏ qua khi quét (THÊM vào config).",
    )
    pack_group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Ghi đè file mà không hỏi xác nhận (chỉ áp dụng ở chế độ fix).",
    )
    pack_group.add_argument(
        "-g",
        "--git-commit",
        action="store_true",
        help="Tự động commit các thay đổi vào Git sau khi hoàn tất.",
    )

    pack_group.add_argument(
        "-w",
        "--stepwise",
        action="store_true",
        help="Chế độ gia tăng. Chỉ quét các file đã thay đổi kể từ lần chạy cuối cùng có cùng cài đặt.",
    )

    config_group = parser.add_argument_group("Khởi tạo Cấu hình (chạy riêng)")
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

    logger = setup_logging(script_name="Forc")
    logger.debug("FormatCode script started.")

    config_initializer = ConfigInitializer(
        logger=logger,
        module_dir=MODULE_DIR,
        template_filename=TEMPLATE_FILENAME,
        config_filename=CONFIG_FILENAME,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
        base_defaults=FORC_DEFAULTS,
    )
    config_initializer.check_and_handle_requests(args)

    try:
        orchestrate_format_code(
            logger=logger,
            cli_args=args,
            project_root=PROJECT_ROOT,
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
        print("\n\n❌ [Lệnh dừng] Đã dừng định dạng Code.")
        sys.exit(1)
