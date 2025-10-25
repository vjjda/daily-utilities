# Path: utils/core/config_helpers.py

"""
Tiện ích logic để xử lý template và cấu trúc dữ liệu config.
(Internal module, imported by utils/core.py)
"""

import logging
from pathlib import Path
from typing import Dict, Any, Set, List

from .toml_io import load_toml_file # Import từ module mới

__all__ = [
    "load_project_config_section",
    "load_config_template",
    "generate_dynamic_config",
    "merge_config_sections"
]

# (Hàm _format_value_to_toml giữ nguyên từ config_io.py cũ)
def _format_value_to_toml(value: Any) -> str:
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

# (Hàm load_config_template giữ nguyên từ config_io.py cũ)
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
        return f"# LỖI: File template {template_filename} bị thiếu."
    except Exception as e:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không thể đọc file template '{template_filename}': {e}")
        return f"# LỖI: Không thể đọc file template {template_filename}."

# (Hàm generate_dynamic_config giữ nguyên từ config_io.py cũ)
def generate_dynamic_config(
    template_content: str,
    defaults_map: Dict[str, Any], 
    logger: logging.Logger
) -> str:
    """
    Chèn các giá trị mặc định (đã định dạng TOML) vào chuỗi template.
    """
    format_dict: Dict[str, str] = {}
    for key, value in defaults_map.items():
        formatted_value = _format_value_to_toml(value)
        if formatted_value or isinstance(value, (bool, int, float)):
             format_dict[f"toml_{key}"] = formatted_value
        elif key in template_content: 
             format_dict[f"toml_{key}"] = f"# {key} = ..."

    try:
        dynamic_template = template_content.format(**format_dict)
        return dynamic_template
    except KeyError as e:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Template key không khớp: Thiếu key '{e}' trong defaults_map hoặc template.")
        return f"# LỖI: Template key '{e}' không khớp."
    except Exception as e:
         logger.error(f"❌ LỖI NGHIÊM TRỌNG: Lỗi khi format template: {e}")
         return "# LỖI: Không thể format template."