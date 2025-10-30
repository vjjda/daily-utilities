# Path: modules/no_doc/no_doc_executor.py
"""
Execution and Reporting logic for the no_doc module.
(Side-effects: Báo cáo, Xác nhận người dùng, Ghi file)
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Thiết lập sys.path
if not 'PROJECT_ROOT' in locals():
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from utils.logging_config import log_success

__all__ = ["execute_ndoc_action"]

FileResult = Dict[str, Any]

# SỬA: Thay đổi chữ ký hàm
def execute_ndoc_action(
    logger: logging.Logger,
    grouped_results: Dict[str, List[FileResult]],
    dry_run: bool,
    force: bool,
    scan_root: Path, # Dùng để in đường dẫn tương đối
    git_warning_str: str,
) -> None:
    """
    Xử lý danh sách các file cần sửa, thực hiện side-effects.
    """

    # SỬA: Tính tổng số file từ các nhóm
    total_files_to_fix = sum(len(files) for files in grouped_results.values())

    if total_files_to_fix == 0:
        log_success(logger, "Tất cả file đã sạch docstring hoặc không cần thay đổi.")
        return

    # 1. In báo cáo (SỬA: Lặp qua các nhóm)
    logger.warning(
        f"⚠️ {total_files_to_fix} file cần được sửa (Docstrings sẽ bị xóa):"
    )

    for group_name, files_in_group in grouped_results.items():
        logger.warning(f"\n   --- Nhóm: {group_name} ({len(files_in_group)} file) ---")
        
        for info in files_in_group:
            file_path: Path = info["path"]
            try:
                rel_path = file_path.relative_to(scan_root).as_posix()
            except ValueError:
                rel_path = str(file_path) # Fallback nếu nằm ngoài
                
            logger.warning(f"   -> {rel_path} (Sẽ bị thay đổi định dạng do AST unparse)")

    # 2. Xử lý theo chế độ
    if dry_run:
        logger.warning(f"-> Để xóa docstring, chạy lại mà không có cờ -d (sử dụng -f/--force để bỏ qua xác nhận).")
        sys.exit(1) # Thoát với mã lỗi
    else:
        # --- Chế độ "fix" (Mặc định) ---
            
        proceed_to_write = force
        if not force:
            try:
                confirmation = input("\nTiếp tục xóa docstring và ghi đè các file này? (y/n): ")
            except EOFError:
                confirmation = "n"
            except KeyboardInterrupt:
                confirmation = "n" 
            
            if confirmation.lower() == "y":
                proceed_to_write = True
            else:
                logger.warning("Hoạt động sửa file bị hủy bởi người dùng.")
                sys.exit(0)

        if proceed_to_write:
            written_count = 0
            # SỬA: Lặp qua các nhóm để ghi file
            for files_in_group in grouped_results.values():
                for info in files_in_group:
                    target_path: Path = info["path"]
                    new_content: str = info["new_content"]
                    
                    try:
                        target_path.write_text(new_content, encoding="utf-8")
                        rel_path_str = target_path.relative_to(scan_root).as_posix()
                        logger.info(f"Đã sửa: {rel_path_str}")
                        written_count += 1
                    except IOError as e:
                        logger.error(
                            "❌ Lỗi khi ghi file %s: %s",
                            target_path.relative_to(scan_root).as_posix(),
                            e
                        )

            log_success(logger, f"Hoàn tất! Đã xóa docstring khỏi {written_count} file.")