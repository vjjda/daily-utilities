# Path: modules/zsh_wrapper/zsh_wrapper_helpers.py

"""
Helper logic for zsh_wrapper (zrap).
Handles interactive path resolution (S/I/Q prompts) and validation.
(Internal module, imported by zsh_wrapper_core)
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Callable, Final

from .zsh_wrapper_config import (
    DEFAULT_WRAPPER_RELATIVE_DIR, 
    DEFAULT_WRAPPER_ABSOLUTE_PATH
)

__all__ = ["resolve_output_path_interactively", "resolve_root_interactively"]

# Định nghĩa type hint cho hàm validator
# (Hàm nhận Path và Logger, trả về bool)
PathValidator = Callable[[Path, logging.Logger], bool]


def _validate_output_path(path: Path, logger: logging.Logger) -> bool:
    """
    Validator cho đường dẫn output (S/I/Q).
    Kiểm tra xem thư mục cha có tồn tại và là thư mục không.
    """
    parent_dir = path.parent
    if not parent_dir.exists():
        logger.error(f"❌ Error: Parent directory of Output path does not exist: {parent_dir.as_posix()}")
        return False
    if not parent_dir.is_dir():
        logger.error(f"❌ Error: Parent path is not a directory: {parent_dir.as_posix()}")
        return False
    return True

def _validate_root_path(path: Path, logger: logging.Logger) -> bool:
    """
    Validator cho đường dẫn Project Root (S/I/Q).
    Kiểm tra xem đường dẫn có tồn tại và là thư mục không.
    """
    if not path.exists() or not path.is_dir():
        logger.error(f"❌ Error: The entered path does not exist or is not a directory: {path.as_posix()}")
        return False
    return True

def _resolve_path_via_prompt(
    logger: logging.Logger,
    prompt_title: str,
    suggested_option_text: str,
    suggested_path: Path,
    custom_input_prompt: str,
    custom_path_validator: PathValidator
) -> Path:
    """
    Xử lý vòng lặp prompt S/I/Q chung để xác định đường dẫn.
    
    Args:
        logger: Logger.
        prompt_title: Tiêu đề hiển thị (ví dụ: "⚠️ Output Path...").
        suggested_option_text: Văn bản cho lựa chọn [S] (ví dụ: "Use Suggested...").
        suggested_path: Đường dẫn cho lựa chọn [S].
        custom_input_prompt: Lời nhắc khi người dùng chọn [I].
        custom_path_validator: Hàm (Path, Logger) -> bool để kiểm tra input [I].

    Returns:
        Đường dẫn (Path) đã được resolve.
    
    Raises:
        SystemExit: Nếu người dùng chọn [Q].
    """
    selected_path: Optional[Path] = None

    logger.warning(f"\n{prompt_title}")
    
    while selected_path is None:
        # 1. Hiển thị lựa chọn
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
            raise sys.exit(0) # Thoát script
            
        else:
            print("   Invalid choice. Please enter S, I, or Q.")
            
    return selected_path.resolve()


def resolve_output_path_interactively(
    logger: logging.Logger,
    script_path: Path,
    output_arg: Optional[Path],
    mode: str,
    project_root: Path
) -> Path:
    """
    Xử lý tương tác S/I/Q cho đường dẫn output (nếu chưa được cung cấp).
    
    Args:
        logger: Logger.
        script_path: Đường dẫn script nguồn (để lấy tên).
        output_arg: Đường dẫn output từ CLI (nếu có).
        mode: 'relative' hoặc 'absolute'.
        project_root: Project root đã xác định.

    Returns:
        Đường dẫn output cuối cùng, đã resolve và tuyệt đối.
    """
    if output_arg is not None:
        # Path đã được cung cấp, chỉ cần resolve
        return output_arg.resolve()
        
    # 1. Chuẩn bị đường dẫn mặc định
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
    else:
        input_prompt = "Enter custom Output path (Mode: absolute -> full path required)"

    # 3. Gọi hàm helper chung
    return _resolve_path_via_prompt(
        logger=logger,
        prompt_title=prompt_title,
        suggested_option_text=suggested_text,
        suggested_path=default_output_path,
        custom_input_prompt=input_prompt,
        custom_path_validator=_validate_output_path # Truyền validator
    )

def resolve_root_interactively(
    logger: logging.Logger, 
    fallback_path: Path
) -> Path:
    """
    Xử lý tương tác S/I/Q cho Project Root (nếu không tìm thấy .git).
    
    Args:
        logger: Logger.
        fallback_path: Đường dẫn dự phòng (thường là thư mục cha của script).

    Returns:
        Đường dẫn project root cuối cùng, đã resolve và tuyệt đối.
    """
    # 1. Chuẩn bị các chuỗi cho prompt
    prompt_title = "⚠️ Project Root (Git Root) was not found automatically.\n   Please select the Project Root for this wrapper:"
    suggested_text = f"Use Suggested Root: {fallback_path.as_posix()} (Script Parent Directory)"
    input_prompt = "Enter custom Project Root path (absolute or relative)"

    # 2. Gọi hàm helper chung
    return _resolve_path_via_prompt(
        logger=logger,
        prompt_title=prompt_title,
        suggested_option_text=suggested_text,
        suggested_path=fallback_path,
        custom_input_prompt=input_prompt,
        custom_path_validator=_validate_root_path # Truyền validator
    )