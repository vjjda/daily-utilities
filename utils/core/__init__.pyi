# Path: utils/core/__init__.pyi
"""Statically declared API for core"""

from typing import Any, List, Optional, Set, Dict, Union
from pathlib import Path

Logger: Any
auto_commit_changes: Any
clean_code: Any
compile_spec_from_patterns: Any
copy_file_to_clipboard: Any
find_commit_by_hash: Any
find_file_upwards: Any
find_git_root: Any
format_code: Any
format_value_to_toml: Any
generate_config_hash: Any
get_diffed_files: Any
get_submodule_paths: Any
git_add_and_commit: Any
is_git_repository: Any
is_path_matched: Any
load_and_merge_configs: Any
load_project_config_section: Any
load_text_template: Any
load_toml_file: Any
merge_config_sections: Any
parse_cli_set_operators: Any
parse_comma_list: Any
parse_gitignore: Any
register_cleaner: Any
register_formatter: Any
resolve_config_list: Any
resolve_config_value: Any
resolve_set_modification: Any
run_command: Any
write_toml_file: Any

# Static declaration of exported symbols (for Pylance)
__all__: List[str] = [
    "Logger",
    "auto_commit_changes",
    "clean_code",
    "compile_spec_from_patterns",
    "copy_file_to_clipboard",
    "find_commit_by_hash",
    "find_file_upwards",
    "find_git_root",
    "format_code",
    "format_value_to_toml",
    "generate_config_hash",
    "get_diffed_files",
    "get_submodule_paths",
    "git_add_and_commit",
    "is_git_repository",
    "is_path_matched",
    "load_and_merge_configs",
    "load_project_config_section",
    "load_text_template",
    "load_toml_file",
    "merge_config_sections",
    "parse_cli_set_operators",
    "parse_comma_list",
    "parse_gitignore",
    "register_cleaner",
    "register_formatter",
    "resolve_config_list",
    "resolve_config_value",
    "resolve_set_modification",
    "run_command",
    "write_toml_file",
]