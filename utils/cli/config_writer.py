# Path: utils/cli/config_writer.py
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import io
import re # <-- Added import

# Cố gắng import thư viện TOML
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

try:
    import tomlkit
except ImportError:
    tomlkit = None

# Import các tiện ích cốt lõi
from utils.core import (
    load_text_template,
    # format_value_to_toml is still needed for individual value formatting
    format_value_to_toml as _format_single_value_to_toml,
    load_project_config_section,
    load_toml_file
)
# Import các tiện ích UI
from .ui_helpers import prompt_config_overwrite, launch_editor
# Import tiện ích logging
from utils.logging_config import log_success

__all__ = ["handle_config_init_request"]

# --- REVISED Generator Function ---
def _generate_template_content(
    logger: logging.Logger,
    module_dir: Path,
    template_filename: str,
    config_section_name: str, # Keep for header check
    effective_defaults: Dict[str, Any]
) -> str:
    """
    Tải template, giữ comment, và chèn giá trị mặc định chỉ khi chúng không None.
    Nếu giá trị mặc định là None, comment out dòng key = value đó trong template.
    """
    template_path = module_dir / template_filename
    template_lines = load_text_template(template_path, logger).splitlines()

    output_lines = []
    section_header_expected = f"[{config_section_name}]" # Used for validation later
    header_found_in_template = False

    # Regex để tìm dòng `key = {placeholder}` hoặc `# key = {placeholder}`
    # Groups: 1:indent, 2:comment_marker, 3:key_name_toml, 4:placeholder_suffix
    placeholder_pattern = re.compile(r"^(\s*)(#?\s*)([\w-]+)\s*=\s*\{toml_(\w+)\}\s*(?:#.*)?$")

    for line in template_lines:
        match = placeholder_pattern.match(line)
        if match:
            indent = match.group(1)
            comment_marker = match.group(2) # Original comment marker (e.g., '# ' or '  ')
            key_name_toml = match.group(3)
            placeholder_suffix = match.group(4)
            # Convert placeholder suffix (use_gitignore) to dict key (use-gitignore)
            key_name_dict = placeholder_suffix.replace('_', '-')

            if key_name_dict in effective_defaults:
                value = effective_defaults[key_name_dict]
                if value is not None:
                    # Value exists and is not None: write the line UNCOMMENTED
                    value_str = _format_single_value_to_toml(value)
                    output_lines.append(f"{indent}{key_name_toml} = {value_str}")
                else:
                    # Value is None: write the line COMMENTED OUT
                    # Use '# ' as the standard comment marker
                    output_lines.append(f"{indent}# {key_name_toml} = ") # Show key but no value, commented
            else:
                 # Key not found in defaults, keep template line as is (likely commented or placeholder)
                 output_lines.append(line)
        else:
            # Not a placeholder line, keep as is (header, comment, blank line)
            if section_header_expected in line:
                header_found_in_template = True
            output_lines.append(line)

    # Validation
    if not header_found_in_template:
         raise ValueError(f"Template '{template_filename}' thiếu header section '{section_header_expected}'.")

    # Add trailing newline if needed
    if output_lines and output_lines[-1].strip() != "":
        output_lines.append("")

    return "\n".join(output_lines)


# _handle_local_scope remains the same, it uses the generated string directly
def _handle_local_scope(
    logger: logging.Logger,
    config_file_path: Path,
    content_from_template: str,
) -> Optional[Path]:
    """Handles I/O logic for 'local' scope."""
    file_existed = config_file_path.exists()
    should_write = True

    if file_existed:
        should_write = prompt_config_overwrite(
            logger, config_file_path, f"File '{config_file_path.name}'"
        )

    if should_write is None: return None

    if should_write:
        try:
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


