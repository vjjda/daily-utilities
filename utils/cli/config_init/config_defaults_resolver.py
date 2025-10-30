# Path: utils/cli/config_init/config_defaults_resolver.py

import logging
from pathlib import Path
from typing import Dict, Any


from utils.core import load_project_config_section

__all__ = ["resolve_effective_defaults"]


def resolve_effective_defaults(
    logger: logging.Logger,
    scope: str,
    project_config_filename: str,
    config_section_name: str,
    base_defaults: Dict[str, Any],
    cwd: Path,
) -> Dict[str, Any]:
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

    return effective_defaults