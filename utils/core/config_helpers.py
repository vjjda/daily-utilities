# Path: utils/core/config_helpers.py
import logging
from pathlib import Path
from typing import Dict, Any, Set, List, Optional
import tomlkit

from .toml_io import load_toml_file, write_toml_file
from .parsing import parse_comma_list, parse_cli_set_operators


logger = logging.getLogger(__name__)

__all__ = [
    "load_project_config_section",
    "load_and_merge_configs",
    "merge_config_sections",
    "format_value_to_toml",
    "resolve_config_value",
    "resolve_config_list",
    "resolve_set_modification",
]


def format_value_to_toml(value: Any) -> str:
    if isinstance(value, bool):

        return tomlkit.boolean(value).as_string()
    elif isinstance(value, (int, float)):

        return tomlkit.item(value).as_string()
    elif isinstance(value, (str, Path)):

        return tomlkit.string(str(value)).as_string()
    elif isinstance(value, (list, set)):
        if not value:
            return "[]"

        a = tomlkit.array()

        # Đây là logic đúng: chỉ sort set, giữ nguyên list
        items = sorted(list(value)) if isinstance(value, set) else value
        for item in items:

            try:
                a.append(tomlkit.item(item))
            except Exception:

                logger.warning(
                    f"Could not format item '{item}' of type {type(item)} within list for TOML. Using repr."
                )
                a.append(repr(item))

        return a.as_string()

    elif value is None:

        return ""
    else:

        try:

            return tomlkit.item(value).as_string()
        except Exception as e:
            logger.warning(
                f"Fallback TOML formatting failed for type {type(value)}: {e}. Using repr."
            )
            return repr(value)


def resolve_config_value(cli_value: Any, file_value: Any, default_value: Any) -> Any:
    if cli_value is not None:
        return cli_value
    if file_value is not None:
        return file_value
    return default_value


def resolve_config_list(
    cli_str_value: Optional[str],
    file_list_value: Optional[List[str]],
    default_set_value: Set[str],
) -> List[str]:
    base_list: List[str]
    if file_list_value is not None:
        base_list = file_list_value
    else:
        base_list = sorted(list(default_set_value))
    cli_set = parse_comma_list(cli_str_value)
    cli_list = sorted(list(cli_set))
    return base_list + cli_list


def resolve_set_modification(
    tentative_set: Set[str], cli_string: Optional[str]
) -> Set[str]:
    if cli_string is None or cli_string == "":
        return tentative_set
    overwrite_set, add_set, subtract_set = parse_cli_set_operators(cli_string)
    base_set = overwrite_set if overwrite_set else tentative_set
    return (base_set.union(add_set)).difference(subtract_set)


def load_project_config_section(
    config_path: Path, section_name: str, logger: logging.Logger
) -> Dict[str, Any]:
    config_data = load_toml_file(config_path, logger)
    return config_data.get(section_name, {})


def merge_config_sections(
    project_section: Dict[str, Any], local_section: Dict[str, Any]
) -> Dict[str, Any]:
    return {**project_section, **local_section}


def load_and_merge_configs(
    start_dir: Path,
    logger: logging.Logger,
    project_config_filename: str,
    local_config_filename: str,
    config_section_name: str,
) -> Dict[str, Any]:
    project_config_path = start_dir / project_config_filename
    local_config_path = start_dir / local_config_filename
    project_section = load_project_config_section(
        project_config_path, config_section_name, logger
    )
    local_config_data = load_toml_file(local_config_path, logger)
    local_section = local_config_data.get(config_section_name, {})
    return merge_config_sections(project_section, local_section)