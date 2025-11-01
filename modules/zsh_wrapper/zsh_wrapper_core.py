# Path: modules/zsh_wrapper/zsh_wrapper_core.py
import logging
import os
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from utils.core import load_and_merge_configs
from utils.core.config_helpers import resolve_config_value

from .zsh_wrapper_resolver import resolve_wrapper_inputs
from .zsh_wrapper_generator import generate_wrapper_content
from .zsh_wrapper_helpers import (
    resolve_output_path_interactively,
    resolve_default_output_path,
)
from .zsh_wrapper_executor import execute_zsh_wrapper_action
from .zsh_wrapper_config import (
    DEFAULT_MODE,
    DEFAULT_VENV,
    DEFAULT_WRAPPER_RELATIVE_DIR,
    DEFAULT_WRAPPER_ABSOLUTE_PATH,
    CONFIG_FILENAME,
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
)

__all__ = ["run_zsh_wrapper"]


def run_zsh_wrapper(
    logger: logging.Logger, cli_args: argparse.Namespace, project_root: Path
) -> bool:
    """
    Logic điều phối chính, xử lý các cờ -n và -M.
    """

    # 1. Giải quyết Input
    input_data = resolve_wrapper_inputs(logger, cli_args, project_root)
    if not input_data:
        return False

    tool_name: str = input_data["tool_name"]
    script_path: Path = input_data["script_path"]
    final_root: Path = input_data["final_root"]

    # 2. Tải config từ Root đã xác định
    file_config_data = load_and_merge_configs(
        start_dir=final_root,
        logger=logger,
        project_config_filename=PROJECT_CONFIG_FILENAME,
        local_config_filename=CONFIG_FILENAME,
        config_section_name=CONFIG_SECTION_NAME,
    )

    # 3. Xác định modes (Sử dụng config)
    modes_to_run: List[str]
    if getattr(cli_args, "multi_mode", False):
        modes_to_run = ["relative", "absolute"]
        logger.info("Chế độ Multi-Mode (-M) được kích hoạt (relative & absolute).")
    else:
        cli_mode = getattr(cli_args, "mode")
        file_mode = file_config_data.get("mode")
        cli_mode_val = cli_mode if cli_mode != DEFAULT_MODE else None 
        
        final_mode = resolve_config_value(cli_mode_val, file_mode, DEFAULT_MODE)
        modes_to_run = [final_mode]

    # 4. Lấy các tham số khác (Sử dụng config)
    
    cli_venv = getattr(cli_args, "venv", None)
    file_venv = file_config_data.get("venv")
    venv_name: str = resolve_config_value(cli_venv, file_venv, DEFAULT_VENV)
    
    # --- START THÊM MỚI: LẤY CONFIG PATHS ---
    file_rel_dir = file_config_data.get("relative_dir")
    final_rel_dir: str = resolve_config_value(
        None, file_rel_dir, DEFAULT_WRAPPER_RELATIVE_DIR
    )
    
    file_abs_dir_str = file_config_data.get("absolute_dir")
    final_abs_dir_str: str = resolve_config_value(
        None, file_abs_dir_str, str(DEFAULT_WRAPPER_ABSOLUTE_PATH)
    )
    # Luôn expanduser phòng trường hợp config ghi "~/bin"
    final_abs_dir = Path(final_abs_dir_str).expanduser()
    # --- END THÊM MỚI ---

    force: bool = getattr(cli_args, "force", False)
    output_arg_str: Optional[str] = getattr(cli_args, "output", None)
    output_arg_path = Path(output_arg_str).expanduser() if output_arg_str else None

    if output_arg_path and len(modes_to_run) > 1:
        logger.warning(
            f"⚠️ Cờ -o ({output_arg_path.name}) bị bỏ qua khi dùng -M (multi-mode)."
        )
        output_arg_path = None

    all_success = True

    # 5. Vòng lặp điều phối
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
                # --- START SỬA: TRUYỀN CONFIG VÀO ---
                final_output_path = resolve_default_output_path(
                    tool_name,
                    mode,
                    final_root,
                    final_rel_dir,  # <-- Truyền vào
                    final_abs_dir   # <-- Truyền vào
                )
                # --- END SỬA ---
            else:
                # --- START SỬA: TRUYỀN CONFIG VÀO ---
                final_output_path = resolve_output_path_interactively(
                    logger=logger,
                    tool_name=tool_name,
                    output_arg=None,
                    mode=mode,
                    project_root=final_root,
                    relative_dir_name=final_rel_dir, # <-- Truyền vào
                    absolute_dir_path=final_abs_dir  # <-- Truyền vào
                )
                # --- END SỬA ---

        # 6. Gọi Generator
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

        # 7. Gọi Executor
        try:
            execute_zsh_wrapper_action(logger=logger, result=result_for_executor)
        except Exception as e:
            logger.error(f"❌ Lỗi khi thực thi ghi file (mode: {mode}): {e}")
            all_success = False

    return all_success