#!/usr/bin/env python3
# Path: utils/_process.py

"""
Process Execution Utilities
(Internal module, imported by utils/core.py)
"""

import subprocess
import logging
from typing import List, Tuple, Union

# Type hint for logger
Logger = logging.Logger

# ----------------------------------------------------------------------
# PROCESS EXECUTION
# ----------------------------------------------------------------------

def run_command(command: Union[str, List[str]], logger: Logger, description: str = "Execute shell command") -> Tuple[bool, str]:
    """
    Executes a shell/system command and logs the result.

    Args:
        command: The command to execute (string or list of command parts).
        logger: The configured logger instance.
        description: A user-friendly description for the command (used in logs).

    Returns:
        Tuple (success - True/False, output/error message).
    """
    
    # Ensure command is a list for safer subprocess.run
    if isinstance(command, str):
        command_list = command.split()
    else:
        command_list = command

    logger.debug(f"Running command: {' '.join(command_list)}")
    
    try:
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            check=True, # Will raise CalledProcessError if return code is non-zero
            shell=False # Always False to prevent injection
        )
        
        logger.debug(f"Command '{command_list[0]}' succeeded. Output:\n{result.stdout.strip()}")
        return True, result.stdout.strip()
        
    except subprocess.CalledProcessError as e:
        error_message = f"Command '{command_list[0]}' failed. Error:\n{e.stderr.strip()}"
        logger.error(error_message)
        return False, error_message
        
    except FileNotFoundError:
        error_message = f"Error: Command '{command_list[0]}' not found. Ensure it is in your $PATH."
        logger.error(error_message)
        return False, error_message