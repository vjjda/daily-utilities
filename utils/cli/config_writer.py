# Path: utils/cli/config_writer.py
"""
Tiện ích xử lý logic ghi file config cho các entrypoint CLI.
Sử dụng tomlkit để bảo toàn comment và định dạng khi cập nhật .project.toml.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import io

# Cố gắng import thư viện TOML
try:
    import tomllib  # Chỉ dùng để đọc nếu tomlkit lỗi (fallback hiếm)
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

try:
    import tomlkit # Thư viện chính để đọc/ghi bảo toàn định dạng
except ImportError:
    tomlkit = None

# Import các tiện ích cốt lõi
from utils.core import (
    load_text_template,
    format_value_to_toml, # Vẫn dùng để format giá trị cho template
    load_project_config_section,
    load_toml_file # Vẫn dùng load_toml_file (vì nó kiểm tra tomllib)
)
# Import các tiện ích UI
from .ui_helpers import prompt_config_overwrite, launch_editor
# Import tiện ích logging
from utils.logging_config import log_success

__all__ = ["handle_config_init_request"]


def _generate_template_content(
    logger: logging.Logger,
    module_dir: Path,
    template_filename: str,
    config_section_name: str,
    effective_defaults: Dict[str, Any]
) -> str:
    """
    Tải file template .toml, điền các giá trị mặc định vào đó.
    (Giữ nguyên logic)
    """
    template_path = module_dir / template_filename
    template_str = load_text_template(template_path, logger)

    format_dict: Dict[str, str] = {
        'config_section_name': config_section_name,
    }

    for key, value in effective_defaults.items():
        placeholder_key = f"toml_{key.replace('-', '_')}"
        format_dict[placeholder_key] = format_value_to_toml(value)

    try:
        content_filled = template_str.format(**format_dict)
    except KeyError as e:
        logger.error(f"❌ Lỗi: Template '{template_filename}' thiếu placeholder: {e}")
        raise ValueError(f"Template '{template_filename}' thiếu placeholder: {e}")

    start_marker = f"[{config_section_name}]"
    if start_marker not in content_filled:
        logger.error(f"❌ Lỗi: Nội dung template sau khi format thiếu header section '{start_marker}'.")
        raise ValueError(f"Template '{template_filename}' thiếu header section '{start_marker}' sau khi format.")

    return content_filled


def _handle_local_scope(
    logger: logging.Logger,
    config_file_path: Path,
    content_from_template: str,
) -> Optional[Path]:
    """
    Xử lý logic I/O cho scope 'local'.
    (Kiểm tra, Hỏi, Ghi đè toàn bộ file - Sử dụng write_text thông thường)
    """
    file_existed = config_file_path.exists()
    should_write = True

    if file_existed:
        should_write = prompt_config_overwrite(
            logger, config_file_path, f"File '{config_file_path.name}'"
        )

    if should_write is None:
        return None

    if should_write:
        try:
            # Ghi nội dung đã tạo từ template bằng write_text
            config_file_path.write_text(content_from_template, encoding="utf-8")
            log_msg = (
                f"Đã tạo thành công '{config_file_path.name}'." if not file_existed
                else f"Đã ghi đè thành công '{config_file_path.name}'."
            )
            log_success(logger, log_msg)
        except IOError as e:
            logger.error(f"❌ Lỗi I/O khi ghi file '{config_file_path.name}': {e}")
            raise

    return config_file_path


def _handle_project_scope_with_tomlkit(
    logger: logging.Logger,
    config_file_path: Path,
    config_section_name: str,
    new_section_data: Dict[str, Any],
) -> Optional[Path]:
    """
    Xử lý logic I/O cho scope 'project' sử dụng tomlkit.
    (Kiểm tra, Hỏi, Đọc bằng tomlkit, Sửa đổi, Ghi bằng tomlkit)
    """
    should_write = True
    try:
        # 1. Đọc file bằng tomlkit, bảo toàn mọi định dạng
        content = config_file_path.read_text(encoding='utf-8') if config_file_path.exists() else ""
        doc = tomlkit.parse(content)

        # 2. Kiểm tra section
        section_existed = config_section_name in doc
        if section_existed:
            should_write = prompt_config_overwrite(
                logger, config_file_path, f"Section [{config_section_name}]"
            )

        if should_write is None:
            return None

        if should_write:
            # 3. Chuẩn bị dữ liệu để ghi (chuyển set -> list, BỎ QUA None)
            serializable_data = tomlkit.table()
            for k, v in new_section_data.items():
                # --- SỬA LỖI: Bỏ qua giá trị None ---
                if v is None:
                    continue
                # ------------------------------------
                if isinstance(v, set):
                    serializable_data[k] = tomlkit.array(sorted(list(v)))
                else:
                    serializable_data[k] = v

            # Gán section mới vào tài liệu
            doc[config_section_name] = serializable_data

            # 4. Ghi lại file
            with config_file_path.open('w', encoding='utf-8') as f:
                tomlkit.dump(doc, f)

            log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.")

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi cập nhật file '{config_file_path.name}': {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi cập nhật TOML (tomlkit): {e}")
        raise

    return config_file_path


def handle_config_init_request(
    logger: logging.Logger,
    config_project: bool,
    config_local: bool,
    # Thông tin về template và file config
    module_dir: Path,
    template_filename: str,
    config_filename: str,
    project_config_filename: str,
    config_section_name: str,
    # Dữ liệu mặc định
    base_defaults: Dict[str, Any]
) -> bool:
    """
    Hàm điều phối (Orchestrator) logic tạo/cập nhật file config.
    """

    if not (config_project or config_local):
        return False

    # Kiểm tra thư viện TOML cần thiết
    toml_read_lib_missing = tomllib is None
    toml_write_lib_missing = tomlkit is None

    if toml_read_lib_missing:
         logger.error("❌ Thiếu thư viện đọc TOML ('tomllib' hoặc 'toml').")
         logger.error("   Vui lòng cài đặt: 'pip install toml' (hoặc dùng Python 3.11+ cho 'tomllib')")
    if toml_write_lib_missing:
         logger.error("❌ Thiếu thư viện ghi TOML bảo toàn định dạng ('tomlkit').")
         logger.error("   Vui lòng chạy: pip install tomlkit")

    if toml_read_lib_missing or toml_write_lib_missing:
        raise ImportError("Thiếu thư viện TOML cần thiết")

    scope = 'project' if config_project else 'local'
    logger.info(f"Yêu cầu khởi tạo cấu hình scope '{scope}'...")

    # 1. Xác định các giá trị mặc định hiệu lực (Giữ nguyên)
    effective_defaults = base_defaults.copy()
    if scope == "local":
        project_config_path = Path.cwd() / project_config_filename
        project_section = load_project_config_section(
            project_config_path, config_section_name, logger
        )
        if project_section:
            logger.debug(f"Sử dụng section [{config_section_name}] từ '{project_config_filename}' làm cơ sở cho template '{config_filename}'.")
            effective_defaults.update(project_section)
        else:
            logger.debug(f"Không tìm thấy '{project_config_filename}' hoặc section [{config_section_name}], sử dụng default gốc cho template '{config_filename}'.")

    # 2. Khởi tạo
    config_file_path: Optional[Path] = None

    try:
        if scope == "local":
            content_from_template = _generate_template_content(
                logger, module_dir, template_filename,
                config_section_name, effective_defaults
            )
            target_path = Path.cwd() / config_filename
            config_file_path = _handle_local_scope(
                logger, target_path, content_from_template
            )

        elif scope == "project":
            # Chuẩn bị dict dữ liệu (không cần lọc None ở đây nữa, helper sẽ xử lý)
            new_section_data = effective_defaults.copy()
            target_path = Path.cwd() / project_config_filename
            config_file_path = _handle_project_scope_with_tomlkit(
                logger, target_path, config_section_name, new_section_data
            )

    except (FileNotFoundError, ValueError, IOError, ImportError, Exception) as e:
        logger.error(f"❌ Không thể hoàn tất khởi tạo config do lỗi: {e}")
        raise

    # 3. Mở file config trong editor (nếu không bị hủy)
    if config_file_path:
        launch_editor(logger, config_file_path)

    return True