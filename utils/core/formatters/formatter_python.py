# Path: utils/core/formatters/formatter_python.py
"""
Trình định dạng (Formatter) cho mã nguồn Python sử dụng 'black'.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional, List

# Import tiện ích tìm config và chạy lệnh
from ..process import run_command
from ..git import find_file_upwards # (Giả định hàm này sẽ được thêm vào git.py)

__all__ = ["format_python_black"]

def _find_pyproject_toml(start_dir: Path, logger: logging.Logger) -> Optional[Path]:
    """Tìm file pyproject.toml gần nhất bằng cách đi ngược lên."""
    return find_file_upwards("pyproject.toml", start_dir, logger)

def format_python_black(
    code_content: str, 
    logger: logging.Logger,
    file_path: Optional[Path] = None
) -> str:
    """
    Định dạng mã Python bằng 'black', đọc từ stdin và trả về stdout.
    Tự động tìm và sử dụng 'pyproject.toml' nếu 'file_path' được cung cấp.
    """
    logger.debug("Trình định dạng Python (Black) được gọi.")

    # 1. Xây dựng lệnh cơ bản
    command: List[str] = ["black", "--fast", "--quiet", "-"] # Đọc từ stdin
    description: str = "Đang chạy 'black' từ stdin"

    # 2. Tìm cấu hình nếu có đường dẫn file
    if file_path:
        start_dir = file_path.parent
        config_path = _find_pyproject_toml(start_dir, logger)
        if config_path:
            logger.debug(f"Đã tìm thấy cấu hình Black tại: {config_path.as_posix()}")
            command.extend(["--config", str(config_path)])
            description += f" (sử dụng config {config_path.name})"
        else:
            logger.debug("Không tìm thấy pyproject.toml, sử dụng cài đặt Black mặc định.")

    # 3. Chạy lệnh
    try:
        success, output = run_command(
            command,
            logger,
            description=description,
            # Truyền nội dung code vào stdin
            input_content=code_content 
        )

        if success:
            return output # Trả về nội dung đã format
        else:
            # Lỗi (ví dụ: syntax error trong code), Black báo lỗi qua stderr
            logger.warning(f"⚠️ 'black' thất bại. Code có thể chứa lỗi cú pháp. Trả về nội dung gốc.")
            logger.debug(f"Black stderr: {output}")
            return code_content # An toàn: trả về gốc
            
    except FileNotFoundError:
        logger.error("❌ Lỗi: Không tìm thấy lệnh 'black'. Hãy đảm bảo 'black' đã được cài đặt trong $PATH.")
        return code_content # An toàn: trả về gốc
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi chạy 'black': {e}")
        return code_content # An toàn: trả về gốc