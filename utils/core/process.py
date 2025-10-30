# Path: utils/core/process.py
"""
Các tiện ích thực thi tiến trình hệ thống.
(Module nội bộ, được import bởi utils/core)
"""

import subprocess
import logging
from typing import List, Tuple, Union, Optional
from pathlib import Path

Logger = logging.Logger # Type hint alias

__all__ = ["run_command"]

def run_command(
    command: Union[str, List[str]],
    logger: Logger,
    description: str = "Thực thi lệnh shell",
    cwd: Optional[Path] = None,
    input_content: Optional[str] = None # <-- THÊM THAM SỐ MỚI
) -> Tuple[bool, str]:
    """
    Thực thi một lệnh hệ thống/shell và ghi log kết quả.
    Args:
        command: Lệnh dưới dạng chuỗi hoặc list các thành phần lệnh.
        logger: Logger để ghi log.
        description: Mô tả ngắn gọn về mục đích của lệnh (để log).
        cwd: Thư mục làm việc hiện tại (current working directory) để chạy lệnh.
             Mặc định là None (sử dụng thư mục của tiến trình Python).

    Returns:
        Tuple[bool, str]:
            - bool: True nếu lệnh thành công (exit code 0), False nếu thất bại.
            - str: Nội dung stdout (nếu thành công) hoặc stderr/stdout (nếu thất bại).
                   Đã được strip() khoảng trắng thừa.
    """

    if isinstance(command, str):
        command_list = command.split()
    else:
        command_list = command

    cwd_info = f" (trong {cwd})" if cwd else ""
    stdin_info = " (với input stdin)" if input_content is not None else ""
    logger.debug(f"Đang chạy lệnh{cwd_info}{stdin_info}: {' '.join(command_list)}")

    try:
        result = subprocess.run(
    command_list,
            capture_output=True,
            text=True,
            check=True,
    shell=False,
            cwd=cwd,
            input=input_content, # <-- TRUYỀN input
            encoding='utf-8' # <-- Chỉ định rõ encoding cho input/output
        )

        stdout_clean = result.stdout.strip()
        logger.debug(f"Lệnh '{command_list[0]}' thành công. Output:\n{stdout_clean}")
        return True, stdout_clean

    except subprocess.CalledProcessError as e:
        # Lỗi do exit code != 0
        error_details = ""
        if e.stderr:
            error_details = e.stderr.strip()
        if not error_details and e.stdout:
            error_details = e.stdout.strip()

        error_message = f"Lệnh '{command_list[0]}' thất bại. Lỗi:\n{error_details}" #
        logger.error(f"❌ {error_message}") #

        return False, error_details

    except FileNotFoundError:
        # Lỗi do không tìm thấy file thực thi (lệnh không có trong PATH)
        error_message = f"Lỗi: Lệnh '{command_list[0]}' không tìm thấy. Đảm bảo nó nằm trong $PATH của bạn." #
        logger.error(f"❌ {error_message}") #
        return False, error_message
    except Exception as e:
        # Bắt các lỗi không mong muốn khác
        error_message = f"Lỗi không mong muốn khi chạy lệnh '{command_list[0]}': {e}" #
        logger.error(f"❌ {error_message}") #
        logger.debug("Traceback:", exc_info=True)
        return False, error_message