# _handle_project_scope_with_tomlkit uses the generated string, parses it, extracts, assigns
def _handle_project_scope_with_tomlkit(
    logger: logging.Logger,
    config_file_path: Path,
    config_section_name: str,
    module_dir: Path,
    template_filename: str,
    effective_defaults: Dict[str, Any],
) -> Optional[Path]:
    """Handles I/O logic for 'project' scope using tomlkit, preserving comments."""
    should_write = True
    try:
        content = config_file_path.read_text(encoding='utf-8') if config_file_path.exists() else ""
        main_doc = tomlkit.parse(content)

        section_existed = config_section_name in main_doc
        if section_existed:
            should_write = prompt_config_overwrite(
                logger, config_file_path, f"Section [{config_section_name}]"
            )

        if should_write is None: return None

        if should_write:
            try:
                # Generate the syntactically valid section string using the revised generator
                new_section_string_content = _generate_template_content(
                    logger, module_dir, template_filename,
                    config_section_name, effective_defaults
                )
                # Parse this string (which now handles None correctly by commenting)
                parsed_section_doc = tomlkit.parse(new_section_string_content)

                # Extract the Table object (should exist and be valid)
                if config_section_name not in parsed_section_doc:
                     raise ValueError(f"Generated content unexpectedly missing section [{config_section_name}] after parsing.")
                new_section_object = parsed_section_doc[config_section_name]

            except (FileNotFoundError, ValueError, tomlkit.exceptions.ParseError, Exception) as e:
                 logger.error(f"❌ Lỗi khi tạo/phân tích nội dung section từ template: {e}")
                 raise

            # Assign the TOML Table object (preserving comments/structure from template)
            main_doc[config_section_name] = new_section_object

            # Write back the main document
            with config_file_path.open('w', encoding='utf-8') as f:
                tomlkit.dump(main_doc, f)

            log_success(logger, f"✅ Đã tạo/cập nhật thành công '{config_file_path.name}'.")

    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi cập nhật file '{config_file_path.name}': {e}")
        raise
    except (tomlkit.exceptions.ParseError, tomlkit.exceptions.ConvertError, Exception) as e:
        logger.error(f"❌ Lỗi không mong muốn khi cập nhật TOML (tomlkit): {e}")
        raise

    return config_file_path


# Orchestrator function - no significant changes needed here
def handle_config_init_request(
    logger: logging.Logger,
    config_project: bool,
    config_local: bool,
    module_dir: Path,
    template_filename: str,
    config_filename: str,
    project_config_filename: str,
    config_section_name: str,
    base_defaults: Dict[str, Any]
) -> bool:
    """Orchestrates the config initialization/update process."""

    if not (config_project or config_local): return False

    toml_read_lib_missing = tomllib is None
    toml_write_lib_missing = tomlkit is None

    if toml_read_lib_missing:
         logger.error("❌ Thiếu thư viện đọc TOML ('tomllib' hoặc 'toml').")
    if toml_write_lib_missing:
         logger.error("❌ Thiếu thư viện ghi TOML ('tomlkit').")
    if toml_read_lib_missing or toml_write_lib_missing:
        raise ImportError("Thiếu thư viện TOML cần thiết")

    scope = 'project' if config_project else 'local'
    logger.info(f"Yêu cầu khởi tạo cấu hình scope '{scope}'...")

    # Determine effective defaults (remains the same)
    effective_defaults = base_defaults.copy()
    if scope == "local":
        project_config_path = Path.cwd() / project_config_filename
        project_section = load_project_config_section(
            project_config_path, config_section_name, logger
        )
        if project_section:
            logger.debug(f"Sử dụng section [{config_section_name}] từ '{project_config_filename}' làm cơ sở.")
            effective_defaults.update(project_section)
        else:
            logger.debug(f"Không tìm thấy section [{config_section_name}] trong '{project_config_filename}', dùng default gốc.")

    config_file_path: Optional[Path] = None

    try:
        # Generate the content string once using the revised generator
        generated_content_string = _generate_template_content(
            logger, module_dir, template_filename,
            config_section_name, effective_defaults
        )

        if scope == "local":
            target_path = Path.cwd() / config_filename
            config_file_path = _handle_local_scope(
                logger, target_path, generated_content_string
            )
        elif scope == "project":
            target_path = Path.cwd() / project_config_filename
            # The project handler now needs the template info again to regenerate/parse
            config_file_path = _handle_project_scope_with_tomlkit(
                logger=logger,
                config_file_path=target_path,
                config_section_name=config_section_name,
                module_dir=module_dir,
                template_filename=template_filename,
                effective_defaults=effective_defaults
            )

    except (FileNotFoundError, ValueError, IOError, ImportError, Exception) as e:
        logger.error(f"❌ Không thể hoàn tất khởi tạo config do lỗi: {e}")
        raise

    # Launch editor (remains the same)
    if config_file_path:
        launch_editor(logger, config_file_path)

    return True