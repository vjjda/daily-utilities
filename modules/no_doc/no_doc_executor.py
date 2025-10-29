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

def execute_ndoc_action(
    logger: logging.Logger,
    files_to_fix: List[FileResult],
    dry_run: bool,
    force: bool,
    scan_root: Path,
    git_warning_str: str,
) -> None:
    """
    Xử lý danh sách các file cần sửa, thực hiện side-effects.
    
    Args:
        logger: Logger.
        files_to_fix: Danh sách kết quả từ Core/Analyzer.
        dry_run: True nếu ở chế độ 'check' (dry-run).
        force: True nếu cờ --force được sử dụng.
        scan_root: Gốc quét (để tính đường dẫn tương đối).
        git_warning_str: Cảnh báo Git (nếu có) từ entrypoint.
    """

    processed_count = len(files_to_fix)

    if processed_count == 0:
        if git_warning_str: logger.warning(f"\n{git_warning_str}")
        log_success(logger, "Tất cả file đã sạch docstring hoặc không cần thay đổi.")
        return

    # 1. In báo cáo
    logger.warning(
        f"⚠️ {processed_count} file cần được sửa (Docstrings sẽ bị xóa):"
    )

    for info in files_to_fix:
        file_path: Path = info["path"]
        try:
            rel_path = file_path.relative_to(scan_root).as_posix()
        except ValueError:
            rel_path = str(file_path)
            
        # Chúng ta không thể hiển thị "preview" dễ dàng do ast.unparse 
        # thay đổi định dạng quá nhiều. Chỉ in ra đường dẫn.
        logger.warning(f"   -> {rel_path} (Sẽ bị thay đổi định dạng do AST unparse)")

    # 2. Xử lý theo chế độ
    if dry_run:
        # --- Chế độ "dry-run" ---
        if git_warning_str: logger.warning(f"\n{git_warning_str}")
        logger.warning(f"-> Để xóa docstring, chạy lại mà không có cờ -d (sử dụng -f/--force để bỏ qua xác nhận).")
        sys.exit(1) # Thoát với mã lỗi
    else:
        # --- Chế độ "fix" (mặc định) ---
        if git_warning_str: logger.warning(f"\n{git_warning_str}")
            
        proceed_to_write = force
        if not force:
            try:
                confirmation = input("\nTiếp tục xóa docstring và ghi đè các file này? (y/n): ")
            except EOFError:
                confirmation = "n"
            
            if confirmation.lower() == "y":
                proceed_to_write = True
            else:
                logger.warning("Hoạt động sửa file bị hủy bởi người dùng.")
                sys.exit(0)

        if proceed_to_write:
            written_count = 0
            for info in files_to_fix:
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