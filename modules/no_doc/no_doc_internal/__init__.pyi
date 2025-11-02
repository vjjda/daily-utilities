# Path: modules/no_doc/no_doc_internal/__init__.pyi
"""Statically declared API for no_doc_internal"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

analyze_file_for_cleaning_and_formatting: Any
load_config_files: Any
merge_ndoc_configs: Any
print_dry_run_report_for_group: Any
process_no_doc_task_dir: Any
scan_files: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "analyze_file_for_cleaning_and_formatting",
    "load_config_files",
    "merge_ndoc_configs",
    "print_dry_run_report_for_group",
    "process_no_doc_task_dir",
    "scan_files",
]