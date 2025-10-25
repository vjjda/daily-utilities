# Path: utils/core/toml_io.py

"""
Tiện ích I/O thuần túy cho file TOML.
(Internal module, imported by utils/core.py)
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

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

__all__ = ["load_toml_file", "write_toml_file"]

def load_toml_file(path: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Đọc toàn bộ file TOML và trả về một dict.
    Trả về dict rỗng nếu file không tồn tại hoặc lỗi.
    """
    if tomllib is None:
        logger.error("❌ Thiếu thư viện 'tomli' (cần cho Python < 3.11).")
        return {}

    if not path.exists():
        logger.debug(f"File config không tồn tại: {path.name}")
        return {}

    try:
        with open(path, 'rb') as f:
            data = tomllib.load(f)
        logger.debug(f"Đã đọc file TOML: {path.name}")
        return data
    except Exception as e:
        logger.warning(f"⚠️ Không thể đọc file TOML {path.name}: {e}")
        return {}

def write_toml_file(path: Path, data: Dict[str, Any], logger: logging.Logger) -> bool:
    """
    Ghi một dict vào file TOML.
    Trả về True nếu thành công.
    """
    if tomli_w is None:
        logger.error("❌ Thiếu thư viện 'tomli-w' (cần để ghi file).")
        logger.error("   Chạy: pip install tomli-w")
        return False
        
    try:
        with open(path, 'wb') as f:
            tomli_w.dump(data, f)
        logger.debug(f"Đã ghi file TOML: {path.name}")
        return True
    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi ghi file '{path.name}': {e}")
        return False