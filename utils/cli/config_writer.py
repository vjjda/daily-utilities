# Path: utils/cli/config_writer.py

"""
Tiện ích xử lý logic ghi file config cho các entrypoint CLI.
(Module nội bộ, được import bởi utils/cli)

Chứa logic chung để tạo/cập nhật file .toml cục bộ hoặc
section trong .project.toml dựa trên template.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import io # Import io

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
    write_toml_file, # Still used for scope == 'local'
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
        logger.error(f"❌ Lỗi: Template '{template_filename}' thiếu placeholder: {e}")
        raise ValueError(f"Template '{template_filename}' thiếu placeholder: {e}")

    # Kiểm tra xem header section có tồn tại trong kết quả không
    start_marker = f"[{config_section_name}]"
    if start_marker not in content_filled:
        logger.error(f"❌ Lỗi: Nội dung template sau khi format thiếu header section '{start_marker}'.")
        raise ValueError(f"Template '{template_filename}' thiếu header section '{start_marker}' sau khi format.")

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
    4. Tạo nội dung config từ template (cho scope local) hoặc dict (cho scope project).
    5. Hỏi người dùng nếu file/section đã tồn tại.
    6. Ghi nội dung vào file đích (ghi đè toàn bộ file cho local, thay thế section cho project).
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
         logger.error("❌ Thiếu thư viện TOML ('tomllib'/'toml' và 'tomli-w').")
         logger.error("   Vui lòng cài đặt: 'pip install toml tomli-w' (hoặc dùng Python 3.11+ cho 'tomllib')")
         raise ImportError("Thiếu thư viện TOML")

    scope = 'project' if config_project else 'local'
    logger.info(f"Yêu cầu khởi tạo cấu hình scope '{scope}'...")

    # Xác định các giá trị mặc định cuối cùng
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

    # Tạo nội dung config TỪ TEMPLATE (chỉ dùng cho scope local)
    content_from_template = ""
    if scope == "local":
        try:
            content_from_template = _generate_template_content(
                logger, module_dir, template_filename,
                config_section_name, effective_defaults
            )
        except (FileNotFoundError, ValueError, Exception) as e:
            logger.error(f"❌ Lỗi khi tạo nội dung template: {e}")
            raise

    should_write: Optional[bool] = True # Mặc định là ghi
    config_file_path: Path

    # Xử lý ghi file dựa trên scope
    if scope == "local":
        config_file_path = Path.cwd() / config_filename
        file_existed = config_file_path.exists()

        if file_existed:
            should_write = prompt_config_overwrite(
                logger, config_file_path, f"File '{config_filename}'"
            )

        if should_write is None: return True # Báo dừng

        if should_write:
            try:
                # Ghi nội dung đã tạo từ template
                config_file_path.write_text(content_from_template, encoding="utf-8")
                log_msg = (
                    f"Đã tạo thành công '{config_file_path.name}'." if not file_existed
                    else f"Đã ghi đè thành công '{config_file_path.name}'."
                )
                log_success(logger, log_msg)
            except IOError as e:
                logger.error(f"❌ Lỗi I/O khi ghi file '{config_file_path.name}': {e}")
                raise

    elif scope == "project":
        config_file_path = Path.cwd() / project_config_filename

        # Chuẩn bị dict dữ liệu cho section mới (lọc None, chuyển set->list)
        valid_defaults = {
            k: v for k, v in effective_defaults.items() if v is not None
        }
        new_section_dict_serializable = {}
        for k, v in valid_defaults.items():
            if isinstance(v, set):
                new_section_dict_serializable[k] = sorted(list(v))
            else:
                new_section_dict_serializable[k] = v

        # Kiểm tra xem section có tồn tại trong file hiện tại không
        config_data = load_toml_file(config_file_path, logger)
        section_existed = config_section_name in config_data

        if section_existed:
            should_write = prompt_config_overwrite(
                logger, config_file_path, f"Section [{config_section_name}]"
            )

        if should_write is None: return True # Báo dừng

        if should_write:
            try:
                # --- SỬA LỖI (Vòng 5) ---
                # Sử dụng io.BytesIO thay vì io.StringIO
                # và decode kết quả thành string UTF-8
                section_io = io.BytesIO()
                tomli_w.dump({config_section_name: new_section_dict_serializable}, section_io)
                new_section_bytes = section_io.getvalue()
                new_section_content = new_section_bytes.decode('utf-8').strip()
                # --- KẾT THÚC SỬA LỖI ---

                # Thêm dòng trống nếu dict không rỗng
                if new_section_dict_serializable:
                     new_section_content += "\n"

                # Đọc file gốc line-by-line và thay thế section
                original_lines = config_file_path.read_text(encoding='utf-8').splitlines(True) if config_file_path.exists() else []
                output_lines: List[str] = []
                in_section = False
                section_found = False

                for line in original_lines:
                    stripped_line = line.strip()
                    # Phát hiện bắt đầu section
                    if stripped_line == f"[{config_section_name}]":
                        in_section = True
                        section_found = True
                        # Ghi nội dung section mới (bao gồm header)
                        output_lines.append(new_section_content + "\n")
                        continue # Bỏ qua dòng header cũ

                    # Phát hiện kết thúc section (bắt đầu section mới hoặc hết file)
                    if in_section and stripped_line.startswith("[") and stripped_line.endswith("]"):
                        in_section = False

                    # Chỉ giữ lại các dòng không thuộc section cũ
                    if not in_section:
                        output_lines.append(line)

                # Nếu section không tồn tại trong file gốc, thêm vào cuối
                if not section_found:
                    # Thêm dòng trống nếu file không rỗng và chưa kết thúc bằng newline
                    if output_lines and not output_lines[-1].endswith('\n'):
                        output_lines.append('\n')
                    output_lines.append(new_section_content + "\n")

                # Ghi lại file
                config_file_path.write_text("".join(output_lines), encoding='utf-8')
                log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.")

            except IOError as e:
                logger.error(f"❌ Lỗi I/O khi cập nhật file '{config_file_path.name}': {e}")
                raise
            except Exception as e:
                logger.error(f"❌ Lỗi không mong muốn khi cập nhật TOML section: {e}")
                raise

    # Mở file config trong editor sau khi ghi
    launch_editor(logger, config_file_path)

    return True # Báo cho entrypoint dừng sau khi hoàn thành