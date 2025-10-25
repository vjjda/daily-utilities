# Path: utils/cli/ui_helpers.py

"""
Tiện ích UI chung cho các entry-point CLI (Typer).
Chứa các hàm xử lý prompt (O/R/Q) và khởi chạy editor.
"""

import logging
from pathlib import Path
# --- FIX: Xóa 'bool' khỏi import ---
# from typing import bool # <-- Dòng này bị xóa
# --- END FIX ---

import typer 

__all__ = ["prompt_config_overwrite", "launch_editor"]

def prompt_config_overwrite(
    logger: logging.Logger, 
    item_path: Path, 
    item_name: str
) -> bool: # <-- Type hint 'bool' vẫn hợp lệ ở đây
    """
    Hỏi người dùng (O/R/Q) khi file/section config đã tồn tại.

    Args:
        logger: Logger để ghi log.
        item_path: Đường dẫn file (ví dụ: .project.toml).
        item_name: Tên của mục (ví dụ: "Section [tree]" hoặc "File .tree.toml").

    Returns:
        bool: True nếu người dùng chọn [O]verwrite.
              False nếu người dùng chọn [R]ead-only.
    
    Raises:
        typer.Exit: Nếu người dùng chọn [Q]uit.
    """
    logger.warning(f"⚠️ {item_name} đã tồn tại trong '{item_path.name}'.")
    logger.warning("   Vui lòng chọn một tùy chọn:")
    logger.warning(f"     [O] Overwrite: Ghi đè {item_name} và mở file.")
    logger.warning("     [R] Read-only: Chỉ mở file (không ghi đè).")
    logger.warning("     [Q] Quit: Hủy bỏ, không làm gì cả.")
    
    choice = ""
    while choice not in ('o', 'r', 'q'):
        try:
            choice = input("   Nhập lựa chọn của bạn (O/R/Q): ").lower().strip()
        except (EOFError, KeyboardInterrupt):
            choice = 'q'
    
    if choice == 'o':
        logger.info(f"✅ [Overwrite] Đã chọn. Đang ghi đè {item_name}...")
        return True # Yêu cầu ghi
    elif choice == 'r':
        logger.info(f"✅ [Read-only] Đã chọn. Sẽ chỉ mở file.")
        return False # Không ghi
    else: # choice == 'q'
        logger.warning("❌ Hoạt động bị hủy bởi người dùng.")
        raise typer.Exit(code=0)

def launch_editor(logger: logging.Logger, file_path: Path) -> None:
    """
    Mở file cấu hình trong editor mặc định một cách an toàn.
    """
    try:
        logger.info(f"Đang mở '{file_path.name}'...")
        typer.launch(str(file_path))
    except Exception as e:
        logger.error(f"❌ Lỗi khi mở file: {e}")
        logger.warning(f"⚠️ Không thể tự động mở file.")