# Path: utils/core/toml_io.py

"""
Các tiện ích I/O thuần túy cho file TOML.
(Module nội bộ, được import bởi utils/core)

Sử dụng `tomllib` (Python 3.11+) hoặc fallback về `toml` (nếu cài) để đọc,
và `tomli_w` để ghi.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Cố gắng import thư viện đọc TOML
try:
    import tomllib # Chuẩn Python 3.11+
except ImportError:
    try:
        import toml as tomllib # Thư viện bên thứ ba phổ biến
    except ImportError:
        tomllib = None # Không có thư viện nào

# Cố gắng import thư viện ghi TOML
try:
    import tomli_w
except ImportError:
    tomli_w = None

__all__ = ["load_toml_file", "write_toml_file"]

def load_toml_file(path: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Đọc toàn bộ file TOML và trả về một dict.
    Trả về dict rỗng nếu file không tồn tại, không đọc được,
    hoặc thiếu thư viện đọc TOML.

    Args:
        path: Đường dẫn đến file TOML.
        logger: Logger để ghi log.

    Returns:
        Dict chứa dữ liệu từ file TOML, hoặc dict rỗng.
    """
    if tomllib is None:
        logger.error("❌ Thiếu thư viện đọc TOML ('tomllib' hoặc 'toml'). Cần cho Python < 3.11.") #
        return {}

    if not path.exists():
        logger.debug(f"File config không tồn tại, bỏ qua: {path.name}") #
        return {}

    try:
        with open(path, 'rb') as f: # Mở ở chế độ binary theo yêu cầu của tomllib
            data = tomllib.load(f)
        logger.debug(f"Đã đọc file TOML: {path.name}") #
        return data
    except Exception as e:
        logger.warning(f"⚠️ Không thể đọc hoặc phân tích file TOML {path.name}: {e}") #
        return {}

def write_toml_file(path: Path, data: Dict[str, Any], logger: logging.Logger) -> bool:
    """
    Ghi một dict vào file TOML.

    Args:
        path: Đường dẫn đến file TOML cần ghi.
        data: Dict dữ liệu cần ghi.
        logger: Logger để ghi log.

    Returns:
        True nếu ghi thành công, False nếu thất bại (thiếu thư viện hoặc lỗi I/O).
    """
    if tomli_w is None:
        logger.error("❌ Thiếu thư viện ghi TOML ('tomli_w').") #
        logger.error("   Vui lòng chạy: pip install tomli-w") #
        return False

    try:
        with open(path, 'wb') as f: # Mở ở chế độ binary theo yêu cầu của tomli_w
            tomli_w.dump(data, f)
        logger.debug(f"Đã ghi file TOML: {path.name}") #
        return True
    except IOError as e:
        logger.error(f"❌ Lỗi I/O khi ghi file '{path.name}': {e}") #
        return False
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi ghi file TOML '{path.name}': {e}") #
        return False