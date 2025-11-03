# Path: tools/clip_diag.py
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final
import pyperclip


try:
    import argcomplete
except ImportError:
    argcomplete = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))


from utils.logging_config import setup_logging


from modules.clip_diag import (
    process_clipboard_content,
    execute_diagram_generation,
    DEFAULT_TO_ARG,
    get_diagram_type_from_clipboard,
)


THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()


def main():

    parser = argparse.ArgumentParser(
        description="Xử lý code diagram (Graphviz/Mermaid) từ clipboard và tạo file.",
        epilog="Mặc định: Mở file nguồn. Sử dụng -t để tạo và mở file ảnh.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    output_group = parser.add_mutually_exclusive_group()

    output_group.add_argument(
        "-t",
        "--to",
        default=DEFAULT_TO_ARG,
        choices=["svg", "png"],
        help="Convert source code to an image file (svg or png) and open it.",
    )

    output_group.add_argument(
        "-g",
        "--is-graph",
        action="store_true",
        help="Chế độ kiểm tra: In ra 'Graphviz', 'Mermaid', hoặc 'False' và thoát.",
    )

    parser.add_argument(
        "-f",
        "--filter",
        action="store_true",
        help="Filter out emojis from the clipboard content before processing.",
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    if args.is_graph:
        try:

            dummy_logger = logging.getLogger("cdiag_silent")
            dummy_logger.setLevel(logging.CRITICAL + 1)

            result_str = get_diagram_type_from_clipboard(
                logger=dummy_logger, enable_filter_emoji=args.filter
            )
            print(result_str)

            sys.exit(0)

        except Exception:
            print("False")
            sys.exit(1)

    logger = setup_logging(script_name="CDiag")
    logger.debug("CDiag script started.")

    try:

        result = process_clipboard_content(
            logger=logger,
            enable_filter_emoji=args.filter,
        )

        if result:

            output_format: Optional[str] = args.to
            execute_diagram_generation(logger, result, output_format)

        else:

            pass

    except Exception as e:
        logger.error(f"❌ Đã xảy ra lỗi không mong muốn: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ [Lệnh dừng] Hoạt động của tool đã bị dừng bởi người dùng.")
        sys.exit(1)
