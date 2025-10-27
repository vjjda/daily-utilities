# Path: utils/cli/ui_helpers.py

"""
Tiện ích UI chung cho các entry-point CLI (Typer).
Chứa các hàm xử lý prompt (O/R/Q) và khởi chạy editor.
"""

import logging
from pathlib import Path
# --- MODIFIED: Thêm imports ---
from typing import Tuple, Optional, List # <-- Thêm List
import subprocess 
import platform 
import os 
import sys # <-- THÊM LẠI
# --- END MODIFIED ---

# Import các tiện ích core cần thiết cho hàm mới
from utils.core import is_git_repository, find_git_root

__all__ = ["prompt_config_overwrite", "launch_editor", "handle_project_root_validation"]

# ... (Hàm prompt_config_overwrite giữ nguyên) ...

def launch_editor(logger: logging.Logger, file_path: Path) -> None:
    """
    Mở file cấu hình trong editor mặc định một cách an toàn (cross-platform).
    """
    system_name = platform.system()
    command: Optional[List[str]] = None
    
    # --- MODIFIED: Logic mở file cho Windows (Khắc phục Pylance và thêm Fallback) ---
    if system_name == "Windows":
        # Sử dụng os.startfile trên Windows nếu có, nếu không thì fallback sang cmd start
        try:
            startfile = getattr(os, "startfile", None) # <-- Khắc phục lỗi Pylance
            if callable(startfile):
                startfile(str(file_path))
                logger.info(f"Đang mở '{file_path.name}'...")
                return
            
            # Fallback: use cmd's start (works when startfile is unavailable)
            # Dùng check=True vì đây là lệnh cuối cùng để mở file
            subprocess.run(["cmd", "/c", "start", "", str(file_path)], check=True)
            logger.info(f"Đang mở '{file_path.name}'...")
            return
        except Exception:
            pass # Thất bại trên Windows
    # --- END MODIFIED ---

    elif system_name == "Darwin": # macOS
        command = ["open", str(file_path)]
    elif system_name == "Linux":
        command = ["xdg-open", str(file_path)]
    
    try:
        if command:
            logger.info(f"Đang mở '{file_path.name}'...")
            # Run command, suppress output
            subprocess.run(command, check=False, capture_output=True)
            return
        else:
            logger.warning(f"⚠️ Hệ điều hành không được hỗ trợ để tự động mở file: {system_name}")
    except Exception as e:
        logger.error(f"❌ Lỗi khi mở file: {e}")
        logger.warning(f"⚠️ Không thể tự động mở file. Vui lòng mở thủ công: {file_path.as_posix()}")

# --- NEW: Hàm xác thực Project Root (R/C/Q) ---
def handle_project_root_validation(
    logger: logging.Logger,
    scan_root: Path,
    force_silent: bool = False
) -> Tuple[Optional[Path], str]:
    """
    Xác thực gốc quét (scan_root). 
    Nếu không phải là Git root, chạy logic tương tác (R/C/Q hoặc y/N).
    Bỏ qua nếu force_silent = True.

    Returns:
        Tuple[Optional[Path], str]: (effective_scan_root, git_warning_str)
        Trả về (None, "") nếu người dùng chọn Quit.
    """
    
    effective_scan_root: Optional[Path] = scan_root
    git_warning_str = ""
    
    # Chỉ chạy logic tương tác nếu KHÔNG ở chế độ im lặng
    if not force_silent:
        if not is_git_repository(scan_root):
            suggested_root = find_git_root(scan_root.parent)
            
            if suggested_root:
                logger.warning(f"⚠️ Thư mục quét '{scan_root.name}/' không phải là gốc Git.")
                logger.warning(f"   Đã tìm thấy gốc Git tại: {suggested_root.as_posix()}")
                logger.warning("   Vui lòng chọn một tùy chọn:")
                logger.warning("     [R] Chạy từ Gốc Git (Khuyên dùng)")
                logger.warning(f"     [C] Chạy từ Thư mục Hiện tại ({scan_root.name}/)")
                logger.warning("     [Q] Thoát / Hủy")
                choice = ""
                while choice not in ('r', 'c', 'q'):
                    try:
                        choice = input("   Nhập lựa chọn của bạn (R/C/Q): ").lower().strip()
                    except (EOFError, KeyboardInterrupt):
                        choice = 'q'
                
                if choice == 'r':
                    effective_scan_root = suggested_root
                    # --- FIX (Theo gợi ý của bạn): Dùng suggested_root ---
                    logger.info(f"✅ Di chuyển quét đến gốc Git: {suggested_root.as_posix()}")
                elif choice == 'c':
                    effective_scan_root = scan_root
                    logger.info(f"✅ Quét từ thư mục hiện tại: {scan_root.as_posix()}")
                    git_warning_str = f"⚠️ Cảnh báo: Đang chạy từ thư mục không phải gốc Git ('{scan_root.name}/'). Quy tắc .gitignore có thể không đầy đủ."
                elif choice == 'q':
                    logger.error("❌ Hoạt động bị hủy bởi người dùng.")
                    return None, ""
            
            else:
                logger.warning(f"⚠️ Không tìm thấy thư mục '.git' trong '{scan_root.name}/' hoặc các thư mục cha.")
                logger.warning(f"   Quét từ một thư mục không phải dự án (như $HOME) có thể chậm hoặc không an toàn.")
                
                # --- FIX (Như lần trước): Tách f-string khỏi input() ---
                confirmation_prompt = f"   Bạn có chắc muốn quét '{scan_root.as_posix()}'? (y/N): "
                try:
                    confirmation = input(confirmation_prompt)
                # --- END FIX ---
                except (EOFError, KeyboardInterrupt):
                    confirmation = 'n'
                
                if confirmation.lower() != 'y':
                    logger.error("❌ Hoạt động bị hủy bởi người dùng.")
                    return None, ""
                else:
                    logger.info(f"✅ Tiếp tục quét tại thư mục không phải gốc Git: {scan_root.as_posix()}")
                    git_warning_str = f"⚠️ Cảnh báo: Đang chạy từ thư mục không phải gốc Git ('{scan_root.name}/'). Quy tắc .gitignore có thể không đầy đủ."
        else:
            if scan_root.name == ".":
                 logger.info(f"✅ Git repository detected. Quét từ gốc: {scan_root.resolve().as_posix()}")
            else:
                 logger.info(f"✅ Git repository detected. Quét từ gốc: {scan_root.as_posix()}")

    return effective_scan_root, git_warning_str
# --- END NEW ---