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

__all__ = [
    "load_project_config_section",
    "load_and_merge_configs", # <-- MỚI
    "load_config_template",
    "merge_config_sections",
    "format_value_to_toml",
    "resolve_config_value",
    "resolve_config_list"
]

# --- (Các hàm format_value_to_toml, resolve_config_value, resolve_config_list giữ nguyên) ---
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
# --- (Hết các hàm giữ nguyên) ---


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

# --- NEW: Hàm helper tải config chung ---
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
    
    Ưu tiên: File cục bộ (.toolname.toml) sẽ ghi đè .project.toml.
    """
    project_config_path = start_dir / project_config_filename
    local_config_path = start_dir / local_config_filename

    # 1. Tải section từ .project.toml
    project_section = load_project_config_section(
        project_config_path, 
        config_section_name, 
        logger
    )
    
    # 2. Tải file .toolname.toml (file này là section [toolname])
    local_section = load_toml_file(local_config_path, logger)
    
    # (Xử lý trường hợp file .toolname.toml có thể chứa section [toolname])
    if config_section_name in local_section:
        local_section = local_section[config_section_name]
        
    # 3. Merge (local ghi đè project)
    return merge_config_sections(project_section, local_section)
# --- END NEW ---

def load_config_template(
    module_dir: Path,
    template_filename: str,
    logger: logging.Logger
) -> str:
    """
    Đọc nội dung thô của file template .toml từ thư mục module cụ thể.
    """
    try:
        template_path = module_dir / template_filename
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không tìm thấy template '{template_filename}' trong {module_dir.name}.")
        raise
    except Exception as e:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không thể đọc file template '{template_filename}': {e}")
        raise