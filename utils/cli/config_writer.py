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

# Import các tiện ích cốt lõi
from utils.core import (
    # --- MODIFIED: Thay thế hàm load template ---
    load_text_template, # <-- MỚI (thay thế load_config_template)
    # --- END MODIFIED ---
    format_value_to_toml,
    load_toml_file,
    write_toml_file,
    load_project_config_section
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
    effective_defaults: Dict[str, Any] 
) -> str:
    """Tải và điền nội dung template .toml."""
    
    # --- MODIFIED: Sử dụng hàm load template chung ---
    template_path = module_dir / template_filename
    template_str = load_text_template(template_path, logger)
    # --- END MODIFIED ---
    
    # (Logic format giữ nguyên)
    # 1. Xử lý các giá trị đặc biệt (ví dụ: level của ctree)
    toml_level_str = ""
    if "level" in effective_defaults:
        level_val = effective_defaults["level"]
        toml_level_str = (
            f"level = {level_val}" 
            if level_val is not None 
            else f"# level = 3"
        )

    # 2. Format các giá trị còn lại
    format_dict: Dict[str, str] = {
        'config_section_name': config_section_name,
        'toml_level': toml_level_str, 
    }
    
    for key, value in effective_defaults.items():
        if key == "level":
            continue
        placeholder_key = f"toml_{key.replace('-', '_')}" 
        format_dict[placeholder_key] = format_value_to_toml(value)

    return template_str.format(**format_dict)


def handle_config_init_request(
    logger: logging.Logger,
    config_project: bool,
    config_local: bool,
    # Đường dẫn và tên file
    module_dir: Path,
    template_filename: str,
    config_filename: str, 
    project_config_filename: str, 
    config_section_name: str, 
    # Dữ liệu để điền
    base_defaults: Dict[str, Any] 
) -> bool:
    """
    Xử lý logic tạo config (-c / -C) cho các entrypoint.
    """
    
    # (Nội dung hàm này giữ nguyên, nó đã gọi _generate_template_content
    #  mà chúng ta vừa sửa ở trên)
    
    if not (config_project or config_local):
        return False 

    if tomllib is None:
         logger.error("❌ Thiếu thư viện 'tomli'/'tomli-w'. Vui lòng cài đặt: 'pip install tomli tomli-w'")
         raise ImportError("Missing tomli/tomli-w libraries")
         
    scope = 'project' if config_project else 'local'
    
    effective_defaults = base_defaults.copy() 
    
    if config_local:
        project_config_path = Path.cwd() / project_config_filename
        project_section = load_project_config_section(
            project_config_path, 
            config_section_name, 
            logger
        )
        if project_section:
            logger.debug(f"Sử dụng {project_config_filename} làm cơ sở cho template {config_filename}")
            effective_defaults.update(project_section)
        else:
            logger.debug(f"Không tìm thấy {project_config_filename}, dùng DEFAULT làm cơ sở cho {config_filename}")
    
    content_with_placeholders = _generate_template_content(
        logger,
        module_dir,
        template_filename,
        config_section_name,
        effective_defaults
    )

    should_write_result: Optional[bool] = True 
    config_file_path: Path

    if scope == "local":
        config_file_path = Path.cwd() / config_filename
        file_existed = config_file_path.exists()
        
        if file_existed:
            should_write_result = prompt_config_overwrite(
                logger, 
                config_file_path, 
                f"File '{config_filename}'"
            )
        
        if should_write_result is None:
            return True 

        if should_write_result:
            config_file_path.write_text(content_with_placeholders, encoding="utf-8")
            log_msg = (
                f"Đã tạo thành công '{config_file_path.name}'." if not file_existed
                else f"Đã ghi đè thành công '{config_file_path.name}'."
            )
            log_success(logger, log_msg) 

    elif scope == "project":
        config_file_path = Path.cwd() / project_config_filename
        
        start_marker = f"[{config_section_name}]"
        start_index = content_with_placeholders.find(start_marker)
        if start_index == -1: 
            raise ValueError(f"Template '{template_filename}' thiếu header section '{start_marker}'.")
            
        content_section_only = content_with_placeholders[start_index + len(start_marker):].strip()
        full_toml_string = f"[{config_section_name}]\n{content_section_only}"
        new_section_dict = tomllib.loads(full_toml_string).get(config_section_name, {})
        
        if not new_section_dict:
                raise ValueError("Nội dung section mới bị rỗng sau khi parse.")

        config_data = load_toml_file(config_file_path, logger)
        
        if config_section_name in config_data:
            should_write_result = prompt_config_overwrite(
                logger,
                config_file_path,
                f"Section [{config_section_name}]"
            )
        
        if should_write_result is None:
            return True 

        if should_write_result:
            config_data[config_section_name] = new_section_dict
            if not write_toml_file(config_file_path, config_data, logger):
                raise IOError(f"Không thể ghi file TOML: {config_file_path.name}")
            log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.")

    launch_editor(logger, config_file_path)
    
    return True