# Path: utils/core/config_io.py

"""
Tiện ích I/O cho file cấu hình (chủ yếu là TOML).
(Module nội bộ, được import bởi utils/core.py)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Set, Optional, Union

import typer # Cần cho confirm

# Import thư viện TOML
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

try:
    import tomli_w
except ImportError:
    tomli_w = None

from utils.logging_config import log_success

__all__ = [
    "load_project_config_section", # Đọc section từ .project.toml
    "load_config_template",
    "generate_dynamic_config",
    "overwrite_or_append_project_config_section",
    "write_config_file" # Hàm ghi file chung (dùng cho .tree.toml)
]

# --- Helpers ---

def _format_value_to_toml(value: Any) -> str:
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
        # Trong TOML, để thể hiện 'không có giá trị', ta comment nó ra
        # Hoặc yêu cầu người dùng bỏ comment nếu cần.
        # Ở đây ta trả về chuỗi rỗng để template có thể bỏ qua.
        return "" # Hoặc có thể là "# Bỏ comment để dùng: "
    else:
        # Kiểu không xác định, dùng repr() như một fallback
        return repr(value)

# --- Core Functions ---

def load_project_config_section(
    config_path: Path,
    section_name: str,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Tải file .project.toml và trả về dict của section_name cụ thể.
    Trả về dict rỗng nếu file/section không tồn tại hoặc lỗi.
    """
    if tomllib is None:
        logger.error("❌ Thiếu thư viện 'tomli' (cần cho Python < 3.11).")
        return {}

    config_data: Dict[str, Any] = {}
    if config_path.exists():
        try:
            with open(config_path, 'rb') as f:
                config_data = tomllib.load(f)
            logger.debug(f"Đã đọc file config dự án: {config_path.name}")
        except Exception as e:
            logger.warning(f"⚠️ Không thể đọc file config dự án {config_path.name}: {e}")
            return {} # Trả về rỗng nếu lỗi đọc file

    # Trả về section hoặc dict rỗng
    return config_data.get(section_name, {})


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
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không tìm thấy file template '{template_filename}' trong {module_dir.name}.")
        return f"# LỖI: File template {template_filename} bị thiếu."
    except Exception as e:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Không thể đọc file template '{template_filename}': {e}")
        return f"# LỖI: Không thể đọc file template {template_filename}."

def generate_dynamic_config(
    template_content: str,
    defaults_map: Dict[str, Any], # Dict chứa các giá trị default (VD: {"ignore": DEFAULT_IGNORE})
    logger: logging.Logger
) -> str:
    """
    Chèn các giá trị mặc định (đã định dạng TOML) vào chuỗi template.
    Tên key trong template phải khớp với key trong defaults_map (VD: {ignore}).
    """
    format_dict: Dict[str, str] = {}
    for key, value in defaults_map.items():
        # Tạo placeholder key cho template (VD: toml_ignore)
        # Bỏ qua nếu giá trị là None và không cần placeholder
        formatted_value = _format_value_to_toml(value)
        # Chỉ thêm vào dict nếu giá trị không rỗng hoặc là bool/int/float (số 0)
        if formatted_value or isinstance(value, (bool, int, float)):
             format_dict[f"toml_{key}"] = formatted_value
        elif key in template_content: # Nếu key có trong template nhưng giá trị là None/rỗng
             # Cung cấp giá trị comment mặc định
             format_dict[f"toml_{key}"] = f"# {key} = ..." # Hoặc để trống

    try:
        dynamic_template = template_content.format(**format_dict)
        return dynamic_template
    except KeyError as e:
        logger.error(f"❌ LỖI NGHIÊM TRỌNG: Template key không khớp: Thiếu key '{e}' trong defaults_map hoặc template.")
        return f"# LỖI: Template key '{e}' không khớp."
    except Exception as e:
         logger.error(f"❌ LỖI NGHIÊM TRỌNG: Lỗi khi format template: {e}")
         return "# LỖI: Không thể format template."


