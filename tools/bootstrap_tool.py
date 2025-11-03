# Path: tools/bootstrap_tool.py
import sys
import argparse
from pathlib import Path
from typing import Final


try:
    import argcomplete
except ImportError:
    argcomplete = None


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging

    from modules.bootstrap import (
        orchestrate_bootstrap,
    )

except ImportError as e:
    print(f"Lỗi: Không thể import utils hoặc gateway bootstrap: {e}", file=sys.stderr)
    sys.exit(1)


def main():

    logger = setup_logging(script_name="Btool", console_level_str="INFO")
    logger.debug("Script bootstrap bắt đầu.")

    parser = argparse.ArgumentParser(
        description="Bootstrap (khởi tạo) một tool utility mới từ file *.spec.toml."
    )
    parser.add_argument(
        "spec_file_path_str",
        type=str,
        help="Đường dẫn đầy đủ đến file *.spec.toml (ví dụ: docs/drafts/new_tool.spec.toml).",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Ghi đè (overwrite) các file và thư mục đã tồn tại nếu có.",
    )

    parser.add_argument(
        "-i",
        "--interface",
        type=str,
        choices=["typer", "argparse"],
        default=None,
        help="Ghi đè (overwrite) loại interface (typer/argparse) được định nghĩa trong file spec.",
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    try:

        orchestrate_bootstrap(logger=logger, cli_args=args, project_root=PROJECT_ROOT)

    except SystemExit:

        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn ở entrypoint: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
