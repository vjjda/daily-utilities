# Path: utils/cli/config_writer.py

"""
Tiện ích xử lý logic ghi file config (cho ctree, cpath).
(Internal module, imported by utils/cli)
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

import typer

# Import các tiện ích cốt lõi
from utils.core import (
    load_config_template, 
    format_value_to_toml,
    load_toml_file,
    write_toml_file
)
# Import các tiện ích UI
from .ui_helpers import prompt_config_overwrite, launch_editor
from utils.logging_config import log_success

__all__ = ["handle_config_init_request"]


def _generate_template_content(
    logger: logging.Logger,
    module_dir: Path,
    template_filename: str,
    config_section_name: str,
    default_values: Dict[str, Any]
) -> str:
    """Tải và điền nội dung template .toml."""
    
    template_str = load_config_template(module_dir, template_filename, logger)
    
    # 1. Xử lý các giá trị đặc biệt (ví dụ: level của ctree)
    toml_level_str = ""
    if "level" in default_values:
        level_val = default_values["level"]
        toml_level_str = (
            f"level = {level_val}" 
            if level_val is not None 
            else f"# level = 3"
        )

    # 2. Format các giá trị còn lại
    format_dict: Dict[str, str] = {
        'config_section_name': config_section_name,
        'toml_level': toml_level_str, # (An toàn nếu không có)
    }
    
    for key, value in default_values.items():
        
        # Bỏ qua 'level' vì nó đã được xử lý đặc biệt ở trên
        if key == "level":
            continue
            
        # --- SỬA LỖI: Chuyển key (ví dụ: 'show-submodules')
        # --- thành key placeholder (ví dụ: 'toml_show_submodules')
        
        # Chuyển 'show-submodules' -> 'toml_show_submodules'
        placeholder_key = f"toml_{key.replace('-', '_')}" 
        
        format_dict[placeholder_key] = format_value_to_toml(value)
        # --- KẾT THÚC SỬA LỖI ---

    return template_str.format(**format_dict)


def handle_config_init_request(
    logger: logging.Logger,
    config_project: bool,
    config_local: bool,
    # Đường dẫn và tên file
    module_dir: Path,
    template_filename: str,
    config_filename: str, # (ví dụ: .tree.toml)
    project_config_filename: str, # (ví dụ: .project.toml)
    config_section_name: str, # (ví dụ: tree)
    # Dữ liệu để điền
    default_values: Dict[str, Any]
) -> bool:
    """
    Xử lý logic tạo config (-c / -C) cho các entrypoint.
    ...
    """
    
    if not (config_project or config_local):
        return False # Không làm gì cả

    # 1. Kiểm tra thư viện
    if tomllib is None:
         logger.error("❌ Thiếu thư viện 'tomli'/'tomli-w'. Vui lòng cài đặt: 'pip install tomli tomli-w'")
         raise typer.Exit(code=1)
         
    scope = 'project' if config_project else 'local'
    
    try:
        # 2. Tạo nội dung file/section từ template
        content_with_placeholders = _generate_template_content(
            logger,
            module_dir,
            template_filename,
            config_section_name,
            default_values
        )

        should_write = True 
        config_file_path: Path

        # 3. Xử lý logic ghi file theo scope
        if scope == "local":
            config_file_path = Path.cwd() / config_filename
            file_existed = config_file_path.exists()
            
            if file_existed:
                should_write = prompt_config_overwrite(
                    logger, 
                    config_file_path, 
                    f"File '{config_filename}'"
                )
            
            if should_write:
                # Ghi file đầy đủ
                config_file_path.write_text(content_with_placeholders, encoding="utf-8")
                log_msg = (
                    f"Đã tạo thành công '{config_file_path.name}'." if not file_existed
                    else f"Đã ghi đè thành công '{config_file_path.name}'."
                )
                log_success(logger, log_msg) # <-- Lỗi Pylance đã được fix

        elif scope == "project":
            config_file_path = Path.cwd() / project_config_filename
            
            # Trích xuất nội dung section [xxx] từ template đã format
            start_marker = f"[{config_section_name}]"
            start_index = content_with_placeholders.find(start_marker)
            if start_index == -1: 
                raise ValueError(f"Template '{template_filename}' thiếu header section '{start_marker}'.")
                
            content_section_only = content_with_placeholders[start_index + len(start_marker):].strip()
            full_toml_string = f"[{config_section_name}]\n{content_section_only}"
            new_section_dict = tomllib.loads(full_toml_string).get(config_section_name, {})
            
            if not new_section_dict:
                    raise ValueError("Nội dung section mới bị rỗng sau khi parse.")

            # Tải, merge và ghi file .project.toml
            config_data = load_toml_file(config_file_path, logger)
            
            if config_section_name in config_data:
                should_write = prompt_config_overwrite(
                    logger,
                    config_file_path,
                    f"Section [{config_section_name}]"
                )
            
            if should_write:
                config_data[config_section_name] = new_section_dict
                if not write_toml_file(config_file_path, config_data, logger):
                    raise IOError(f"Không thể ghi file TOML: {config_file_path.name}")
                log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.") # <-- Lỗi Pylance đã được fix

    except (IOError, KeyError, ValueError) as e:
        logger.error(f"❌ Đã xảy ra lỗi khi thao tác file config: {e}")
        logger.debug("Traceback:", exc_info=True)
        raise typer.Exit(code=1)

    # 4. Mở editor
    launch_editor(logger, config_file_path)
    
    return True # Báo hiệu cho entrypoint biết để thoát