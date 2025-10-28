# Path: utils/cli/config_writer.py

"""
Tiện ích xử lý logic ghi file config cho các entrypoint CLI.
(Module nội bộ, được import bởi utils/cli)

Chứa logic chung để tạo/cập nhật file .toml cục bộ hoặc
section trong .project.toml dựa trên template.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Cố gắng import thư viện TOML
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

# Import các tiện ích cốt lõi
from utils.core import (
    load_text_template,
    format_value_to_toml,
    load_toml_file,
    write_toml_file,
    load_project_config_section
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

    Args:
        logger: Logger.
        module_dir: Thư mục chứa file template (ví dụ: modules/tree).
        template_filename: Tên file template (ví dụ: "tree.toml.template").
        config_section_name: Tên section config (ví dụ: "tree").
        effective_defaults: Dict chứa các giá trị mặc định cuối cùng cần điền.

    Returns:
        Nội dung template đã được điền dưới dạng string.

    Raises:
        FileNotFoundError, Exception: Nếu không tải được template.
        ValueError: Nếu template thiếu header section.
    """

    # Tải nội dung template thô
    template_path = module_dir / template_filename
    template_str = load_text_template(template_path, logger) # Ném lỗi nếu thất bại

    # Chuẩn bị dict để format template
    format_dict: Dict[str, str] = {
        'config_section_name': config_section_name,
        # Thêm các placeholder khác nếu cần (ví dụ: toml_level cho ctree)
    }

    # Format các giá trị mặc định thành chuỗi TOML
    for key, value in effective_defaults.items():
        # Tạo key placeholder (ví dụ: "use-gitignore" -> "toml_use_gitignore")
        placeholder_key = f"toml_{key.replace('-', '_')}"
        format_dict[placeholder_key] = format_value_to_toml(value)

    # Điền vào template
    try:
        content_filled = template_str.format(**format_dict)
    except KeyError as e:
        logger.error(f"❌ Lỗi: Template '{template_filename}' thiếu placeholder: {e}") #
        raise ValueError(f"Template '{template_filename}' thiếu placeholder: {e}")

    # Kiểm tra xem header section có tồn tại trong kết quả không
    start_marker = f"[{config_section_name}]"
    if start_marker not in content_filled:
        logger.error(f"❌ Lỗi: Nội dung template sau khi format thiếu header section '{start_marker}'.") #
        raise ValueError(f"Template '{template_filename}' thiếu header section '{start_marker}' sau khi format.") #

    return content_filled


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
    Xử lý logic tạo/cập nhật file config khi người dùng chạy với cờ -c hoặc -C.

    Hàm này sẽ:
    1. Kiểm tra thư viện TOML.
    2. Xác định scope (local/project) và file đích.
    3. Xác định các giá trị mặc định hiệu lực (có thể lấy từ project nếu tạo local).
    4. Tạo nội dung config từ template.
    5. Hỏi người dùng nếu file/section đã tồn tại.
    6. Ghi nội dung vào file đích.
    7. Mở file trong editor.

    Args:
        logger: Logger.
        config_project: True nếu cờ --config-project được dùng.
        config_local: True nếu cờ --config-local được dùng.
        module_dir: Đường dẫn đến thư mục module chứa template.
        template_filename: Tên file template (ví dụ: "tree.toml.template").
        config_filename: Tên file config cục bộ (ví dụ: ".tree.toml").
        project_config_filename: Tên file config dự án (ví dụ: ".project.toml").
        config_section_name: Tên section config (ví dụ: "tree").
        base_defaults: Dict chứa các giá trị mặc định gốc của tool.

    Returns:
        True nếu một hành động config đã được thực hiện (và script nên dừng lại),
        False nếu không có cờ config nào được cung cấp.

    Raises:
        ImportError: Nếu thiếu thư viện TOML cần thiết.
        IOError, ValueError, Exception: Nếu có lỗi trong quá trình xử lý.
    """

    # Nếu không có cờ config nào, không làm gì cả
    if not (config_project or config_local):
        return False

    # Kiểm tra thư viện TOML
    if tomllib is None or tomli_w is None:
         logger.error("❌ Thiếu thư viện TOML ('tomllib'/'toml' và 'tomli-w').") #
         logger.error("   Vui lòng cài đặt: 'pip install toml tomli-w' (hoặc dùng Python 3.11+ cho 'tomllib')") #
         raise ImportError("Thiếu thư viện TOML") #

    scope = 'project' if config_project else 'local'
    logger.info(f"Yêu cầu khởi tạo cấu hình scope '{scope}'...") #

    # Xác định các giá trị mặc định cuối cùng để điền vào template
    effective_defaults = base_defaults.copy()
    if scope == "local":
        # Nếu tạo file local, thử đọc section tương ứng từ file project làm cơ sở
        project_config_path = Path.cwd() / project_config_filename
        project_section = load_project_config_section(
            project_config_path,
            config_section_name,
            logger
        )
        if project_section:
            logger.debug(f"Sử dụng section [{config_section_name}] từ '{project_config_filename}' làm cơ sở cho template '{config_filename}'.") #
            effective_defaults.update(project_section) # Ghi đè default gốc bằng giá trị từ project
        else:
            logger.debug(f"Không tìm thấy '{project_config_filename}' hoặc section [{config_section_name}], sử dụng default gốc cho template '{config_filename}'.") #

    # Tạo nội dung config từ template
    try:
        content_to_write = _generate_template_content(
            logger,
            module_dir,
            template_filename,
            config_section_name,
            effective_defaults
        )
    except (FileNotFoundError, ValueError, Exception) as e:
        logger.error(f"❌ Lỗi khi tạo nội dung template: {e}") #
        raise # Ném lại lỗi

    should_write: Optional[bool] = True # Mặc định là ghi
    config_file_path: Path

    # Xử lý ghi file dựa trên scope
    if scope == "local":
        config_file_path = Path.cwd() / config_filename
        file_existed = config_file_path.exists()

        if file_existed:
            # Hỏi người dùng nếu file đã tồn tại
            should_write = prompt_config_overwrite(
                logger,
                config_file_path,
                f"File '{config_filename}'" #
            )

        if should_write is None: # Người dùng chọn Quit
            return True # Báo cho entrypoint dừng

        if should_write:
            try:
                config_file_path.write_text(content_to_write, encoding="utf-8")
                log_msg = (
                    f"Đã tạo thành công '{config_file_path.name}'." if not file_existed
                    else f"Đã ghi đè thành công '{config_file_path.name}'." #
                )
                log_success(logger, log_msg)
            except IOError as e:
                logger.error(f"❌ Lỗi I/O khi ghi file '{config_file_path.name}': {e}") #
                raise # Ném lại lỗi

    elif scope == "project":
        config_file_path = Path.cwd() / project_config_filename

        # Chỉ lấy phần nội dung của section từ template đã được điền
        try:
            full_toml_dict = tomllib.loads(content_to_write)
            new_section_dict = full_toml_dict.get(config_section_name, {})
            if not new_section_dict:
                 raise ValueError(f"Section [{config_section_name}] rỗng sau khi parse template.") #
        except Exception as e:
             logger.error(f"❌ Lỗi khi parse nội dung template đã điền: {e}") #
             raise

        # Đọc file .project.toml hiện có
        config_data = load_toml_file(config_file_path, logger)

        # Hỏi người dùng nếu section đã tồn tại
        if config_section_name in config_data:
            should_write = prompt_config_overwrite(
                logger,
                config_file_path,
                f"Section [{config_section_name}]" #
            )

        if should_write is None: # Người dùng chọn Quit
            return True # Báo cho entrypoint dừng

        if should_write:
            # Cập nhật hoặc thêm section mới vào dữ liệu đã đọc
            config_data[config_section_name] = new_section_dict
            # Ghi lại toàn bộ file .project.toml
            if not write_toml_file(config_file_path, config_data, logger):
                raise IOError(f"Không thể ghi file TOML: {config_file_path.name}") #
            log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.") #

    # Mở file config trong editor sau khi ghi
    launch_editor(logger, config_file_path)

    return True # Báo cho entrypoint dừng sau khi hoàn thành