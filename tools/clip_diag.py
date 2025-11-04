# Path: tools/clip_diag.py
import sys
import argparse
import logging
from pathlib import Path
from typing import Final


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    import argcomplete
except ImportError:
    argcomplete = None

from utils.logging_config import setup_logging
from utils.cli import run_cli_app
from modules.clip_diag import (
    orchestrate_clip_diag,
)
from modules.clip_diag.clip_diag_config import DEFAULT_TO_ARG

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

    logger: logging.Logger
    if args.is_graph:
        logger = logging.getLogger("cdiag_silent")
        logger.setLevel(logging.CRITICAL + 1)
    else:
        logger = setup_logging(script_name="CDiag")
        logger.debug("CDiag script started.")

    run_cli_app(
        logger=logger,
        orchestrator_func=orchestrate_clip_diag,
        cli_args=args,
    )


if __name__ == "__main__":
    main()
