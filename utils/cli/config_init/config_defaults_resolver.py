# Path: utils/cli/config_init/config_defaults_resolver.py
"""
Resolves the effective default configuration values by merging base defaults
with project-level configurations when applicable.
"""

import logging
from pathlib import Path
from typing import Dict, Any

# Import only necessary core utils
from utils.core import load_project_config_section

__all__ = ["resolve_effective_defaults"]


def resolve_effective_defaults(
    logger: logging.Logger,
    scope: str,
    project_config_filename: str,
    config_section_name: str,
    base_defaults: Dict[str, Any],
    cwd: Path # Pass Current Working Directory
) -> Dict[str, Any]:
    """
    Determines the final default values to use based on scope.
    For 'local' scope, it merges project config section over base defaults.
    For 'project' scope, it just uses the base defaults.
    """
    effective_defaults = base_defaults.copy()

    if scope == "local":
        project_config_path = cwd / project_config_filename
        project_section = load_project_config_section(
            project_config_path, config_section_name, logger
        )
        if project_section:
            logger.debug(
                f"Sử dụng section [{config_section_name}] từ '{project_config_filename}'"
                f" làm cơ sở cho config '{scope}'."
            )
            effective_defaults.update(project_section)
        else:
            logger.debug(
                f"Không tìm thấy section [{config_section_name}] trong '{project_config_filename}',"
                f" sử dụng default gốc cho config '{scope}'."
            )
    # For 'project' scope, effective_defaults is already initialized with base_defaults

    return effective_defaults