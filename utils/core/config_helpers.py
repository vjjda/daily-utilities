# Path: utils/core/config_helpers.py

"""
Tiện ích logic để xử lý template và cấu trúc dữ liệu config.
(Internal module, imported by utils/core.py)
"""

import logging
from pathlib import Path
from typing import Dict, Any, Set, List, Optional

from .toml_io import load_toml_file, write_toml_file
from .parsing import parse_comma_list
# --- MODIFIED: Xóa import file helper cũ ---
# --- END MODIFIED ---

__all__ = [
    "load_project_config_section",
    "load_and_merge_configs", 
    # "load_config_template", # <-- ĐÃ XÓA
    "merge_config_sections",
    "format_value_to_toml",
    "resolve_config_value",
    "resolve_config_list"
]

# --- (Các hàm format_value_to_toml, resolve_config_value, resolve_config_list,
# ---  load_project_config_section, merge_config_sections, load_and_merge_configs
# ---  giữ nguyên) ---

def format_value_to_toml(value: Any) -> str:
    """Helper: Định dạng giá trị Python thành chuỗi TOML hợp lệ."""
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (set, list)):
        if not value:
            return "[]"
        return repr(sorted(list(value)))
    elif isinstance(value, (str, Path)):
        return repr(str(value))
    elif isinstance(value, (int, float)):
        return str(value)
    elif value is None:
        return "" 
    else:
        return repr(value)

def resolve_config_value(
    cli_value: Any, 
    file_value: Any, 
    default_value: Any
) -> Any:
    """
    Xác định giá trị config cuối cùng cho các_giá_trị_đơn.
    Ưu tiên: CLI > File Config > Mặc định.
    """
    if cli_value is not None:
        return cli_value
    if file_value is not None:
        return file_value
    return default_value

def resolve_config_list(
    cli_str_value: Optional[str], 
    file_list_value: Optional[List[str]], 
    default_set_value: Set[str]
) -> Set[str]:
    """
    Xác định danh sách (set) config cuối cùng (cho ignore, prune, v.v.).
    Logic: (File Config GHI ĐÈ Mặc định) ĐƯỢC HỢP NHẤT (union) với (CLI).
    """
    tentative_set: Set[str]
    if file_list_value is not None:
        tentative_set = set(file_list_value)
    else:
        tentative_set = default_set_value
        
    cli_set = parse_comma_list(cli_str_value)
    
    return tentative_set.union(cli_set)


def load_project_config_section(
    config_path: Path,
    section_name: str,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải file .project.toml (dùng toml_io) và trích xuất một section.
    """
    config_data = load_toml_file(config_path, logger)
    return config_data.get(section_name, {})

def merge_config_sections(
    project_section: Dict[str, Any], 
    local_section: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Hợp nhất hai dict cấu hình, ưu tiên local_section.
    """
    return {**project_section, **local_section}

def load_and_merge_configs(
    start_dir: Path, 
    logger: logging.Logger,
    project_config_filename: str,
    local_config_filename: str,
    config_section_name: str
) -> Dict[str, Any]:
    """
    Hàm chung để tải và hợp nhất cấu hình từ .project.toml và
    file .<toolname>.toml cục bộ.
    """
    project_config_path = start_dir / project_config_filename
    local_config_path = start_dir / local_config_filename

    project_section = load_project_config_section(
        project_config_path, 
        config_section_name, 
        logger
    )
    
    local_section = load_toml_file(local_config_path, logger)
    
    if config_section_name in local_section:
        local_section = local_section[config_section_name]
        
    return merge_config_sections(project_section, local_section)

# --- REMOVED: load_config_template ---
# (Hàm này đã được di chuyển và tổng quát hóa thành 
#  utils.core.file_helpers.load_text_template)
# --- END REMOVED ---