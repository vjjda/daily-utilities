# Path: modules/no_doc/no_doc_internal/__init__.pyi
"""Statically declared API for no_doc_internal"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

analyze_file_content: Any
load_config_files: Any
merge_ndoc_configs: Any
process_no_doc_task_dir: Any
process_no_doc_task_file: Any
scan_files: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "analyze_file_content",
    "load_config_files",
    "merge_ndoc_configs",
    "process_no_doc_task_dir",
    "process_no_doc_task_file",
    "scan_files",
]