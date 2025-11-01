# Path: modules/zsh_wrapper/zsh_wrapper_helpers.py
import logging
import sys
from pathlib import Path
from typing import Optional, Callable, Final

from .zsh_wrapper_config import (
    DEFAULT_WRAPPER_RELATIVE_DIR,
    DEFAULT_WRAPPER_ABSOLUTE_PATH,
)

__all__ = [
    "resolve_default_output_path", # <-- THÊM MỚI
    "resolve_output_path_interactively",
    "resolve_root_interactively",
]


PathValidator = Callable[[Path, logging.Logger], bool]

# ... (Các hàm _validate_output_path, _validate_root_path, _resolve_path_via_prompt giữ nguyên) ...
# ... (Nội dung các hàm này không thay đổi) ...
def _validate_output_path(path: Path, logger: logging.Logger) -> bool:
    parent_dir = path.parent
    if not parent_dir.exists():
        logger.error(
            f"❌ Error: Parent directory of Output path does not exist: {parent_dir.as_posix()}"
        )
        return False
    if not parent_dir.is_dir():
        logger.error(
            f"❌ Error: Parent path is not a directory: {parent_dir.as_posix()}"
        )
        return False
    return True


def _validate_root_path(path: Path, logger: logging.Logger) -> bool:
    if not path.exists() or not path.is_dir():
        logger.error(
            f"❌ Error: The entered path does not exist or is not a directory: {path.as_posix()}"
        )
        return False
    return True


def _resolve_path_via_prompt(
    logger: logging.Logger,
    prompt_title: str,
    suggested_option_text: str,
    suggested_path: Path,
    custom_input_prompt: str,
    custom_path_validator: PathValidator,
) -> Path:
    selected_path: Optional[Path] = None

    logger.warning(f"\n{prompt_title}")

    while selected_path is None:

        print(f"     [S] {suggested_option_text}")
        print("     [I] Input Custom Path")
        print("     [Q] Quit / Cancel")

        try:
            choice = input("   Enter your choice (S/I/Q): ").lower().strip()
        except (EOFError, KeyboardInterrupt):
            choice = "q"

        if choice == "s":
            selected_path = suggested_path
            logger.info(
                f"✅ Option [S] selected. Using suggested path: {selected_path.as_posix()}"
            )

        elif choice == "i":
            while True:
                try:
                    custom_path_str = input(f"   {custom_input_prompt}: ").strip()
                    if not custom_path_str:
                        print("   Error: Path cannot be empty.")
                        continue

                    custom_path = Path(custom_path_str).expanduser().resolve()

                    if custom_path_validator(custom_path, logger):
                        selected_path = custom_path
                        logger.info(
                            f"✅ Option [I] selected. Using custom path: {selected_path.as_posix()}"
                        )
                        break
                    else:
                        continue

                except Exception as e:
                    logger.error(f"❌ Error processing path: {e}")

        elif choice == "q":
            logger.error("❌ Operation cancelled by user.")
            raise sys.exit(0)

        else:
            print("   Invalid choice. Please enter S, I, or Q.")

    return selected_path.resolve()


# --- HÀM MỚI ---
def resolve_default_output_path(
    tool_name: str,
    mode: str,
    project_root: Path,
) -> Path:
    """
    Xác định đường dẫn output mặc định (không tương tác) dựa trên tên và mode.
    """
    if mode == "absolute":
        return DEFAULT_WRAPPER_ABSOLUTE_PATH / tool_name
    else:
        # Mặc định là 'relative'
        return project_root / DEFAULT_WRAPPER_RELATIVE_DIR / tool_name


# --- HÀM CẬP NHẬT ---
def resolve_output_path_interactively(
    logger: logging.Logger,
    tool_name: str, # <-- Thay script_path bằng tool_name
    output_arg: Optional[Path],
    mode: str,
    project_root: Path,
) -> Path:
    if output_arg is not None:
        return output_arg.resolve()

    # --- START CHANGE ---
    # Tái sử dụng logic xác định đường dẫn mặc định
    default_output_path = resolve_default_output_path(
        tool_name, mode, project_root
    )
    
    if mode == "absolute":
        logger.warning(f"⚠️ Output path (-o) not specified for 'absolute' mode.")
    else:
        logger.warning("⚠️ Output path (-o) not specified.")
    # --- END CHANGE ---

    prompt_title = "⚠️ Output Path (-o) was not specified.\n   Please select the destination for the Zsh wrapper:"
    suggested_text = f"Use Suggested Path: {default_output_path.as_posix()}"

    if mode == "relative":
        input_prompt = "Enter custom Output path (Mode: relative -> path relative to Project Root/absolute)"
    else:
        input_prompt = "Enter custom Output path (Mode: absolute -> full path required)"

    return _resolve_path_via_prompt(
        logger=logger,
        prompt_title=prompt_title,
        suggested_option_text=suggested_text,
        suggested_path=default_output_path,
        custom_input_prompt=input_prompt,
        custom_path_validator=_validate_output_path,
    )


def resolve_root_interactively(logger: logging.Logger, fallback_path: Path) -> Path:
    # ... (Hàm này giữ nguyên)
    prompt_title = "⚠️ Project Root (Git Root) was not found automatically.\n   Please select the Project Root for this wrapper:"
    suggested_text = (
        f"Use Suggested Root: {fallback_path.as_posix()} (Script Parent Directory)"
    )
    input_prompt = "Enter custom Project Root path (absolute or relative)"

    return _resolve_path_via_prompt(
        logger=logger,
        prompt_title=prompt_title,
        suggested_option_text=suggested_text,
        suggested_path=fallback_path,
        custom_input_prompt=input_prompt,
        custom_path_validator=_validate_root_path,
    )