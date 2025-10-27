# Path: modules/zsh_wrapper/zsh_wrapper_helpers.py

"""
Helper logic for zsh_wrapper (zrap).
Handles interactive path resolution (S/I/Q prompts) and validation.
"""

import logging
import sys
from pathlib import Path
# --- MODIFIED: Thêm Callable ---
from typing import Optional, Callable
# --- END MODIFIED ---

from .zsh_wrapper_config import (
    DEFAULT_WRAPPER_RELATIVE_DIR, 
    DEFAULT_WRAPPER_ABSOLUTE_PATH
)

# --- NEW: Khai báo __all__ (SỬA LỖI) ---
# Chỉ export các hàm mà entrypoint (scripts/zsh_wrapper.py) cần.
__all__ = ["resolve_output_path_interactively", "resolve_root_interactively"]
# --- END NEW ---

# --- MODIFIED: Thêm typing cho hàm validator ---
# Định nghĩa type hint cho hàm validator
# (Hàm nhận Path và Logger, trả về bool)
PathValidator = Callable[[Path, logging.Logger], bool]
# --- END MODIFIED ---


# --- NEW: Hàm validator cho Output Path ---
def _validate_output_path(path: Path, logger: logging.Logger) -> bool:
    """Validator cho resolve_output_path_interactively."""
    parent_dir = path.parent
    if not parent_dir.exists():
        logger.error(f"❌ Error: Parent directory of Output path does not exist: {parent_dir.as_posix()}")
        return False
    if not parent_dir.is_dir():
        logger.error(f"❌ Error: Parent path is not a directory: {parent_dir.as_posix()}")
        return False
    return True
# --- END NEW ---

# --- NEW: Hàm validator cho Root Path ---
def _validate_root_path(path: Path, logger: logging.Logger) -> bool:
    """Validator cho resolve_root_interactively."""
    if not path.exists() or not path.is_dir():
        logger.error(f"❌ Error: The entered path does not exist or is not a directory: {path.as_posix()}")
        return False
    return True
# --- END NEW ---

# --- NEW: Hàm helper S/I/Q chung ---
def _resolve_path_via_prompt(
    logger: logging.Logger,
    prompt_title: str,
    suggested_option_text: str,
    suggested_path: Path,
    custom_input_prompt: str,
    custom_path_validator: PathValidator
) -> Path:
    """
    Handles the generic S/I/Q prompt loop for resolving a path.
    """
    selected_path: Optional[Path] = None

    logger.warning(f"\n{prompt_title}")
    
    while selected_path is None:
        # 1. Display options
        print(f"     [S] {suggested_option_text}")
        print("     [I] Input Custom Path")
        print("     [Q] Quit / Cancel")

        try:
            choice = input("   Enter your choice (S/I/Q): ").lower().strip()
        except (EOFError, KeyboardInterrupt):
            choice = 'q'
        
        if choice == 's':
            selected_path = suggested_path
            logger.info(f"✅ Option [S] selected. Using suggested path: {selected_path.as_posix()}")
            
        elif choice == 'i':
            while True:
                try:
                    custom_path_str = input(f"   {custom_input_prompt}: ").strip()
                    if not custom_path_str:
                        print("   Error: Path cannot be empty.")
                        continue

                    custom_path = Path(custom_path_str).expanduser().resolve()
                    
                    # Sử dụng hàm validator được truyền vào
                    if custom_path_validator(custom_path, logger):
                        selected_path = custom_path
                        logger.info(f"✅ Option [I] selected. Using custom path: {selected_path.as_posix()}")
                        break
                    else:
                        # Validator tự log lỗi
                        continue
                        
                except Exception as e:
                    logger.error(f"❌ Error processing path: {e}")
                    
        elif choice == 'q':
            logger.error("❌ Operation cancelled by user.")
            raise sys.exit(0) 
            
        else:
            print("   Invalid choice. Please enter S, I, or Q.")
            
    return selected_path.resolve()
# --- END NEW ---


# --- MODIFIED: Hàm gốc được đơn giản hóa ---
def resolve_output_path_interactively(
    logger: logging.Logger,
    script_path: Path,
    output_arg: Optional[Path],
    mode: str,
    project_root: Path
) -> Path:
    """
    Handles the S/I/Q interaction for the output path if it is None.
    Returns the final, resolved, absolute output path or exits (Q).
    """
    if output_arg is not None:
        # Path already provided and expanded by main() caller
        return output_arg.resolve()
        
    # 1. Logic chuẩn bị (vẫn giữ nguyên)
    script_name_without_ext = script_path.stem
    
    if mode == "absolute":
        default_output_path = DEFAULT_WRAPPER_ABSOLUTE_PATH / script_name_without_ext
        logger.warning(f"⚠️ Output path (-o) not specified for 'absolute' mode.")
    else:
        default_output_path = project_root / DEFAULT_WRAPPER_RELATIVE_DIR / script_name_without_ext
        logger.warning("⚠️ Output path (-o) not specified.")

    # 2. Chuẩn bị các chuỗi cho prompt
    prompt_title = "⚠️ Output Path (-o) was not specified.\n   Please select the destination for the Zsh wrapper:"
    suggested_text = f"Use Suggested Path: {default_output_path.as_posix()}"
    
    if mode == "relative":
        input_prompt = "Enter custom Output path (Mode: relative -> path relative to Project Root/absolute)"
    elif mode == "absolute":
        input_prompt = "Enter custom Output path (Mode: absolute -> full path required)"
    else:
        input_prompt = "Enter custom Output path"

    # 3. Gọi hàm helper chung
    return _resolve_path_via_prompt(
        logger=logger,
        prompt_title=prompt_title,
        suggested_option_text=suggested_text,
        suggested_path=default_output_path,
        custom_input_prompt=input_prompt,
        custom_path_validator=_validate_output_path # <-- Truyền validator
    )
# --- END MODIFIED ---


# --- MODIFIED: Hàm gốc được đơn giản hóa ---
def resolve_root_interactively(
    logger: logging.Logger, 
    fallback_path: Path
) -> Path:
    """
    Handles the S/I/Q interaction for the Project Root if fallback is required.
    Returns the final, resolved, absolute project root path or exits (Q).
    """
    # 1. Logic chuẩn bị
    logger.warning(f"\n⚠️ Project Root (Git Root) was not found automatically.")

    # 2. Chuẩn bị các chuỗi cho prompt
    prompt_title = "Please select the Project Root for this wrapper:"
    suggested_text = f"Use Suggested Root: {fallback_path.as_posix()} (Script Parent Directory)"
    input_prompt = "Enter custom Project Root path (absolute or relative)"

    # 3. Gọi hàm helper chung
    return _resolve_path_via_prompt(
        logger=logger,
        prompt_title=prompt_title,
        suggested_option_text=suggested_text,
        suggested_path=fallback_path,
        custom_input_prompt=input_prompt,
        custom_path_validator=_validate_root_path # <-- Truyền validator
    )
# --- END MODIFIED ---