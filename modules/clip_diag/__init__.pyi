# Path: modules/clip_diag/__init__.pyi
"""Statically declared API for clip_diag"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

APP_CONFIG: Any
DEFAULT_OUTPUT_DIR: Any
DEFAULT_TO_ARG: Any
DOT_PATH: Any
GRAPHVIZ_PREFIX: Any
MERMAID_PREFIX: Any
MMC_PATH: Any
detect_diagram_type: Any
execute_diagram_generation: Any
filter_emoji: Any
process_clipboard_content: Any
trim_leading_whitespace: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "APP_CONFIG",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_TO_ARG",
    "DOT_PATH",
    "GRAPHVIZ_PREFIX",
    "MERMAID_PREFIX",
    "MMC_PATH",
    "detect_diagram_type",
    "execute_diagram_generation",
    "filter_emoji",
    "process_clipboard_content",
    "trim_leading_whitespace",
]