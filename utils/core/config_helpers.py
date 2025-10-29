# Path: utils/core/config_helpers.py

import logging
from pathlib import Path
from typing import Dict, Any, Set, List, Optional
import tomlkit # Ensure tomlkit is imported

from .toml_io import load_toml_file, write_toml_file
from .parsing import parse_comma_list, parse_cli_set_operators

__all__ = [
    "load_project_config_section",
    "load_and_merge_configs",
    "merge_config_sections",
    "format_value_to_toml", # Exporting the revised function
    "resolve_config_value",
    "resolve_config_list",
    "resolve_set_modification"
]

# --- REVISED FORMATTER FUNCTION ---
def format_value_to_toml(value: Any) -> str:
    """
    Helper: Định dạng giá trị Python thành chuỗi TOML hợp lệ.
    Ưu tiên xử lý các kiểu phổ biến (str, bool, int, float, list/set)
    để đảm bảo cú pháp [] cho mảng.
    """
    if isinstance(value, bool):
        return str(value).lower() # true / false
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (str, Path)):
        # Use tomlkit to handle string quoting and escaping correctly
        return tomlkit.string(str(value)).as_string()
    elif isinstance(value, (list, set)):
        if not value:
            return "[]"
        # Format each item in the list/set recursively, then join
        # Ensure consistent sorting for sets
        items_to_format = sorted(list(value)) if isinstance(value, set) else value
        formatted_items = [format_value_to_toml(item) for item in items_to_format]
        # Check if all items are simple (int, float, bool) for inline array
        # Heuristic: Check if any item string contains quotes, brackets, or newlines
        is_simple = all(not any(c in s for c in ['"', '[', '{', '\n']) for s in formatted_items)

        if is_simple and len(formatted_items) < 5: # Arbitrary limit for inline
             return f"[{', '.join(formatted_items)}]"
        else:
             # Use multi-line array format for complex items or long lists
             indent = "    " # Or adjust as needed
             return "[\n" + ",\n".join(f"{indent}{item}" for item in formatted_items) + ",\n]"
             # Adding trailing comma for TOML v1.0.0 style arrays
             # Note: Tomlkit might handle this better, but this ensures basic validity

    elif value is None:
        # Handled by generator logic (comments out the line)
        return ""
    else:
        # Fallback for other types (like dicts, though unlikely in our defaults)
        try:
            # Let tomlkit attempt to format it
            return tomlkit.item(value).as_string()
        except Exception:
            # Last resort fallback
            return repr(value)
# --- END REVISED FORMATTER ---


# ... (rest of the functions: resolve_config_value, resolve_config_list, etc. remain the same) ...

def resolve_config_value(
    cli_value: Any,
    file_value: Any,
    default_value: Any
) -> Any:
    """ Determines the final config value for simple types. """
    if cli_value is not None: return cli_value
    if file_value is not None: return file_value
    return default_value

def resolve_config_list(
    cli_str_value: Optional[str],
    file_list_value: Optional[List[str]],
    default_set_value: Set[str]
) -> List[str]:
    """ Resolves the final list for ignore/prune patterns. """
    base_list: List[str]
    if file_list_value is not None:
        base_list = file_list_value
    else:
        base_list = sorted(list(default_set_value))
    cli_set = parse_comma_list(cli_str_value)
    cli_list = sorted(list(cli_set))
    return base_list + cli_list

def resolve_set_modification(
    tentative_set: Set[str],
    cli_string: Optional[str]
) -> Set[str]:
    """ Handles +/-/~ logic for sets based on CLI string. """
    if cli_string is None or cli_string == "": return tentative_set
    overwrite_set, add_set, subtract_set = parse_cli_set_operators(cli_string)
    base_set = overwrite_set if overwrite_set else tentative_set
    return (base_set.union(add_set)).difference(subtract_set)

def load_project_config_section(
    config_path: Path,
    section_name: str,
    logger: logging.Logger
) -> Dict[str, Any]:
    """ Loads a specific section from a TOML file. """
    config_data = load_toml_file(config_path, logger)
    return config_data.get(section_name, {})

def merge_config_sections(
    project_section: Dict[str, Any],
    local_section: Dict[str, Any]
) -> Dict[str, Any]:
    """ Merges two config dicts, prioritizing the local section. """
    return {**project_section, **local_section}

def load_and_merge_configs(
    start_dir: Path,
    logger: logging.Logger,
    project_config_filename: str,
    local_config_filename: str,
    config_section_name: str
) -> Dict[str, Any]:
    """ Loads and merges project and local config files for a specific section. """
    project_config_path = start_dir / project_config_filename
    local_config_path = start_dir / local_config_filename
    project_section = load_project_config_section(project_config_path, config_section_name, logger)
    local_config_data = load_toml_file(local_config_path, logger)
    local_section = local_config_data.get(config_section_name, {})
    return merge_config_sections(project_section, local_section)