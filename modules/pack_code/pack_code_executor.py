# Path: modules/pack_code/pack_code_executor.py
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.core import copy_file_to_clipboard
from utils.logging_config import log_success

__all__ = ["execute_pack_code_action"]


def execute_pack_code_action(logger: logging.Logger, result: Dict[str, Any]) -> None:

    status = result.get("status")
    if status == "empty":
        logger.info("Không có file nào để xử lý. Đã dừng.")
        return
    elif status == "error":

        logger.error(
            f"Logic cốt lõi thất bại: {result.get('message', 'Lỗi không xác định')}"
        )
        sys.exit(1)
    elif status != "ok":
        logger.error(
            "Logic cốt lõi thất bại với trạng thái không xác định, executor bị hủy."
        )
        sys.exit(1)

    dry_run: bool = result.get("dry_run", False)
    stdout: bool = result.get("stdout", False)
    final_content: str = result.get("final_content", "")
    output_path_raw: Optional[Path] = result.get("output_path")
    scan_root: Path = result.get("scan_root", Path.cwd())
    copy_to_clipboard: bool = result.get("copy_to_clipboard", False)
    file_list_relative: List[Path] = result.get("file_list_relative", [])
    tree_string: str = result.get("tree_string", "")
    no_tree: bool = result.get("no_tree", False)

    if dry_run:
        logger.info("⚡ [Dry Run] Các file sẽ được đóng gói:")

        if not no_tree and tree_string:

            print("\n" + tree_string)
        else:

            for rel_path in file_list_relative:
                logger.info(f"   -> {rel_path.as_posix()}")

        logger.info(f"\nTổng cộng: {len(file_list_relative)} file.")
        if output_path_raw:

            logger.info(
                f"Output dự kiến: {output_path_raw.expanduser().resolve().as_posix()}"
            )
        return

    if stdout:
        logger.debug("Đang in kết quả ra STDOUT...")
        print(final_content)
        logger.debug("In ra STDOUT hoàn tất.")
        return

    if output_path_raw:

        try:
            output_path = output_path_raw.expanduser().resolve()
        except Exception as e:
            logger.error(f"❌ Lỗi khi xử lý đường dẫn output: {output_path_raw} -> {e}")
            sys.exit(1)

        if not no_tree and tree_string:
            print("\n" + tree_string)
            print("\n" + ("=" * 80) + "\n")

        try:
            logger.info(f"Đang ghi vào file: {output_path.as_posix()}")

            output_path.parent.mkdir(parents=True, exist_ok=True)

            output_path.write_text(final_content, encoding="utf-8")
            logger.info("✅ Ghi file hoàn tất.")

            if copy_to_clipboard:
                logger.info("Đang sao chép file vào clipboard hệ thống...")
                copy_success = copy_file_to_clipboard(logger, output_path)
                if copy_success:
                    log_success(logger, "Đã sao chép file vào clipboard.")
                else:

                    logger.warning("⚠️ Không thể sao chép file vào clipboard.")

        except IOError as e:
            logger.error(f"❌ Lỗi I/O khi ghi file: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"❌ Lỗi không mong muốn khi ghi file: {e}")
            sys.exit(1)
    else:

        logger.error(
            "❌ Lỗi logic: Không ở chế độ stdout/dry_run nhưng không có đường dẫn output."
        )
        sys.exit(1)
