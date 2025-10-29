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
    # --- THAY ĐỔI: Nhận cả thông tin template ---
    module_dir: Path,
    template_filename: str,
    effective_defaults: Dict[str, Any],
    # --- KẾT THÚC THAY ĐỔI ---
) -> Optional[Path]:
    """
    Xử lý logic I/O cho scope 'project' sử dụng tomlkit.
    Tạo section mới từ template để bảo toàn comment.
    """
    should_write = True
    try:
        # 1. Đọc file .project.toml chính bằng tomlkit
        content = config_file_path.read_text(encoding='utf-8') if config_file_path.exists() else ""
        main_doc = tomlkit.parse(content)

        # 2. Kiểm tra section có tồn tại không
        section_existed = config_section_name in main_doc
        if section_existed:
            should_write = prompt_config_overwrite(
                logger, config_file_path, f"Section [{config_section_name}]"
            )

        if should_write is None:
            return None

        if should_write:
            # --- THAY ĐỔI LOGIC: Tạo section từ template ---
            # 3. Tạo nội dung string của section mới từ template
            #    Hàm này đã bao gồm cả comment và giá trị mặc định
            try:
                # _generate_template_content tạo ra toàn bộ nội dung file ảo
                # bao gồm '[section_name]' ở đầu
                new_section_string_content = _generate_template_content(
                    logger, module_dir, template_filename,
                    config_section_name, effective_defaults
                )
                # Parse chuỗi này để lấy đối tượng tomlkit có comment
                parsed_section_doc = tomlkit.parse(new_section_string_content)
                # Lấy đối tượng Table của section từ document vừa parse
                new_section_object_with_comments = parsed_section_doc[config_section_name]

            except (FileNotFoundError, ValueError, Exception) as e:
                 logger.error(f"❌ Lỗi khi tạo/phân tích nội dung section từ template: {e}")
                 raise # Ném lại lỗi

            # 4. Gán đối tượng section (có comment) vào tài liệu chính
            main_doc[config_section_name] = new_section_object_with_comments
            # --- KẾT THÚC THAY ĐỔI LOGIC ---

            # 5. Ghi lại file .project.toml chính
            with config_file_path.open('w', encoding='utf-8') as f:
                tomlkit.dump(main_doc, f)

            log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.")

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi cập nhật file '{config_file_path.name}': {e}")
        raise
    # Bắt thêm lỗi ConvertError từ tomlkit nếu có gì đó không ổn
    except (tomlkit.exceptions.ConvertError, Exception) as e:
        logger.error(f"❌ Lỗi không mong muốn khi cập nhật TOML (tomlkit): {e}")
        raise

    return config_file_path

# --- Cập nhật hàm điều phối handle_config_init_request ---

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
    # (Phần kiểm tra thư viện và xác định scope giữ nguyên)
    # ...
    if not (config_project or config_local):
        return False

    if tomllib is None or tomlkit is None: # Đổi kiểm tra thành tomlkit
        # (Log lỗi giữ nguyên)
        # ...
        raise ImportError("Thiếu thư viện TOML cần thiết")

    scope = 'project' if config_project else 'local'
    logger.info(f"Yêu cầu khởi tạo cấu hình scope '{scope}'...")

    # (Phần xác định effective_defaults giữ nguyên)
    # ...
    effective_defaults = base_defaults.copy()
    if scope == "local":
        # ... (logic load project_section giữ nguyên)
        project_config_path = Path.cwd() / project_config_filename
        project_section = load_project_config_section(
            project_config_path, config_section_name, logger
        )
        if project_section:
            logger.debug(f"Sử dụng section [{config_section_name}] từ '{project_config_filename}' làm cơ sở cho template '{config_filename}'.")
            effective_defaults.update(project_section)
        else:
            logger.debug(f"Không tìm thấy '{project_config_filename}' hoặc section [{config_section_name}], sử dụng default gốc cho template '{config_filename}'.")


    config_file_path: Optional[Path] = None

    try:
        if scope == "local":
            # Tạo nội dung từ template cho file local
            content_from_template = _generate_template_content(
                logger, module_dir, template_filename,
                config_section_name, effective_defaults
            )
            target_path = Path.cwd() / config_filename
            config_file_path = _handle_local_scope(
                logger, target_path, content_from_template
            )

        elif scope == "project":
            target_path = Path.cwd() / project_config_filename
            # Gọi helper project mới, truyền thêm thông tin template
            config_file_path = _handle_project_scope_with_tomlkit(
                logger=logger,
                config_file_path=target_path,
                config_section_name=config_section_name,
                # --- Truyền thông tin template ---
                module_dir=module_dir,
                template_filename=template_filename,
                effective_defaults=effective_defaults
                # --- Hết ---
            )

    except (FileNotFoundError, ValueError, IOError, ImportError, Exception) as e:
        logger.error(f"❌ Không thể hoàn tất khởi tạo config do lỗi: {e}")
        raise

    # (Phần mở editor giữ nguyên)
    # ...
    if config_file_path:
        launch_editor(logger, config_file_path)

    return True