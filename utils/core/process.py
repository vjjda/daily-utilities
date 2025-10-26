# Path: utils/core/process.py

"""
Process Execution Utilities
(Internal module, imported by utils/core.py)
"""

import subprocess
import logging
from typing import List, Tuple, Union, Optional
from pathlib import Path

Logger = logging.Logger

__all__ = ["run_command"]

# ----------------------------------------------------------------------
# PROCESS EXECUTION
# ----------------------------------------------------------------------

def run_command(
    command: Union[str, List[str]], 
    logger: Logger, 
    description: str = "Execute shell command",
    cwd: Optional[Path] = None 
) -> Tuple[bool, str]:
    """
    Executes a shell/system command and logs the result.
    (Code moved from utils/core.py)
    """
    
    if isinstance(command, str):
        command_list = command.split()
    else:
        command_list = command

    cwd_info = f" (in {cwd})" if cwd else ""
    logger.debug(f"Running command{cwd_info}: {' '.join(command_list)}")
    
    try:
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=True, 
            shell=False, 
            cwd=cwd 
        )
        
        logger.debug(f"Command '{command_list[0]}' succeeded. Output:\n{result.stdout.strip()}")
        return True, result.stdout.strip()
        
    except subprocess.CalledProcessError as e:
        # --- MODIFIED: Đảm bảo nắm bắt chi tiết lỗi ---
        error_details = ""
        if e.stderr:
            error_details = e.stderr.strip()
        if not error_details and e.stdout: # Nếu stderr rỗng, thử stdout
            error_details = e.stdout.strip()
        # --- END MODIFIED ---

        error_message = f"Command '{command_list[0]}' failed. Error:\n{error_details}"
        logger.error(error_message)
        
        # --- MODIFIED: Trả về chi tiết lỗi (thay vì message) ---
        # Điều này rất quan trọng để logic trong _handle_git_commit
        # có thể đọc được "nothing to commit"
        return False, error_details
        # --- END MODIFIED ---
        
    except FileNotFoundError:
        error_message = f"Error: Command '{command_list[0]}' not found. Ensure it is in your $PATH."
        logger.error(error_message)
        return False, error_message