# Path: modules/path_checker/path_checker_config_io.py

"""
Logic thực thi cho các hoạt động File Config trong module Path Checker (cpath).
(Xử lý việc ghi file .project.toml)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Set

import typer

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
from .path_checker_config import (
    PROJECT_CONFIG_FILENAME, CONFIG_SECTION_NAME,
    DEFAULT_EXTENSIONS_STRING, DEFAULT_IGNORE
)

__all__ = [
    "load_config_template",
    "generate_dynamic_config",
    "overwrite_or_append_project_config_section"
]

def _format_set_to_toml_array(value_set: Set[str]) -> str:
    """Helper: Chuyển set thành chuỗi mảng TOML."""
    if not value_set:
        return "[]"
    return repr(sorted(list(value_set)))

def load_config_template() -> str:
    """
    Đọc nội dung thô của file template .toml.
    """
    try:
        current_dir = Path(__file__).parent
        template_path = current_dir / "cpath.toml.template"
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("LỖI NGHIÊM TRỌNG: Không tìm thấy 'cpath.toml.template'.")
        return "# LỖI: File template bị thiếu."
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG: Không thể đọc 'cpath.toml.template': {e}")
        return "# LỖI: Không thể đọc file template."

def generate_dynamic_config(template_content: str) -> str:
    """
    Chèn các giá trị mặc định vào chuỗi template .toml.
    """
    try:
        # Chuẩn bị giá trị
        toml_extensions = repr(DEFAULT_EXTENSIONS_STRING)
        toml_ignore = _format_set_to_toml_array(DEFAULT_IGNORE)
        
        dynamic_template = template_content.format(
            toml_extensions=toml_extensions,
            toml_ignore=toml_ignore
        )
        return dynamic_template
    except KeyError as e:
        print(f"LỖI NGHIÊM TRỌNG: Template key không khớp: {e}")
        return "# LỖI: File template thiếu placeholder."

def overwrite_or_append_project_config_section(
    config_path: Path, 
    new_section_content_str: str, # Đây là string TOML (ví dụ: "key = val")
    logger: logging.Logger
) -> None:
    """
    Đọc file .project.toml, ghi đè section [cpath] nếu tồn tại 
    (và được xác nhận), hoặc nối thêm section [cpath] vào.
    (Logic mượn từ tree_config_io.py)
    """
    if tomllib is None or tomli_w is None:
        logger.error("❌ Thiếu thư viện 'tomli' (đọc) hoặc 'tomli-w' (ghi).")
        logger.error("   Chạy: pip install tomli tomli-w")
        raise typer.Exit(code=1)

    # 1. Đọc config hiện tại (nếu có)
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
    
    # 2. Phân tích nội dung section mới (từ template)
    try:
        full_toml_string = f"[{CONFIG_SECTION_NAME}]\n{new_section_content_str}"
        new_data = tomllib.loads(full_toml_string)
        new_section_dict = new_data.get(CONFIG_SECTION_NAME, {})
        
        if not new_section_dict:
             raise ValueError("Nội dung section mới bị rỗng.")
             
    except Exception as e:
        logger.error(f"❌ Lỗi nội bộ: Không thể parse nội dung section [cpath] mới: {e}")
        raise typer.Exit(code=1)

    # 3. Xử lý logic overwrite/append
    if CONFIG_SECTION_NAME in config_data:
        logger.warning(f"⚠️ Section [{CONFIG_SECTION_NAME}] đã tồn tại trong '{PROJECT_CONFIG_FILENAME}'.")
        try:
            should_overwrite = typer.confirm("   Ghi đè section hiện tại?", abort=True)
        except typer.Abort:
            logger.warning("Hoạt động bị hủy bởi người dùng.")
            raise typer.Exit(code=0)
            
        if not should_overwrite:
            logger.info("Section không bị ghi đè. Đang thoát.")
            raise typer.Exit(code=0)
        
        logger.debug(f"Đang ghi đè section [{CONFIG_SECTION_NAME}]...")
    else:
        logger.debug(f"Đang thêm mới section [{CONFIG_SECTION_NAME}]...")

    # 4. Thêm/Cập nhật section vào config data
    config_data[CONFIG_SECTION_NAME] = new_section_dict

    # 5. Ghi config data trở lại file (dùng 'wb' cho tomli_w)
    try:
        with open(config_path, 'wb') as f:
            tomli_w.dump(config_data, f)
            
        log_msg = (
            f"✅ Đã tạo thành công '{PROJECT_CONFIG_FILENAME}' với section [{CONFIG_SECTION_NAME}]." if not file_existed
            else f"✅ Đã cập nhật thành công '{PROJECT_CONFIG_FILENAME}'."
        )
        log_success(logger, log_msg)
        
    except IOError as e:
        logger.error(f"❌ Lỗi khi ghi file config dự án: {e}")
        raise