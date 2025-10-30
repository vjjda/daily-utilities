# Path: utils/cli/ui_helpers.py

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
    logger: logging.Logger, item_path: Path, item_name: str
) -> Optional[bool]:
    logger.warning(f"⚠️ {item_name} đã tồn tại trong '{item_path.name}'.")
    logger.warning("   Vui lòng chọn một tùy chọn:")
    logger.warning(
        f"     [O] Ghi đè (Overwrite): Ghi đè {item_name} bằng nội dung mới và mở file."
    )
    logger.warning("     [R] Chỉ đọc (Read-only): Chỉ mở file hiện có (không ghi đè).")
    logger.warning("     [Q] Thoát (Quit): Hủy bỏ, không làm gì cả.")

    choice = ""
    while choice not in ("o", "r", "q"):
        try:
            choice = input("   Nhập lựa chọn của bạn (O/R/Q): ").lower().strip()
        except (EOFError, KeyboardInterrupt):
            choice = "q"

    if choice == "o":
        logger.info(f"✅ [Ghi đè] Đã chọn. Đang ghi đè {item_name}...")
        return True
    elif choice == "r":
        logger.info(f"✅ [Chỉ đọc] Đã chọn. Sẽ chỉ mở file.")
        return False
    else:
        logger.warning("❌ Hoạt động bị hủy bởi người dùng.")
        return None


def launch_editor(logger: logging.Logger, file_path: Path) -> None:
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

        elif system_name == "Darwin":
            command = ["open", str(file_path)]
        elif system_name == "Linux":
            command = ["xdg-open", str(file_path)]

        if command:

            subprocess.run(command, check=False, capture_output=True)
            return

        logger.warning(
            f"⚠️ Hệ điều hành không được hỗ trợ để tự động mở file: {system_name}"
        )

    except Exception as e:
        logger.error(f"❌ Lỗi khi mở file '{file_path.name}': {e}")

    logger.warning(
        f"⚠️ Không thể tự động mở file. Vui lòng mở thủ công: {file_path.as_posix()}"
    )


def handle_project_root_validation(
    logger: logging.Logger, scan_root: Path, force_silent: bool = False
) -> Tuple[Optional[Path], str]:

    effective_scan_root: Optional[Path] = scan_root
    git_warning_str = ""

    if not force_silent:
        if not is_git_repository(scan_root):

            suggested_root = find_git_root(scan_root.parent)

            if suggested_root:

                logger.warning(
                    f"⚠️ Thư mục quét '{scan_root.name}/' không phải là gốc Git."
                )
                logger.warning(
                    f"   Đã tìm thấy gốc Git tại: {suggested_root.as_posix()}"
                )
                logger.warning("   Vui lòng chọn một tùy chọn:")
                logger.warning("     [R] Chạy từ Gốc Git (Khuyên dùng)")
                logger.warning(f"     [C] Chạy từ Thư mục Hiện tại ({scan_root.name}/)")
                logger.warning("     [Q] Thoát / Hủy")
                choice = ""
                while choice not in ("r", "c", "q"):
                    try:
                        choice = (
                            input("   Nhập lựa chọn của bạn (R/C/Q): ").lower().strip()
                        )
                    except (EOFError, KeyboardInterrupt):
                        choice = "q"

                if choice == "r":
                    effective_scan_root = suggested_root
                    log_success(
                        logger,
                        f"✅ Di chuyển quét đến gốc Git: {suggested_root.as_posix()}",
                    )
                elif choice == "c":
                    effective_scan_root = scan_root
                    log_success(
                        logger, f"✅ Quét từ thư mục hiện tại: {scan_root.as_posix()}"
                    )

                    git_warning_str = f"⚠️ Cảnh báo: Đang chạy từ thư mục không phải gốc Git ('{scan_root.name}/'). Quy tắc .gitignore có thể không đầy đủ."
                elif choice == "q":
                    logger.error("❌ Hoạt động bị hủy bởi người dùng.")
                    return None, ""
            else:

                logger.warning(
                    f"⚠️ Không tìm thấy thư mục '.git' trong '{scan_root.name}/' hoặc các thư mục cha."
                )
                logger.warning(
                    f"   Quét từ một thư mục không phải dự án (như $HOME) có thể chậm hoặc không an toàn."
                )
                confirmation_prompt = (
                    f"   Bạn có chắc muốn quét '{scan_root.as_posix()}'? (y/N): "
                )
                try:
                    confirmation = input(confirmation_prompt)
                except (EOFError, KeyboardInterrupt):
                    confirmation = "n"

                if confirmation.lower() != "y":
                    logger.error("❌ Hoạt động bị hủy bởi người dùng.")
                    return None, ""
                else:
                    log_success(
                        logger,
                        f"✅ Tiếp tục quét tại thư mục không phải gốc Git: {scan_root.as_posix()}",
                    )

                    git_warning_str = f"⚠️ Cảnh báo: Đang chạy từ thư mục không phải gốc Git ('{scan_root.name}/'). Quy tắc .gitignore có thể không đầy đủ."
        else:

            display_root = (
                scan_root.resolve().as_posix()
                if scan_root.name == "."
                else scan_root.as_posix()
            )
            log_success(logger, f"✅ Kho Git hợp lệ. Quét từ gốc: {display_root}")

    return effective_scan_root, git_warning_str