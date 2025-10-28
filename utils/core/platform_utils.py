# Path: utils/core/platform_utils.py
"""
Các tiện ích dành riêng cho nền tảng (macOS, Windows).
(Module nội bộ, được import bởi utils/core)
"""

import logging
import platform
import subprocess # Cần import lại subprocess
from pathlib import Path
from typing import List # Cần import List

# Import run_command từ module cùng cấp
from .process import run_command

__all__ = ["copy_file_to_clipboard"]


def copy_file_to_clipboard(logger: logging.Logger, file_path: Path) -> bool:
    """
    Sao chép chính *file* (không phải nội dung) vào clipboard của hệ thống.
    Hỗ trợ macOS và Windows.

    Args:
        logger: Logger để ghi log.
        file_path: Đường dẫn TUYỆT ĐỐI đến file cần sao chép.

    Returns:
        True nếu thành công, False nếu thất bại hoặc không được hỗ trợ.
    """
    system = platform.system()

    # Đảm bảo đường dẫn là tuyệt đối và tồn tại
    abs_path = file_path.resolve()
    if not abs_path.exists():
        logger.error(f"❌ Lỗi sao chép Clipboard: File không tồn tại tại {abs_path}") #
        return False

    command: List[str] = [] # Khởi tạo kiểu List[str]
    description = ""

    if system == "Darwin": # macOS
        logger.debug("Sử dụng 'osascript' (macOS) để sao chép file...") #
        # AppleScript để đặt file vào clipboard
        applescript = f'set the clipboard to (POSIX file "{str(abs_path)}")'
        command = ["osascript", "-e", applescript]
        description = "Sao chép file vào clipboard (macOS)" #

    elif system == "Windows":
        logger.debug("Sử dụng 'PowerShell' (Windows) để sao chép file...") #
        # PowerShell để đặt file vào clipboard
        # Dùng -Path thay vì -LiteralPath để xử lý đường dẫn chuẩn
        powershell_command = f"Set-Clipboard -Path '{str(abs_path)}'"
        command = ["powershell.exe", "-Command", powershell_command]
        description = "Sao chép file vào clipboard (Windows)" #

    else:
        logger.warning(f"⚠️ Tính năng sao chép file vào clipboard không được hỗ trợ trên {system}.") #
        return False

    try:
        success, output = run_command(
            command,
            logger,
            description=description
        )
        if not success:
            logger.error(f"❌ Lỗi khi chạy lệnh clipboard: {output}") #
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi sao chép clipboard: {e}") #
        return False