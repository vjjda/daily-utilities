# Path: utils/core/platform_utils.py
"""
Platform-specific utilities (macOS, Windows).
(Internal module, imported by utils/core)
"""

import logging
import platform
from pathlib import Path

# Import run_command từ module 'process' anh em
from .process import run_command

__all__ = ["copy_file_to_clipboard"]


def copy_file_to_clipboard(logger: logging.Logger, file_path: Path) -> bool:
    """
    Sao chép chính file (không phải nội dung) vào clipboard của hệ thống.
    
    Args:
        logger: Logger để ghi log.
        file_path: Đường dẫn TUYỆT ĐỐI đến file cần sao chép.

    Returns:
        True nếu thành công, False nếu thất bại.
    """
    system = platform.system()
    
    # Đảm bảo đường dẫn là tuyệt đối
    abs_path = file_path.resolve()
    if not abs_path.exists():
        logger.error(f"❌ Lỗi sao chép Clipboard: File không tồn tại tại {abs_path}")
        return False

    command = []
    description = ""

    if system == "Darwin": # macOS
        logger.debug("Đang dùng 'osascript' (macOS) để sao chép file...")
        # AppleScript để đặt file vào clipboard
        applescript = f'set the clipboard to (POSIX file "{str(abs_path)}")'
        command = ["osascript", "-e", applescript]
        description = "Sao chép file vào clipboard (macOS)"

    elif system == "Windows":
        logger.debug("Đang dùng 'PowerShell' (Windows) để sao chép file...")
        # PowerShell để đặt file vào clipboard
        # Sử dụng -Path (thay vì -LiteralPath) để xử lý đường dẫn chuẩn
        powershell_command = f"Set-Clipboard -Path '{str(abs_path)}'"
        command = ["powershell.exe", "-Command", powershell_command]
        description = "Sao chép file vào clipboard (Windows)"
        
    else:
        logger.warning(f"⚠️ Tính năng sao chép file vào clipboard không được hỗ trợ trên {system}.")
        return False

    try:
        success, output = run_command(
            command, 
            logger, 
            description=description
        )
        if not success:
            logger.error(f"❌ Lỗi khi chạy lệnh clipboard: {output}")
            return False
        return True
        
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi sao chép clipboard: {e}")
        return False