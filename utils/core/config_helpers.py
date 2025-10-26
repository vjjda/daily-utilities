# Path: utils/core/config_helpers.py

"""
Tiện ích logic để xử lý template và cấu trúc dữ liệu config.
(Internal module, imported by utils/core.py)
"""

import logging
from pathlib import Path
# --- MODIFIED: Thêm Optional ---
from typing import Dict, Any, Set, List, Optional
# --- END MODIFIED ---

from .toml_io import load_toml_file 
# --- NEW: Import parse_comma_list ---
from .parsing import parse_comma_list
# --- END NEW ---

__all__ = [
    "load_project_config_section",
    "load_config_template",
    "merge_config_sections",
    "format_value_to_toml",
    "resolve_config_value",  # <-- NEW
    "resolve_config_list"    # <-- NEW
]

# --- ĐÃ ĐỔI TÊN: Bỏ dấu gạch dưới, export ra ngoài ---
def format_value_to_toml(value: Any) -> str:
    """Helper: Định dạng giá trị Python thành chuỗi TOML hợp lệ."""
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (set, list)):
        if not value:
            return "[]"
        # Dùng repr() cho list/set đã sort để đảm bảo đúng định dạng ['a', 'b']
        return repr(sorted(list(value)))
    elif isinstance(value, (str, Path)):
        # Dùng repr() để tự động thêm dấu ngoặc kép và escape ký tự đặc biệt
        return repr(str(value))
    elif isinstance(value, (int, float)):
        return str(value)
    elif value is None:
        # Trả về chuỗi rỗng để .format() bỏ qua nếu key không
        # tồn tại, hoặc trả về chuỗi comment nếu key tồn tại
        return "" 
    else:
        # Kiểu không xác định, dùng repr() như một fallback
        return repr(value)
# --- KẾT THÚC THAY ĐỔI ---

# --- NEW: Hàm helper cho giá trị đơn ---
def resolve_config_value(
    cli_value: Any, 
    file_value: Any, 
    default_value: Any
) -> Any:
    """
    Xác định giá trị config cuối cùng cho các_giá_trị_đơn.
    Ưu tiên: CLI > File Config > Mặc định.
    
    (Lưu ý: Giá trị 'None' từ CLI/File được coi là "không được đặt")
    """
    if cli_value is not None:
        return cli_value
    if file_value is not None:
        return file_value
    return default_value
# --- END NEW ---

# --- NEW: Hàm helper cho giá trị danh sách (với logic override mới) ---
def resolve_config_list(
    cli_str_value: Optional[str], 
    file_list_value: Optional[List[str]], 
    default_set_value: Set[str]
) -> Set[str]:
    """
    Xác định danh sách (set) config cuối cùng (cho ignore, prune, v.v.).
    Logic: (File Config GHI ĐÈ Mặc định) ĐƯỢC HỢP NHẤT (union) với (CLI).
    """
    
    # 1. Xác định tentative_set (File config GHI ĐÈ Mặc định)
    tentative_set: Set[str]
    if file_list_value is not None:
        # File config (.tree.toml / .project.toml) tồn tại
        tentative_set = set(file_list_value)
    else:
        # Dùng giá trị mặc định của script
        tentative_set = default_set_value
        
    # 2. Phân tích cờ CLI (luôn là union/thêm vào)
    cli_set = parse_comma_list(cli_str_value)
    
    # 3. Trả về kết quả hợp nhất
    return tentative_set.union(cli_set)
# --- END NEW ---


def load_project_config_section(
    config_path: Path,
    section_name: str,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải file .project.toml (dùng toml_io) và trích xuất một section.
    """
    # Dùng hàm I/O thuần túy
    config_data = load_toml_file(config_path, logger)
    # Trả về section hoặc dict rỗng
    return config_data.get(section_name, {})

def merge_config_sections(
    project_section: Dict[str, Any], 
    local_section: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Hợp nhất hai dict cấu hình, ưu tiên local_section.
    (Logic này được trích ra từ tree_loader.py)
    """
    return {**project_section, **local_section}

def load_config_template(
    module_dir: Path, # Thư mục chứa template (VD: modules/tree)
    template_filename: str, # Tên file template (VD: tree.toml.template)
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
        raise # Ném lỗi để entrypoint bắt
    except Exception as e:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không thể đọc file template '{template_filename}': {e}")
        raise # Ném lỗi để entrypoint bắt

# --- ĐÃ XÓA: generate_dynamic_config ---
# (Logic này giờ sẽ nằm trong scripts/tree.py)