def overwrite_or_append_project_config_section(
    config_path: Path,
    config_section_name: str, # Tên section cần xử lý (VD: "tree", "cpath")
    new_section_content_str: str, # Nội dung TOML của section mới (không có header [section])
    logger: logging.Logger
) -> None:
    """
    Đọc file config_path (thường là .project.toml), ghi đè section
    [config_section_name] nếu tồn tại (và được xác nhận), hoặc nối thêm vào.
    """
    if tomllib is None or tomli_w is None:
        logger.error("❌ Thiếu thư viện 'tomli' (đọc) hoặc 'tomli-w' (ghi).")
        logger.error("   Chạy: pip install tomli tomli-w")
        raise typer.Exit(code=1)

    # 1. Đọc config hiện tại
    config_data: Dict[str, Any] = {}
    file_existed = config_path.exists()
    if file_existed:
        try:
            with open(config_path, 'rb') as f:
                config_data = tomllib.load(f)
            logger.debug(f"Đã đọc file config dự án: {config_path.name}")
        except Exception as e:
            logger.error(f"❌ Lỗi đọc file config dự án: {e}")
            raise typer.Exit(code=1)

    # 2. Phân tích nội dung section mới
    try:
        full_toml_string = f"[{config_section_name}]\n{new_section_content_str}"
        new_data = tomllib.loads(full_toml_string)
        new_section_dict = new_data.get(config_section_name, {})
        if not new_section_dict:
             raise ValueError("Nội dung section mới bị rỗng hoặc không hợp lệ.")
    except Exception as e:
        logger.error(f"❌ Lỗi nội bộ: Không thể parse nội dung section [{config_section_name}] mới: {e}")
        raise typer.Exit(code=1)

    # 3. Xử lý logic overwrite/append
    if config_section_name in config_data:
        logger.warning(f"⚠️ Section [{config_section_name}] đã tồn tại trong '{config_path.name}'.")
        try:
            # Dùng Typer để hỏi xác nhận
            should_overwrite = typer.confirm("   Ghi đè section hiện tại?", abort=True)
        except typer.Abort:
            logger.warning("Hoạt động bị hủy bởi người dùng.")
            raise typer.Exit(code=0) # Thoát nhẹ nhàng

        if not should_overwrite:
            logger.info("Section không bị ghi đè. Đang thoát.")
            raise typer.Exit(code=0)
        logger.debug(f"Đang ghi đè section [{config_section_name}]...")
    else:
        logger.debug(f"Đang thêm mới section [{config_section_name}]...")

    # 4. Thêm/Cập nhật section vào config data
    config_data[config_section_name] = new_section_dict

    # 5. Ghi config data trở lại file
    try:
        with open(config_path, 'wb') as f: # Dùng 'wb' cho tomli_w
            tomli_w.dump(config_data, f)

        log_msg = (
            f"✅ Đã tạo/cập nhật thành công '{config_path.name}' với section [{config_section_name}]."
        )
        log_success(logger, log_msg)

    except IOError as e:
        logger.error(f"❌ Lỗi khi ghi file config dự án '{config_path.name}': {e}")
        raise # Ném lại lỗi để entrypoint bắt

def write_config_file(
    config_path: Path,
    content: str,
    logger: logging.Logger,
    file_existed: bool # Dùng để tùy chỉnh thông báo log
) -> None:
    """
    Ghi nội dung chuỗi (thường là từ template đã render) vào một file.
    Hàm này dùng riêng cho việc tạo file config cục bộ (VD: .tree.toml).
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log_msg = (
            f"Đã tạo thành công '{config_path.name}'." if not file_existed
            else f"Đã ghi đè thành công '{config_path.name}'."
        )
        log_success(logger, log_msg)
    except IOError as e:
        logger.error(f"❌ Lỗi khi ghi file '{config_path.name}': {e}")
        raise