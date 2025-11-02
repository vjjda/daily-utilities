# Path: modules/format_code/format_code_internal/__init__.pyi
"""Statically declared API for format_code_internal"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

analyze_file_content_for_formatting: Any
load_config_files: Any
merge_format_code_configs: Any
process_format_code_task_dir: Any
scan_files: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "analyze_file_content_for_formatting",
    "load_config_files",
    "merge_format_code_configs",
    "process_format_code_task_dir",
    "scan_files",
]