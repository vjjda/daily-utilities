# Path: modules/zsh_wrapper/zsh_wrapper_core.py
import logging
import os
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import từ các file helper mới
from .zsh_wrapper_resolver import resolve_wrapper_inputs
from .zsh_wrapper_generator import generate_wrapper_content

from .zsh_wrapper_helpers import (
    resolve_output_path_interactively,
    resolve_default_output_path,
)
from .zsh_wrapper_executor import execute_zsh_wrapper_action
from .zsh_wrapper_config import DEFAULT_MODE, DEFAULT_VENV

__all__ = ["run_zsh_wrapper"]


# TẤT CẢ CÁC HÀM _load_template, _find_project_root, _prepare_*, 
# _generate_wrapper_content ĐỀU ĐÃ BỊ XÓA KHỎI ĐÂY


def run_zsh_wrapper(
    logger: logging.Logger, cli_args: argparse.Namespace, project_root: Path
) -> bool:
    """
    Logic điều phối chính, xử lý các cờ -n và -M.
    (Đã được thu gọn)
    """

    # 1. Giải quyết Input (dùng resolver mới)
    input_data = resolve_wrapper_inputs(logger, cli_args, project_root)
    if not input_data:
        return False # Resolver đã log lỗi

    tool_name: str = input_data["tool_name"]
    script_path: Path = input_data["script_path"]
    final_root: Path = input_data["final_root"]

    # 2. Xác định modes
    modes_to_run: List[str]
    if getattr(cli_args, "multi_mode", False):
        modes_to_run = ["relative", "absolute"]
        logger.info("Chế độ Multi-Mode (-M) được kích hoạt (relative & absolute).")
    else:
        modes_to_run = [getattr(cli_args, "mode", DEFAULT_MODE)]

    # 3. Lấy các tham số khác
    venv_name: str = getattr(cli_args, "venv", DEFAULT_VENV)
    force: bool = getattr(cli_args, "force", False)
    output_arg_str: Optional[str] = getattr(cli_args, "output", None)
    output_arg_path = Path(output_arg_str).expanduser() if output_arg_str else None

    if output_arg_path and len(modes_to_run) > 1:
        logger.warning(
            f"⚠️ Cờ -o ({output_arg_path.name}) bị bỏ qua khi dùng -M (multi-mode)."
        )
        output_arg_path = None

    all_success = True

    # 4. Vòng lặp điều phối
    for mode in modes_to_run:
        logger.info(f"--- 🚀 Đang xử lý mode: {mode} ---")
        final_output_path: Path

        if output_arg_path:
            final_output_path = output_arg_path.resolve()
        else:
            is_non_interactive = getattr(cli_args, "name") or getattr(
                cli_args, "multi_mode"
            ) or getattr(cli_args, "script_path_arg")
            
            if tool_name and is_non_interactive:
                final_output_path = resolve_default_output_path(
                    tool_name, mode, final_root
                )
            else:
                final_output_path = resolve_output_path_interactively(
                    logger=logger,
                    tool_name=tool_name,
                    output_arg=None,
                    mode=mode,
                    project_root=final_root,
                )

        # 5. Gọi Generator
        final_content = generate_wrapper_content(
            logger=logger,
            script_path=script_path,
            output_path=final_output_path,
            project_root=final_root,
            venv_name=venv_name,
            mode=mode,
        )

        if final_content is None:
            logger.error(f"❌ Không thể tạo nội dung wrapper (mode: {mode}).")
            all_success = False
            continue

        result_for_executor = {
            "status": "ok",
            "final_content": final_content,
            "output_path": final_output_path,
            "force": force,
        }

        # 6. Gọi Executor
        try:
            execute_zsh_wrapper_action(logger=logger, result=result_for_executor)
        except Exception as e:
            logger.error(f"❌ Lỗi khi thực thi ghi file (mode: {mode}): {e}")
            all_success = False

    return all_success