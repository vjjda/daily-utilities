# Path: modules/bootstrap/bootstrap_loader.py
"""
Logic tải file cho module Bootstrap.
(Chịu trách nhiệm đọc template và config files)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

# Import thư viện TOML
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
    except ImportError:
        tomllib = None

# Import hằng số và tiện ích chung
from .bootstrap_config import TEMPLATE_DIR, CONFIG_SECTION_NAME
from utils.core import load_project_config_section, load_text_template

__all__ = [
    "load_template",
    "load_bootstrap_config",
    "load_spec_file"
]


def load_template(template_name: str) -> str:
    """
    Helper: Đọc nội dung từ một file template trong thư mục `bootstrap_templates`.

    Args:
        template_name: Tên file template (ví dụ: "bin_wrapper.zsh.template").

    Returns:
        Nội dung file template dưới dạng string.

    Raises:
        FileNotFoundError, Exception: Nếu không tìm thấy hoặc không đọc được file.
    """
    # Lấy logger tạm vì hàm này có thể được gọi từ nhiều nơi
    logger = logging.getLogger("BootstrapLoader")
    template_path = TEMPLATE_DIR / template_name
    # Tái sử dụng hàm load template chung từ utils.core
    return load_text_template(template_path, logger)

def load_bootstrap_config(
    logger: logging.Logger,
    project_root: Path
) -> Dict[str, Any]:
    """
    Tải section `[bootstrap]` từ file `.project.toml` tại gốc dự án.

    Args:
        logger: Logger.
        project_root: Đường dẫn đến thư mục gốc của dự án.

    Returns:
        Dict chứa cấu hình trong section [bootstrap], hoặc dict rỗng.
    """
    if tomllib is None:
        logger.error("Lỗi: Cần gói 'toml' (cho Python < 3.11) hoặc 'tomllib' để đọc config.") #
        sys.exit(1)

    config_path = project_root / ".project.toml"
    # Tái sử dụng hàm load section config chung từ utils.core
    return load_project_config_section(config_path, CONFIG_SECTION_NAME, logger)

def load_spec_file(
    logger: logging.Logger,
    spec_file_path: Path
) -> Dict[str, Any]:
    """
    Tải và parse nội dung file `*.spec.toml`.

    Args:
        logger: Logger.
        spec_file_path: Đường dẫn đầy đủ đến file `.spec.toml`.

    Returns:
        Dict chứa nội dung đã parse của file spec.

    Raises:
        SystemExit: Nếu thiếu thư viện TOML hoặc không đọc/parse được file.
    """
    if tomllib is None:
        logger.error("Lỗi: Cần gói 'toml' (cho Python < 3.11) hoặc 'tomllib' để đọc file spec.") #
        sys.exit(1)

    try:
        with open(spec_file_path, 'rb') as f:
            config = tomllib.load(f)
        return config
    except FileNotFoundError:
        logger.error(f"❌ Lỗi: Không tìm thấy file spec tại: {spec_file_path}") #
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Lỗi khi đọc hoặc parse file TOML '{spec_file_path.name}': {e}") #
        sys.exit(1)