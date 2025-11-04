# Path: modules/bootstrap/bootstrap_internal/bootstrap_loader.py
import logging
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None


from utils.core import load_project_config_section, load_text_template

from ..bootstrap_config import CONFIG_SECTION_NAME, TEMPLATE_DIR

__all__ = ["load_template", "load_bootstrap_config", "load_spec_file"]


def load_template(template_name: str) -> str:

    logger = logging.getLogger("BootstrapLoader")
    template_path = TEMPLATE_DIR / template_name

    return load_text_template(template_path, logger)


def load_bootstrap_config(logger: logging.Logger, project_root: Path) -> Dict[str, Any]:
    if tomllib is None:
        logger.error(
            "Lỗi: Cần gói 'toml' (cho Python < 3.11) hoặc 'tomllib' để đọc config."
        )
        sys.exit(1)

    config_path = project_root / ".project.toml"

    return load_project_config_section(config_path, CONFIG_SECTION_NAME, logger)


def load_spec_file(logger: logging.Logger, spec_file_path: Path) -> Dict[str, Any]:
    if tomllib is None:
        logger.error(
            "Lỗi: Cần gói 'toml' (cho Python < 3.11) hoặc 'tomllib' để đọc file spec."
        )
        sys.exit(1)

    try:
        with open(spec_file_path, "rb") as f:
            config = tomllib.load(f)
        return config
    except FileNotFoundError:
        logger.error(f"❌ Lỗi: Không tìm thấy file spec tại: {spec_file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(
            f"❌ Lỗi khi đọc hoặc parse file TOML '{spec_file_path.name}': {e}"
        )
        sys.exit(1)
