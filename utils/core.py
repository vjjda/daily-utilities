#!/usr/bin/env python
# Path: utils/core.py

import subprocess
from typing import List, Tuple, Union
import logging

# Lấy logger từ module logging_config (chỉ dùng để type hinting, 
# logger thực tế sẽ được truyền từ script chính)
Logger = logging.Logger 

def run_command(command: Union[str, List[str]], logger: Logger, description: str = "Thực thi lệnh shell") -> Tuple[bool, str]:
    """
    Thực thi một lệnh shell/hệ thống và ghi log kết quả.

    Args:
        command: Lệnh cần thực thi (chuỗi hoặc danh sách các thành phần lệnh).
        logger: Đối tượng logger đã được cấu hình.
        description: Mô tả thân thiện với người dùng cho lệnh.

    Returns:
        Tuple (thành công - True/False, kết quả đầu ra/lỗi).
    """
    
    # Đảm bảo command là danh sách để sử dụng subprocess.run an toàn hơn
    if isinstance(command, str):
        command_list = command.split()
    else:
        command_list = command

    # Ghi log DEBUG chi tiết về lệnh sẽ chạy
    logger.debug(f"Đang chạy lệnh: {' '.join(command_list)}")
    
    try:
        # Chạy lệnh
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=True, # Sẽ raise CalledProcessError nếu mã trả về khác 0
            shell=False # Luôn False để tránh injection, trừ khi dùng shell=True và command là string
        )
        
        # Ghi log thành công
        logger.debug(f"Lệnh '{command_list[0]}' hoàn thành. Output:\n{result.stdout.strip()}")
        return True, result.stdout.strip()
        
    except subprocess.CalledProcessError as e:
        # Ghi log lỗi nếu lệnh thất bại (exit code khác 0)
        error_message = f"Lỗi khi thực thi lệnh '{command_list[0]}'. Lỗi:\n{e.stderr.strip()}"
        logger.error(error_message)
        return False, error_message
        
    except FileNotFoundError:
        error_message = f"Lỗi: Không tìm thấy lệnh '{command_list[0]}'. Hãy đảm bảo nó có trong \$PATH."
        logger.error(error_message)
        return False, error_message

# Thêm các hàm tiện ích khác ở đây (ví dụ: file_handling, config_reader)
