# Path: modules/zsh_wrapper/zsh_wrapper_internal/zsh_wrapper_resolver.py
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from utils.core import find_git_root

from .zsh_wrapper_helpers import resolve_root_interactively

__all__ = ["resolve_wrapper_inputs", "find_project_root"]


def find_project_root(
    logger: logging.Logger, script_path: Path, root_arg: Optional[str]
) -> Tuple[Path, bool]:
    if root_arg:
        logger.debug(f"Sử dụng Project Root được chỉ định: {root_arg}")
        return Path(root_arg).expanduser().resolve(), False

    logger.debug(f"Đang tự động tìm Project Root (Git) từ: {script_path.parent}")
    git_root = find_git_root(script_path.parent)
    if git_root:
        logger.debug(f"Đã tìm thấy Git root: {git_root}")
        return git_root, False

    fallback_path = script_path.parent.resolve()
    logger.warning(
        f"Không tìm thấy Git root. Đề xuất Project Root dự phòng: {fallback_path}"
    )
    return fallback_path, True


def resolve_wrapper_inputs(
    logger: logging.Logger, cli_args: argparse.Namespace, project_root_entry: Path
) -> Optional[Dict[str, Any]]:
    tool_name: Optional[str] = getattr(cli_args, "name", None)
    script_path_arg_str: Optional[str] = getattr(cli_args, "script_path_arg", None)
    script_path: Optional[Path] = None

    if script_path_arg_str:
        script_path = Path(script_path_arg_str).expanduser().resolve()
        if not tool_name:
            tool_name = script_path.stem
            logger.debug(f"Lấy tên tool từ script: {tool_name}")
        else:
            logger.debug(
                f"Sử dụng script {script_path_arg_str} và output name {tool_name}"
            )
    elif tool_name:
        logger.debug(f"Sử dụng tên từ cờ -n ({tool_name}) để đoán script input")
        script_path_str = f"scripts/{tool_name}.py"
        script_path = project_root_entry / script_path_str
    else:
        logger.error("❌ Lỗi: Phải cung cấp tên tool (-n) hoặc đường dẫn script.")
        return None

    if not script_path or not script_path.is_file():
        logger.error(
            f"❌ Lỗi: Script path không tồn tại hoặc không phải là file: {script_path}"
        )
        return None
    if not tool_name:
        logger.error("❌ Lỗi: Không thể xác định tên tool (output name).")
        return None

    try:
        rel_script_path = script_path.relative_to(project_root_entry).as_posix()
    except ValueError:
        rel_script_path = script_path.as_posix()

    logger.info(f"Tool: {tool_name}, Script: {rel_script_path}")

    root_arg_str: Optional[str] = getattr(cli_args, "root", None)
    initial_root, is_fallback = find_project_root(logger, script_path, root_arg_str)

    final_root: Path
    try:
        if is_fallback and root_arg_str is None:
            final_root = resolve_root_interactively(
                logger=logger, fallback_path=initial_root
            )
        else:
            final_root = initial_root
    except SystemExit:
        return None

    logger.info(f"Root đã xác định cuối cùng: {final_root.as_posix()}")

    return {
        "tool_name": tool_name,
        "script_path": script_path,
        "final_root": final_root,
    }
