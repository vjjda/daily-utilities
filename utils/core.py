#!/usr/bin/env python
# Path: utils/core.py

import subprocess
from typing import List, Tuple, Union
import logging

Logger = logging.Logger 

def run_command(command: Union[str, List[str]], logger: Logger, description: str = "Thực thi lệnh shell") -> Tuple[bool, str]:
    """
    Thực thi một lệnh shell/hệ thống và ghi log kết quả.
    """
    
    if isinstance(command, str):
        command_list = command.split()
    else:
        command_list = command

    logger.debug(f"Đang chạy lệnh: {' '.join(command_list)}")
    
    try:
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=True, 
            shell=False 
        )
        
        logger.debug(f"Lệnh '{command_list[0]}' hoàn thành. Output:\n{result.stdout.strip()}")
        return True, result.stdout.strip()
        
    except subprocess.CalledProcessError as e:
        error_message = f"Lỗi khi thực thi lệnh '{command_list[0]}'. Lỗi:\n{e.stderr.strip()}"
        logger.error(error_message)
        return False, error_message
        
    except FileNotFoundError:
        # --- DÒNG ĐÃ SỬA ---
        # Đã xóa dấu \ không cần thiết trước $PATH
        error_message = f"Lỗi: Không tìm thấy lệnh '{command_list[0]}'. Hãy đảm bảo nó có trong $PATH."
        # -------------------
        logger.error(error_message)
        return False, error_message