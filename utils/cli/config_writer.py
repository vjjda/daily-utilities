# Path: utils/cli/config_writer.py

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys


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


from .config_init import (
    resolve_effective_defaults,
    generate_config_content,
    write_local_config,
    write_project_config_section,
)


from .ui_helpers import launch_editor

__all__ = ["handle_config_init_request"]


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

    toml_read_lib_missing = tomllib is None
    toml_write_lib_missing = tomlkit is None and config_project

    lib_missing = False
    if toml_read_lib_missing:
        logger.error("❌ Thiếu thư viện đọc TOML ('tomllib' hoặc 'toml').")
        lib_missing = True
    if toml_write_lib_missing:
        logger.error("❌ Thiếu thư viện ghi TOML ('tomlkit') cần cho scope 'project'.")
        lib_missing = True

    if lib_missing:
        logger.error(
            "   Vui lòng cài đặt thư viện còn thiếu (ví dụ: pip install tomlkit toml)."
        )
        sys.exit("Thiếu thư viện TOML cần thiết.")

    scope = "project" if config_project else "local"
    logger.info(f"Yêu cầu khởi tạo cấu hình scope '{scope}'...")
    cwd = Path.cwd()

    try:
        effective_defaults = resolve_effective_defaults(
            logger=logger,
            scope=scope,
            project_config_filename=project_config_filename,
            config_section_name=config_section_name,
            base_defaults=base_defaults,
            cwd=cwd,
        )

        config_content_string = generate_config_content(
            logger=logger,
            module_dir=module_dir,
            template_filename=template_filename,
            config_section_name=config_section_name,
            effective_defaults=effective_defaults,
        )

        config_file_path: Optional[Path] = None
        if scope == "local":
            target_path = cwd / config_filename
            config_file_path = write_local_config(
                logger=logger,
                config_file_path=target_path,
                content_from_template=config_content_string,
            )
        elif scope == "project":
            target_path = cwd / project_config_filename
            config_file_path = write_project_config_section(
                logger=logger,
                config_file_path=target_path,
                config_section_name=config_section_name,
                new_section_content_string=config_content_string,
            )

        if config_file_path:
            launch_editor(logger, config_file_path)

        return True

    except (FileNotFoundError, ValueError, IOError, ImportError, Exception) as e:
        logger.error(f"❌ Không thể hoàn tất khởi tạo config do lỗi: {e}")
        raise