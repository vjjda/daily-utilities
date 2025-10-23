# Path: utils/core.py

import subprocess
import logging
import configparser
import fnmatch
import os
from pathlib import Path
from typing import List, Tuple, Union, Set, Optional

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

# ----------------------------------------------------------------------
# FILE SYSTEM & CONFIG UTILITIES (NEW)
# ----------------------------------------------------------------------

def is_git_repository(root: Path) -> bool:
    """Checks if the given root path is the root of a Git repository."""
    return (root / ".git").is_dir()

# --- NEW FUNCTION: Tìm kiếm thư mục Git Root ---
def find_git_root(start_path: Path, max_levels: int = 5) -> Optional[Path]:
    """
    Traverses up the directory tree (up to max_levels) to find the nearest
    Git repository root (a directory containing a .git folder).

    Args:
        start_path: The path to begin searching from.
        max_levels: The maximum number of parent directories to check.

    Returns:
        The Path object of the Git root, or None if not found.
    """
    current_path = start_path.resolve()
    for _ in range(max_levels):
        if is_git_repository(current_path):
            return current_path
        
        # Dừng nếu đã đến thư mục gốc của hệ thống (root)
        if current_path == current_path.parent:
            break
            
        current_path = current_path.parent
        
    return None
# --- END NEW FUNCTION ---

def get_submodule_paths(root: Path, logger: Optional[logging.Logger] = None) -> Set[Path]: # <--- THAY ĐỔI KIỂU TRẢ VỀ
    """Gets submodule directory full paths based on the .gitmodules file."""
    submodule_paths = set()
    gitmodules_path = root / ".gitmodules"
    if gitmodules_path.exists():
        try:
            config = configparser.ConfigParser()
            config.read(gitmodules_path)
            for section in config.sections():
                if config.has_option(section, "path"):
                    path_str = config.get(section, "path")
                    # --- THAY ĐỔI LOGIC ---
                    # Trả về đường dẫn đầy đủ, đã giải quyết
                    submodule_paths.add((root / path_str).resolve())
                    # --------------------
        except configparser.Error as e:
            warning_msg = f"Could not parse .gitmodules file: {e}"
            if logger:
                logger.warning(f"⚠️ {warning_msg}")
            else:
                print(f"Warning: {warning_msg}") 
    return submodule_paths

def is_path_matched(path: Path, patterns: Set[str], start_dir: Path) -> bool:
    """Checks if a path matches any pattern (using fnmatch for name or relative path)."""
    if not patterns: 
        return False
    
    relative_path = path.relative_to(start_dir)
    relative_path_str = relative_path.as_posix()
    
    # --- FIX: Lấy tất cả các phần của đường dẫn ---
    # Ví dụ: Path('a/b/c.txt') -> ('a', 'b', 'c.txt')
    path_parts = relative_path.parts 

    for pattern in patterns: 
        # Check 1: Match full relative path (e.g., 'docs/drafts', 'build/')
        if fnmatch.fnmatch(relative_path_str, pattern):
            return True
        
        # Check 2: Match just the name (e.g., '.DS_Store', '*.log')
        if fnmatch.fnmatch(path.name, pattern):
            return True

        # Check 3 (FIX): Match any part of the path (e.g., '.venv', 'build')
        # Điều này xử lý khi 'build' nằm trong .gitignore và chúng ta đang kiểm tra 'build/main.py'
        if any(fnmatch.fnmatch(part, pattern) for part in path_parts):
            return True
            
    return False

def parse_comma_list(value: Union[str, None]) -> Set[str]:
    """Converts a comma-separated string into a set of stripped items."""
    if not value: 
        return set()
    return {item.strip() for item in value.split(',') if item.strip() != ''}

def parse_gitignore(root: Path) -> Set[str]:
    """Parses a .gitignore file and returns a set of non-empty, non-comment patterns."""
    gitignore_path = root / ".gitignore"
    patterns = set()
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith('#'):
                        patterns.add(stripped_line)
        except Exception as e:
            # We don't use logger here as this might be called before logging is set up
            print(f"Warning: Could not read .gitignore file: {e}")
    return patterns