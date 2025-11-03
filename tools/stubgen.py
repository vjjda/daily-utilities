# Path: tools/stubgen.py
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


try:
    from utils.logging_config import setup_logging, log_success

    from utils.cli import (
        ConfigInitializer,
    )

    from modules.stubgen import (
        MODULE_DIR,
        TEMPLATE_FILENAME,
        SGEN_DEFAULTS,
        PROJECT_CONFIG_FILENAME,
        CONFIG_FILENAME,
        CONFIG_SECTION_NAME,
        orchestrate_stubgen,
    )
except ImportError as e:

    print(f"Lỗi: Không thể import project utilities/modules: {e}", file=sys.stderr)
    sys.exit(1)


THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()


def main():

    parser = argparse.ArgumentParser(
        description="Tự động tạo file .pyi stub cho các module gateway động.",
        epilog="Ví dụ: sgen . -f",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    stubgen_group = parser.add_argument_group("Stub Generation Options")
    stubgen_group.add_argument(
        "target_paths",
        type=str,
        nargs="*",
        default=[],
        help="Đường dẫn (file hoặc thư mục) để quét. Mặc định là thư mục hiện tại (.).",
    )
    stubgen_group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Ghi đè file .pyi nếu đã tồn tại (không hỏi xác nhận).",
    )
    stubgen_group.add_argument(
        "-I",
        "--ignore",
        type=str,
        default=None,
        help="Danh sách pattern (giống .gitignore) để bỏ qua (THÊM vào config).",
    )

    stubgen_group.add_argument(
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

    logger = setup_logging(script_name="SGen")
    logger.debug("SGen script started.")

    config_initializer = ConfigInitializer(
        logger=logger,
        module_dir=MODULE_DIR,
        template_filename=TEMPLATE_FILENAME,
        config_filename=CONFIG_FILENAME,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
        base_defaults=SGEN_DEFAULTS,
    )
    config_initializer.check_and_handle_requests(args)

    try:

        orchestrate_stubgen(
            logger=logger,
            cli_args=args,
            this_script_path=THIS_SCRIPT_PATH,
        )

    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động tạo Stub đã bị dừng bởi người dùng.")
        sys.exit(1)
    except SystemExit as e:
        sys.exit(e.code)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":

    main()
