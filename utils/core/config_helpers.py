# Path: utils/core/config_helpers.py

"""
Tiện ích logic để xử lý template và cấu trúc dữ liệu config.
(Internal module, imported by utils/core.py)
"""

import logging
from pathlib import Path
from typing import Dict, Any, Set, List, Optional

from .toml_io import load_toml_file, write_toml_file
# --- MODIFIED: Import hàm parser mới ---
from .parsing import parse_comma_list, parse_cli_set_operators
# --- END MODIFIED ---

__all__ = [
    "load_project_config_section",
    "load_and_merge_configs", 
    "merge_config_sections",
    "format_value_to_toml",
    "resolve_config_value",
    "resolve_config_list",
    "resolve_set_modification" # <-- NEW
]

# --- (Hàm format_value_to_toml giữ nguyên) ---
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

# --- (Hàm resolve_config_value giữ nguyên) ---
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

# --- MODIFIED: Cập nhật resolve_config_list để trả về List và giữ trật tự ---
def resolve_config_list(
    cli_str_value: Optional[str], 
    file_list_value: Optional[List[str]], # <-- Đây đã là List
    default_set_value: Set[str]
) -> List[str]: # <-- Trả về List
    """
    Xác định danh sách (list) config cuối cùng (cho ignore, prune, v.v.).
    Logic: (File Config GHI ĐÈ Mặc định) ĐƯỢC NỐI (append) với (CLI).
    Thứ tự được giữ nguyên.
    """
    
    # 1. Base list: Ưu tiên file config (giữ trật tự), nếu không có thì dùng default (sắp xếp).
    base_list: List[str]
    if file_list_value is not None:
        base_list = file_list_value
    else:
        base_list = sorted(list(default_set_value)) # Sắp xếp default cho nhất quán
        
    # 2. Lấy danh sách từ CLI (chuyển set thành list đã sắp xếp)
    cli_set = parse_comma_list(cli_str_value)
    cli_list = sorted(list(cli_set))
    
    # 3. Nối chúng lại: Base (File/Default) + CLI
    return base_list + cli_list
# --- END MODIFIED ---

# --- NEW: Hàm resolver set mới ---
def resolve_set_modification(
    tentative_set: Set[str], 
    cli_string: Optional[str]
) -> Set[str]:
    """
    Xử lý logic +/-/overwrite cho một set dựa trên chuỗi CLI.
    - "a,b" (Overwrite): Trả về {"a", "b"} (cộng thêm add_set, trừ đi subtract_set)
    - "+a,b" (Modify): Trả về tentative_set.union({"a", "b"})
    - "-a,b" (Modify): Trả về tentative_set.difference({"a", "b"})
    - "a,b+c,d-a" (Overwrite): Trả về {"b", "c", "d"}
    """
    if cli_string is None or cli_string == "":
        return tentative_set # Không thay đổi
    
    overwrite_set, add_set, subtract_set = parse_cli_set_operators(cli_string)
    
    base_set: Set[str]
    if overwrite_set:
        # Chế độ Ghi đè: Bắt đầu từ overwrite_set
        base_set = overwrite_set
    else:
        # Chế độ Chỉnh sửa: Bắt đầu từ tentative_set
        base_set = tentative_set
    
    # Áp dụng toán tử
    final_set = (base_set.union(add_set)).difference(subtract_set)
    
    return final_set
# --- END NEW ---


# --- (Các hàm load/merge config còn lại giữ nguyên) ---
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