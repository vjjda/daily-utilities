# Path: utils/core/process.py

import subprocess
import logging
from typing import List, Tuple, Union, Optional
from pathlib import Path

Logger = logging.Logger

__all__ = ["run_command"]


def run_command(
    command: Union[str, List[str]],
    logger: Logger,
    description: str = "Thực thi lệnh shell",
    cwd: Optional[Path] = None,
    input_content: Optional[str] = None,
) -> Tuple[bool, str]:

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
            input=input_content,
            encoding="utf-8",
        )

        stdout_clean = result.stdout.strip()
        logger.debug(f"Lệnh '{command_list[0]}' thành công. Output:\n{stdout_clean}")
        return True, stdout_clean

    except subprocess.CalledProcessError as e:

        error_details = ""
        if e.stderr:
            error_details = e.stderr.strip()
        if not error_details and e.stdout:
            error_details = e.stdout.strip()

        error_message = f"Lệnh '{command_list[0]}' thất bại. Lỗi:\n{error_details}"
        logger.error(f"❌ {error_message}")

        return False, error_details

    except FileNotFoundError:

        error_message = f"Lỗi: Lệnh '{command_list[0]}' không tìm thấy. Đảm bảo nó nằm trong $PATH của bạn."
        logger.error(f"❌ {error_message}")
        return False, error_message
    except Exception as e:

        error_message = f"Lỗi không mong muốn khi chạy lệnh '{command_list[0]}': {e}"
        logger.error(f"❌ {error_message}")
        logger.debug("Traceback:", exc_info=True)
        return False, error_message