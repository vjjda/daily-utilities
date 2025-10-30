# Path: utils/cli/ui_helpers.py

"""
Các tiện ích giao diện người dùng (UI) chung cho các entrypoint CLI.
Chứa các hàm xử lý prompt (O/R/Q, R/C/Q) và khởi chạy editor.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional, List
import subprocess
import platform
import os
import sys

from utils.core import is_git_repository, find_git_root
from utils.logging_config import log_success 

__all__ = ["prompt_config_overwrite", "launch_editor", "handle_project_root_validation"]

def prompt_config_overwrite(
    logger: logging.Logger,
    item_path: Path,
    item_name: str
) -> Optional[bool]:
    """
    Hỏi người dùng (O/R/Q) khi file/section config đã tồn tại.
    Args:
        logger: Logger.
        item_path: Đường dẫn đến file config.
        item_name: Tên của mục đã tồn tại (ví dụ: "File '.tree.toml'", "Section [cpath]").
    Returns:
        True: Nếu người dùng chọn Overwrite (Ghi đè).
        False: Nếu người dùng chọn Read-only (Chỉ đọc).
        None: Nếu người dùng chọn Quit (Hủy bỏ).
    """
    logger.warning(f"⚠️ {item_name} đã tồn tại trong '{item_path.name}'.")
    logger.warning("   Vui lòng chọn một tùy chọn:")
    logger.warning(f"     [O] Ghi đè (Overwrite): Ghi đè {item_name} bằng nội dung mới và mở file.")
    logger.warning("     [R] Chỉ đọc (Read-only): Chỉ mở file hiện có (không ghi đè).")
    logger.warning("     [Q] Thoát (Quit): Hủy bỏ, không làm gì cả.")

    choice = ""
    while choice not in ('o', 'r', 'q'):
        try:
            choice = input("   Nhập lựa chọn của bạn (O/R/Q): ").lower().strip()
        except (EOFError, KeyboardInterrupt):
            choice = 'q' # Coi như Quit nếu Ctrl+C/Ctrl+D

    if choice == 'o':
        logger.info(f"✅ [Ghi đè] Đã chọn. Đang ghi đè {item_name}...")
        return True # Yêu cầu ghi
    elif choice == 'r':
        logger.info(f"✅ [Chỉ đọc] Đã chọn. Sẽ chỉ mở file.")
        return False # Không ghi
    else: # choice == 'q'
        logger.warning("❌ Hoạt động bị hủy bởi người dùng.")
        return None # Báo hủy

def launch_editor(logger: logging.Logger, file_path: Path) -> None:
    """
    Mở file cấu hình trong editor mặc định một cách an toàn (cross-platform).
    Args:
        logger: Logger.
        file_path: Đường dẫn đến file cần mở.
    """
    system_name = platform.system()
    command: Optional[List[str]] = None

    logger.info(f"Đang mở '{file_path.name}' trong editor mặc định...")

    try:
        if system_name == "Windows":
            startfile = getattr(os, "startfile", None)
            if callable(startfile):
                 startfile(str(file_path))
                 return 
            subprocess.run(["cmd", "/c", "start", "", str(file_path)], check=True)
            return 

        elif system_name == "Darwin": # macOS
            command = ["open", str(file_path)]
        elif system_name == "Linux":
            command = ["xdg-open", str(file_path)]

        if command:
            subprocess.run(command, check=False, capture_output=True)
            return 

        logger.warning(f"⚠️ Hệ điều hành không được hỗ trợ để tự động mở file: {system_name}")

    except Exception as e:
        logger.error(f"❌ Lỗi khi mở file '{file_path.name}': {e}")

    logger.warning(f"⚠️ Không thể tự động mở file. Vui lòng mở thủ công: {file_path.as_posix()}")


def handle_project_root_validation(
    logger: logging.Logger,
    scan_root: Path,
    force_silent: bool = False
) -> Tuple[Optional[Path], str]:
    """
    Xác thực thư mục gốc quét (`scan_root`).
    Nếu không phải là gốc Git, tự động tìm và sử dụng gốc Git nếu có.
    Bỏ qua nếu `force_silent` = True.
    Args:
        logger: Logger.
        scan_root: Thư mục gốc dự kiến để quét.
        force_silent: True để bỏ qua kiểm tra và tương tác (ví dụ: khi có --force).
    Returns:
        Tuple[Optional[Path], str]:
            - `effective_scan_root`: Đường dẫn gốc quét cuối cùng (hoặc None nếu bị hủy).
            - `git_warning_str`: Chuỗi cảnh báo (nếu quét từ thư mục không phải gốc Git).
    """

    effective_scan_root: Optional[Path] = scan_root
    git_warning_str = ""

    # Chỉ chạy logic nếu KHÔNG ở chế độ im lặng
    if force_silent:
        # Nếu im lặng, chỉ cần trả về đường dẫn gốc
        return effective_scan_root, ""

    if not is_git_repository(scan_root):
        # Thử tìm gốc Git ở thư mục cha
        suggested_root = find_git_root(scan_root.parent)

        if suggested_root:
            # --- BỎ QUA PROMPT R/C/Q ---
            # Tự động chọn gốc Git ('R')
            effective_scan_root = suggested_root
            # Log thông báo rõ ràng về việc tự động thay đổi
            log_success(logger, f"✅ Quét từ '{scan_root.name}/'. Tự động sử dụng gốc Git: {suggested_root.as_posix()}")
            # Không cần cảnh báo, vì chúng ta đang dùng gốc Git
            git_warning_str = ""
        
        else:
            # --- Prompt y/N (Vẫn giữ lại để đảm bảo an toàn) ---
            logger.warning(f"⚠️ Không tìm thấy thư mục '.git' trong '{scan_root.name}/' hoặc các thư mục cha.")
            logger.warning(f"   Quét từ một thư mục không phải dự án (như $HOME) có thể chậm hoặc không an toàn.")
            confirmation_prompt = f"   Bạn có chắc muốn quét '{scan_root.as_posix()}'? (y/N): "
            try:
                confirmation = input(confirmation_prompt)
            except (EOFError, KeyboardInterrupt):
                confirmation = 'n'

            if confirmation.lower() != 'y':
                logger.error("❌ Hoạt động bị hủy bởi người dùng.")
                return None, "" # Báo hủy
            else:
                log_success(logger, f"✅ Tiếp tục quét tại thư mục không phải gốc Git: {scan_root.as_posix()}")
                # Chuẩn bị cảnh báo để hiển thị sau
                git_warning_str = f"⚠️ Cảnh báo: Đang chạy từ thư mục không phải gốc Git ('{scan_root.name}/'). Quy tắc .gitignore có thể không đầy đủ."
    else:
        # Là gốc Git, chỉ log thông báo đơn giản
        display_root = "thư mục hiện tại" if scan_root.name == "." else scan_root.as_posix()
        log_success(logger, f"✅ Kho Git hợp lệ. Quét từ gốc: {display_root}")

    # Trả về gốc quét hiệu lực và chuỗi cảnh báo (có thể rỗng)
    return effective_scan_root, git_warning_str