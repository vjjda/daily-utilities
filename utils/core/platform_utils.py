# Path: utils/core/platform_utils.py
import logging
import platform
from pathlib import Path
from typing import List

from .process import run_command

__all__ = ["copy_file_to_clipboard"]


def copy_file_to_clipboard(logger: logging.Logger, file_path: Path) -> bool:
    system = platform.system()

    abs_path = file_path.resolve()
    if not abs_path.exists():
        logger.error(f"❌ Lỗi sao chép Clipboard: File không tồn tại tại {abs_path}")
        return False

    command: List[str] = []
    description = ""

    if system == "Darwin":
        logger.debug("Sử dụng 'osascript' (macOS) để sao chép file...")

        applescript = f'set the clipboard to (POSIX file "{str(abs_path)}")'
        command = ["osascript", "-e", applescript]
        description = "Sao chép file vào clipboard (macOS)"

    elif system == "Windows":
        logger.debug("Sử dụng 'PowerShell' (Windows) để sao chép file...")

        powershell_command = f"Set-Clipboard -Path '{str(abs_path)}'"
        command = ["powershell.exe", "-Command", powershell_command]
        description = "Sao chép file vào clipboard (Windows)"

    else:
        logger.warning(
            f"⚠️ Tính năng sao chép file vào clipboard không được hỗ trợ trên {system}."
        )
        return False

    try:
        success, output = run_command(command, logger, description=description)
        if not success:
            logger.error(f"❌ Lỗi khi chạy lệnh clipboard: {output}")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi sao chép clipboard: {e}")
        return False
