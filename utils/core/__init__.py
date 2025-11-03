# Path: utils/core/__init__.py


from .code_cleaner import (
    clean_code,
    register_cleaner,
)


from .code_formatter import (
    format_code,
    register_formatter,
)


from .config_helpers import (
    load_project_config_section,
    load_and_merge_configs,
    merge_config_sections,
    format_value_to_toml,
    resolve_config_value,
    resolve_config_list,
    resolve_set_modification,
    generate_config_hash,
)


from .file_extensions import (
    is_extension_matched,
)


from .file_helpers import (
    load_text_template,
)


from .file_scanner import (
    scan_directory_recursive,
)


from .filter import (
    is_path_matched,
    compile_spec_from_patterns,
)


from .git import (
    is_git_repository,
    find_git_root,
    get_submodule_paths,
    parse_gitignore,
    git_add_and_commit,
    find_file_upwards,
    auto_commit_changes,
    find_commit_by_hash,
    get_diffed_files,
)


from .parsing import (
    parse_comma_list,
    parse_cli_set_operators,
)


from .platform_utils import (
    copy_file_to_clipboard,
)


from .process import (
    run_command,
)


from .toml_io import (
    load_toml_file,
    write_toml_file,
)


__all__ = [
    "clean_code",
    "register_cleaner",
    "format_code",
    "register_formatter",
    "load_project_config_section",
    "load_and_merge_configs",
    "merge_config_sections",
    "format_value_to_toml",
    "resolve_config_value",
    "resolve_config_list",
    "resolve_set_modification",
    "generate_config_hash",
    "is_extension_matched",
    "load_text_template",
    "scan_directory_recursive",
    "is_path_matched",
    "compile_spec_from_patterns",
    "is_git_repository",
    "find_git_root",
    "get_submodule_paths",
    "parse_gitignore",
    "git_add_and_commit",
    "find_file_upwards",
    "auto_commit_changes",
    "find_commit_by_hash",
    "get_diffed_files",
    "parse_comma_list",
    "parse_cli_set_operators",
    "copy_file_to_clipboard",
    "run_command",
    "load_toml_file",
    "write_toml_file",
]
