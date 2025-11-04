# Path: utils/cli/config_initializer.py
import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .config_writer import handle_config_init_request

__all__ = ["ConfigInitializer"]


class ConfigInitializer:
    def __init__(
        self,
        logger: logging.Logger,
        module_dir: Path,
        template_filename: str,
        config_filename: str,
        project_config_filename: str,
        config_section_name: str,
        base_defaults: Dict[str, Any],
        project_config_root_key: Optional[str] = None,
    ):
        self.logger = logger
        self.module_dir = module_dir
        self.template_filename = template_filename
        self.config_filename = config_filename
        self.project_config_filename = project_config_filename
        self.config_section_name = config_section_name
        self.base_defaults = base_defaults
        self.project_config_root_key = project_config_root_key

    def check_and_handle_requests(self, args: argparse.Namespace) -> None:
        config_project = getattr(args, "config_project", False)
        config_local = getattr(args, "config_local", False)

        if not (config_project or config_local):
            return

        try:
            config_action_taken = handle_config_init_request(
                logger=self.logger,
                config_project=config_project,
                config_local=config_local,
                module_dir=self.module_dir,
                template_filename=self.template_filename,
                config_filename=self.config_filename,
                project_config_filename=self.project_config_filename,
                config_section_name=self.config_section_name,
                base_defaults=self.base_defaults,
                project_config_root_key=self.project_config_root_key,
            )

            if config_action_taken:
                sys.exit(0)

        except Exception as e:
            self.logger.error(f"❌ Đã xảy ra lỗi khi khởi tạo config: {e}")
            self.logger.debug("Traceback:", exc_info=True)
            sys.exit(1)
