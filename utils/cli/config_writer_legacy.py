# Path: utils/cli/config_writer_legacy.py
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import io


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


from utils.core import (
    load_text_template,
    format_value_to_toml,
    load_toml_file,
    load_project_config_section,
)

from .ui_helpers import prompt_config_overwrite, launch_editor

from utils.logging_config import log_success

__all__ = ["handle_config_init_request"]


def _generate_template_content(
    logger: logging.Logger,
    module_dir: Path,
    template_filename: str,
    config_section_name: str,
    effective_defaults: Dict[str, Any],
) -> str:
    template_path = module_dir / template_filename
    template_str = load_text_template(template_path, logger)

    format_dict: Dict[str, str] = {
        "config_section_name": config_section_name,
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
        logger.error(
            f"❌ Lỗi: Nội dung template sau khi format thiếu header section '{start_marker}'."
        )
        raise ValueError(
            f"Template '{template_filename}' thiếu header section '{start_marker}' sau khi format."
        )

    return content_filled


def _handle_local_scope(
    logger: logging.Logger,
    config_file_path: Path,
    content_from_template: str,
) -> Optional[Path]:
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
            config_file_path.write_text(content_from_template, encoding="utf-8")
            log_msg = (
                f"Đã tạo thành công '{config_file_path.name}'."
                if not file_existed
                else f"Đã ghi đè thành công '{config_file_path.name}'."
            )
            log_success(logger, log_msg)
        except IOError as e:
            logger.error(f"❌ Lỗi I/O khi ghi file '{config_file_path.name}': {e}")
            raise

    return config_file_path


def _handle_project_scope(
    logger: logging.Logger,
    config_file_path: Path,
    config_section_name: str,
    new_section_data: Dict[str, Any],
) -> Optional[Path]:
    should_write = True
    try:

        config_data = load_toml_file(config_file_path, logger)
        section_existed = config_section_name in config_data

        if section_existed:
            should_write = prompt_config_overwrite(
                logger, config_file_path, f"Section [{config_section_name}]"
            )

        if should_write is None:
            return None

        if should_write:

            section_io = io.BytesIO()
            tomli_w.dump({config_section_name: new_section_data}, section_io)
            new_section_bytes = section_io.getvalue()
            new_section_content = new_section_bytes.decode("utf-8").strip()

            if new_section_data:
                new_section_content += "\n"

            original_lines = (
                config_file_path.read_text(encoding="utf-8").splitlines(True)
                if config_file_path.exists()
                else []
            )
            output_lines: List[str] = []
            in_section = False
            section_found = False

            for line in original_lines:
                stripped_line = line.strip()
                if stripped_line == f"[{config_section_name}]":
                    in_section = True
                    section_found = True
                    output_lines.append(new_section_content + "\n")
                    continue
                if (
                    in_section
                    and stripped_line.startswith("[")
                    and stripped_line.endswith("]")
                ):
                    in_section = False
                if not in_section:
                    output_lines.append(line)

            if not section_found:
                if output_lines and not output_lines[-1].endswith("\n"):
                    output_lines.append("\n")
                output_lines.append(new_section_content + "\n")

            config_file_path.write_text("".join(output_lines), encoding="utf-8")
            log_success(
                logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'."
            )

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi cập nhật file '{config_file_path.name}': {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi cập nhật TOML section: {e}")
        raise

    return config_file_path


def handle_config_init_request(
    logger: logging.Logger,
    config_project: bool,
    config_local: bool,
    module_dir: Path,
    template_filename: str,
    config_filename: str,
    project_config_filename: str,
    config_section_name: str,
    base_defaults: Dict[str, Any],
) -> bool:

    if not (config_project or config_local):
        return False

    if tomllib is None or tomli_w is None:
        logger.error("❌ Thiếu thư viện TOML ('tomllib'/'toml' và 'tomli-w').")
        logger.error(
            "   Vui lòng cài đặt: 'pip install toml tomli-w' (hoặc dùng Python 3.11+ cho 'tomllib')"
        )
        raise ImportError("Thiếu thư viện TOML")

    scope = "project" if config_project else "local"
    logger.info(f"Yêu cầu khởi tạo cấu hình scope '{scope}'...")

    effective_defaults = base_defaults.copy()
    if scope == "local":
        project_config_path = Path.cwd() / project_config_filename
        project_section = load_project_config_section(
            project_config_path, config_section_name, logger
        )
        if project_section:
            logger.debug(
                f"Sử dụng section [{config_section_name}] từ '{project_config_filename}' làm cơ sở cho template '{config_filename}'."
            )
            effective_defaults.update(project_section)
        else:
            logger.debug(
                f"Không tìm thấy '{project_config_filename}' hoặc section [{config_section_name}], sử dụng default gốc cho template '{config_filename}'."
            )

    config_file_path: Optional[Path] = None

    try:
        if scope == "local":
            content_from_template = _generate_template_content(
                logger,
                module_dir,
                template_filename,
                config_section_name,
                effective_defaults,
            )
            target_path = Path.cwd() / config_filename

            config_file_path = _handle_local_scope(
                logger, target_path, content_from_template
            )

        elif scope == "project":

            valid_defaults = {
                k: v for k, v in effective_defaults.items() if v is not None
            }
            new_section_data = {}
            for k, v in valid_defaults.items():
                new_section_data[k] = sorted(list(v)) if isinstance(v, set) else v

            target_path = Path.cwd() / project_config_filename

            config_file_path = _handle_project_scope(
                logger, target_path, config_section_name, new_section_data
            )

    except (FileNotFoundError, ValueError, IOError, Exception) as e:

        logger.error(f"❌ Không thể hoàn tất khởi tạo config do lỗi: {e}")
        raise

    if config_file_path:
        launch_editor(logger, config_file_path)

    return True