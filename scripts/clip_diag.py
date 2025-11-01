# Path: scripts/clip_diag.py
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Final


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
)


THIS_SCRIPT_PATH: Final[Path] = Path(__file__).resolve()


def main():

    parser = argparse.ArgumentParser(
        description="Xử lý code diagram (Graphviz/Mermaid) từ clipboard và tạo file.",
        epilog="Mặc định: Mở file nguồn. Sử dụng -t để tạo và mở file ảnh.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-t",
        "--to",
        default=DEFAULT_TO_ARG,
        choices=["svg", "png"],
        help="Convert source code to an image file (svg or png) and open it.",
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

    logger = setup_logging(script_name="CDiag")
    logger.debug("CDiag script started.")

    try:

        result = process_clipboard_content(
            logger=logger,
            filter_emoji=args.filter,
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
