# Path: modules/clip_diag/clip_diag_config.py
import os
from pathlib import Path
from typing import Dict, Any, Optional, Final

__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "DOT_PATH",
    "MMC_PATH",
    "APP_CONFIG",
    "GRAPHVIZ_PREFIX",
    "MERMAID_PREFIX",
    "DEFAULT_TO_ARG",
]


DEFAULT_OUTPUT_DIR: Final[Path] = Path(os.path.expanduser("~/Documents/graphviz"))
DOT_PATH: Final[str] = "/opt/homebrew/bin/dot"
MMC_PATH: Final[str] = "/opt/homebrew/bin/mmc"
APP_CONFIG: Final[Dict[str, str]] = {
    "dot_app": "DotChart",
    "mermaid_app": "MarkChart",
    "svg_viewer_app": "Google Chrome",
    "png_viewer_app": "Preview",
}
GRAPHVIZ_PREFIX: Final[str] = "graphviz"
MERMAID_PREFIX: Final[str] = "mermaid"

DEFAULT_TO_ARG: Final[Optional[str]] = None
