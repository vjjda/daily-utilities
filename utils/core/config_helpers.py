# Path: utils/core/config_helpers.py

import logging
from pathlib import Path
from typing import Dict, Any, Set, List, Optional
import tomlkit # Ensure tomlkit is imported

from .toml_io import load_toml_file, write_toml_file
from .parsing import parse_comma_list, parse_cli_set_operators

# Initialize logger for this module if needed for warnings
logger = logging.getLogger(__name__)

__all__ = [
    "load_project_config_section",
    "load_and_merge_configs",
    "merge_config_sections",
    "format_value_to_toml",
    "resolve_config_value",
    "resolve_config_list",
    "resolve_set_modification"
]

# --- REVISED FORMATTER FUNCTION (v3) ---
def format_value_to_toml(value: Any) -> str:
    """
    Helper: Formats a Python value into a valid TOML string representation.
    Uses tomlkit's builders where possible for correctness.
    """
    if isinstance(value, bool):
        # Use tomlkit boolean representation
        return tomlkit.boolean(value).as_string() # 'true' or 'false'
    elif isinstance(value, (int, float)):
        # Use tomlkit integer/float representation
        return tomlkit.item(value).as_string()
    elif isinstance(value, (str, Path)):
        # Use tomlkit string representation (handles quotes, escapes, multiline)
        return tomlkit.string(str(value)).as_string()
    elif isinstance(value, (list, set)):
        if not value:
            return "[]"
        # Create a tomlkit array
        a = tomlkit.array()
        # Ensure consistent sorting for sets before adding to array
        items = sorted(list(value)) if isinstance(value, set) else value
        for item in items:
            # Recursively format each item using tomlkit's item() factory
            # This ensures nested structures are also handled correctly
             try:
                 a.append(tomlkit.item(item))
             except Exception:
                 # Fallback if tomlkit cannot handle the item type within the list
                 logger.warning(f"Could not format item '{item}' of type {type(item)} within list for TOML. Using repr.")
                 a.append(repr(item)) # Use repr as a last resort inside list

        # Format the array as a string (tomlkit decides inline vs multiline)
        # Use as_string() for the final representation
        return a.as_string()

    elif value is None:
        # Should be handled by generator logic commenting out the line
        return "" # Return empty, generator comments it out
    else:
        # Fallback for truly unknown/complex types
        try:
            # Attempt using tomlkit.item directly
            return tomlkit.item(value).as_string()
        except Exception as e:
            logger.warning(f"Fallback TOML formatting failed for type {type(value)}: {e}. Using repr.")
            return repr(value) # Absolute last resort

# ... (rest of the file: resolve_config_value, resolve_config_list, etc. remain the same) ...
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