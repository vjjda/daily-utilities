# Path: modules/zsh_wrapper/zsh_wrapper_helpers.py

"""
Helper logic for zsh_wrapper (zrap).
Handles interactive path resolution (S/I/Q prompts) and validation.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .zsh_wrapper_config import (
    DEFAULT_WRAPPER_RELATIVE_DIR, 
    DEFAULT_WRAPPER_ABSOLUTE_PATH
)

# --- NEW: __all__ definition ---
__all__ = ["resolve_output_path_interactively", "resolve_root_interactively"]
# --- END NEW ---


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
        
    # Determine the default path based on mode
    script_name_without_ext = script_path.stem
    
    if mode == "absolute":
        default_output_path = DEFAULT_WRAPPER_ABSOLUTE_PATH / script_name_without_ext
        logger.warning(f"⚠️ Output path (-o) not specified for 'absolute' mode.")
    else:
        # Use PROJECT_ROOT (từ script entrypoint) để tính toán đường dẫn mặc định
        default_output_path = project_root / DEFAULT_WRAPPER_RELATIVE_DIR / script_name_without_ext
        logger.warning("⚠️ Output path (-o) not specified.")

    selected_output: Optional[Path] = None
    
    logger.warning(f"\n⚠️ Output Path (-o) was not specified.")
    logger.warning(f"   Please select the destination for the Zsh wrapper:")
    
    while selected_output is None:
        # 1. Display options
        print(f"     [S] Use Suggested Path: {default_output_path.as_posix()}")
        print("     [I] Input Custom Path")
        print("     [Q] Quit / Cancel")

        try:
            choice = input("   Enter your choice (S/I/Q): ").lower().strip()
        except (EOFError, KeyboardInterrupt):
            choice = 'q'
        
        if choice == 's':
            selected_output = default_output_path
            logger.info(f"✅ Option [S] selected. Using suggested path: {selected_output.as_posix()}")
            
        elif choice == 'i':
            while True:
                try:
                    # --- MODIFIED: Thêm thông tin về mode vào prompt ---
                    if mode == "relative":
                        prompt_mode_info = " (Mode: relative -> path relative to Project Root/absolute)"
                    elif mode == "absolute":
                        prompt_mode_info = " (Mode: absolute -> full path required)"
                    else:
                        prompt_mode_info = ""
                        
                    custom_path_str = input(f"   Enter custom Output path{prompt_mode_info}: ").strip()
                    # --- END MODIFIED ---

                    if not custom_path_str:
                        print("   Error: Path cannot be empty.")
                        continue

                    custom_path = Path(custom_path_str).expanduser().resolve()
                    
                    parent_dir = custom_path.parent
                    if not parent_dir.exists():
                        logger.error(f"❌ Error: Parent directory of Output path does not exist: {parent_dir.as_posix()}")
                        continue
                    if not parent_dir.is_dir():
                        logger.error(f"❌ Error: Parent path is not a directory: {parent_dir.as_posix()}")
                        continue

                    selected_output = custom_path
                    logger.info(f"✅ Option [I] selected. Using custom path: {selected_output.as_posix()}")
                    break
                except Exception as e:
                    logger.error(f"❌ Error processing path: {e}")
                    
        elif choice == 'q':
            logger.error("❌ Operation cancelled by user.")
            raise sys.exit(0) 
            
        else:
            print("   Invalid choice. Please enter S, I, or Q.")
            
    return selected_output.resolve()


def resolve_root_interactively(
    logger: logging.Logger, 
    fallback_path: Path
) -> Path:
    """
    Handles the S/I/Q interaction for the Project Root if fallback is required.
    Returns the final, resolved, absolute project root path or exits (Q).
    """
    selected_root: Optional[Path] = None

    logger.warning(f"\n⚠️ Project Root (Git Root) was not found automatically.")
    logger.warning(f"   Please select the Project Root for this wrapper:")
    
    while selected_root is None:
        # 1. Display options
        print(f"     [S] Use Suggested Root: {fallback_path.as_posix()} (Script Parent Directory)")
        print("     [I] Input Custom Path")
        print("     [Q] Quit / Cancel")

        try:
            choice = input("   Enter your choice (S/I/Q): ").lower().strip()
        except (EOFError, KeyboardInterrupt):
            choice = 'q'
        
        if choice == 's':
            selected_root = fallback_path
            logger.info(f"✅ Option [S] selected. Using suggested root.")
            
        elif choice == 'i':
            while True:
                try:
                    custom_path_str = input("   Enter custom Project Root path (absolute or relative): ").strip()
                    if not custom_path_str:
                        print("   Error: Path cannot be empty.")
                        continue

                    custom_path = Path(custom_path_str).expanduser().resolve()

                    if not custom_path.exists() or not custom_path.is_dir():
                        logger.error(f"❌ Error: The entered path does not exist or is not a directory: {custom_path.as_posix()}")
                        continue
                    
                    selected_root = custom_path
                    logger.info(f"✅ Option [I] selected. Using custom root: {selected_root.as_posix()}")
                    break
                except Exception as e:
                    logger.error(f"❌ Error processing path: {e}")
                    
        elif choice == 'q':
            logger.error("❌ Operation cancelled by user.")
            raise sys.exit(0) 
            
        else:
            print("   Invalid choice. Please enter S, I, or Q.")
            
    return selected_root.resolve()