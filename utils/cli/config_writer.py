# Path: utils/cli/config_writer.py
"""
Orchestrator for configuration file initialization/update logic.
Coordinates default resolution, content generation, and file writing.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys # Needed for sys.exit() if libs are missing

# Check for necessary libraries early
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

# Import refactored components
from .config_defaults_resolver import resolve_effective_defaults
from .config_content_generator import generate_config_content
from .config_writer_local import write_local_config
from .config_writer_project import write_project_config_section

# Import UI helpers
from .ui_helpers import launch_editor

__all__ = ["handle_config_init_request"]


def handle_config_init_request(
    logger: logging.Logger,
    config_project: bool,
    config_local: bool,
    # Template and config file info
    module_dir: Path,
    template_filename: str,
    config_filename: str,
    project_config_filename: str,
    config_section_name: str,
    # Default data
    base_defaults: Dict[str, Any]
) -> bool:
    """
    Orchestrates the config file creation/update process by calling
    specialized helper modules.
    """
    if not (config_project or config_local):
        return False # No config flag provided

    # --- Library Checks ---
    toml_read_lib_missing = tomllib is None
    # For project scope, tomlkit is essential for writing
    toml_write_lib_missing = tomlkit is None and config_project

    lib_missing = False
    if toml_read_lib_missing:
         logger.error("❌ Thiếu thư viện đọc TOML ('tomllib' hoặc 'toml').")
         lib_missing = True
    if toml_write_lib_missing:
         logger.error("❌ Thiếu thư viện ghi TOML ('tomlkit') cần cho scope 'project'.")
         lib_missing = True

    if lib_missing:
        logger.error("   Vui lòng cài đặt thư viện còn thiếu (ví dụ: pip install tomlkit toml).")
        # Exit here as core functionality is missing
        sys.exit("Thiếu thư viện TOML cần thiết.")

    scope = 'project' if config_project else 'local'
    logger.info(f"Yêu cầu khởi tạo cấu hình scope '{scope}'...")
    cwd = Path.cwd() # Get current working directory once

    try:
        # 1. Resolve Defaults
        effective_defaults = resolve_effective_defaults(
            logger=logger,
            scope=scope,
            project_config_filename=project_config_filename,
            config_section_name=config_section_name,
            base_defaults=base_defaults,
            cwd=cwd
        )

        # 2. Generate Content String (common for both scopes now)
        # This content includes comments and handles None values appropriately
        config_content_string = generate_config_content(
            logger=logger,
            module_dir=module_dir,
            template_filename=template_filename,
            config_section_name=config_section_name,
            effective_defaults=effective_defaults
        )

        # 3. Call appropriate Writer
        config_file_path: Optional[Path] = None
        if scope == "local":
            target_path = cwd / config_filename
            config_file_path = write_local_config(
                logger=logger,
                config_file_path=target_path,
                content_from_template=config_content_string
            )
        elif scope == "project":
            target_path = cwd / project_config_filename
            config_file_path = write_project_config_section(
                logger=logger,
                config_file_path=target_path,
                config_section_name=config_section_name,
                # Pass the generated string content for the section
                new_section_content_string=config_content_string
            )

        # 4. Launch Editor (if write was successful and not cancelled)
        if config_file_path:
            launch_editor(logger, config_file_path)

        # Return True if action was taken (even if cancelled during prompt)
        return True

    except (FileNotFoundError, ValueError, IOError, ImportError, Exception) as e:
        # Errors from helpers should be caught here
        logger.error(f"❌ Không thể hoàn tất khởi tạo config do lỗi: {e}")
        # Re-raise to signal failure to the entry point
        raise