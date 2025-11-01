# Path: modules/zsh_wrapper/zsh_wrapper_core.py
import logging
import os
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


from utils.core import find_git_root


from .zsh_wrapper_helpers import (
    resolve_output_path_interactively,
    resolve_root_interactively,
    resolve_default_output_path,
)
from .zsh_wrapper_executor import execute_zsh_wrapper_action
from .zsh_wrapper_config import DEFAULT_MODE, DEFAULT_VENV

__all__ = ["run_zsh_wrapper"]


TEMPLATE_DIR = Path(__file__).parent / "templates"

# ... (Các hàm _load_template, _find_project_root, _prepare_absolute_mode, 
# _prepare_relative_mode, _generate_wrapper_content giữ nguyên y như cũ) ...

def _load_template(template_name: str) -> str:
    path = TEMPLATE_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy template: {template_name}")
    
    lines = path.read_text(encoding="utf-8").splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith("# Path:")]
    return "\n".join(filtered_lines)


def _find_project_root(
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


def _prepare_absolute_mode(template_content: str, paths: Dict[str, Path]) -> str:
    return (
        template_content.replace("__PROJECT_ROOT_ABS__", str(paths["project_root"]))
        .replace("__VENV_PATH_ABS__", str(paths["venv_path"]))
        .replace("__SCRIPT_PATH_ABS__", str(paths["script_path"]))
    )


def _prepare_relative_mode(
    logger: logging.Logger, template_content: str, paths: Dict[str, Path]
) -> str:
    output_dir = paths["output_path"].parent
    try:
        project_root_rel_to_output = os.path.relpath(
            paths["project_root"], start=output_dir
        )
    except ValueError as e:
        logger.error("Lỗi: Không thể tính đường dẫn tương đối.")
        logger.error("Project Root và Output dường như ở 2 ổ đĩa khác nhau.")
        raise e

    script_path_rel_to_project = paths["script_path"].relative_to(paths["project_root"])
    venv_path_rel_to_project = paths["venv_path"].relative_to(paths["project_root"])
    output_path_rel_to_project = paths["output_path"].relative_to(paths["project_root"])

    return (
        template_content.replace(
            "__PROJECT_ROOT_REL_TO_OUTPUT__", project_root_rel_to_output
        )
        .replace("__VENV_PATH_REL_TO_PROJECT__", venv_path_rel_to_project.as_posix())
        .replace(
            "__SCRIPT_PATH_REL_TO_PROJECT__", script_path_rel_to_project.as_posix()
        )
        .replace(
            "__OUTPUT_PATH_REL_TO_PROJECT__", output_path_rel_to_project.as_posix()
        )
    )


def _generate_wrapper_content(
    logger: logging.Logger,
    script_path: Path,
    output_path: Path,
    project_root: Path,
    venv_name: str,
    mode: str,
) -> Optional[str]:
    venv_path = project_root / venv_name

    paths = {
        "script_path": script_path,
        "output_path": output_path,
        "project_root": project_root,
        "venv_path": venv_path,
    }
    logger.debug(f"Đã giải quyết các đường dẫn cuối cùng: {paths}")

    try:
        shebang = "#!/usr/bin/env zsh"
        path_comment = ""

        if mode == "absolute":
            path_comment = f"# Path: {output_path.as_posix()}"
        else:
            try:
                relative_output_path = output_path.relative_to(project_root).as_posix()
                path_comment = f"# Path: {relative_output_path}"
            except ValueError:
                logger.warning(
                    f"Không thể tính toán đường dẫn relative cho # Path: (output nằm ngoài project)."
                )
                path_comment = (
                    f"# Path: {output_path.as_posix()} (Warning: Non-relative)"
                )

        template_body = ""
        if mode == "absolute":
            logger.info("Chế độ 'absolute': Tạo wrapper với đường dẫn tuyệt đối.")
            template = _load_template("absolute.zsh.template")
            template_body = _prepare_absolute_mode(template, paths)

        elif mode == "relative":
            logger.info("Chế độ 'relative': Tạo wrapper với đường dẫn tương đối.")
            template = _load_template("relative.zsh.template")
            template_body = _prepare_relative_mode(logger, template, paths)

        final_content = f"{shebang}\n{path_comment}\n\n{template_body}"
        return final_content

    except ValueError:
        logger.error(
            "❌ ERROR: When using 'relative' mode, the output file must be INSIDE the Project Root directory."
        )
        logger.error(f"   Output path: {paths['output_path'].as_posix()}")
        logger.error(f"   Project Root: {paths['project_root'].as_posix()}")
        logger.error(
            "   Suggestion: Create the wrapper inside the project's 'bin' directory OR use 'absolute' mode (-m absolute)."
        )
        return None
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi tạo nội dung wrapper: {e}")
        logger.debug("Traceback:", exc_info=True)
        return None


# --- START SỬA LỖI HÀM NÀY ---
def run_zsh_wrapper(
    logger: logging.Logger, cli_args: argparse.Namespace, project_root: Path
) -> bool:
    """
    Logic điều phối chính, xử lý các cờ -n và -M.
    """

    # 1. Xác định Tên (Output) và Đường dẫn Script (Input)
    tool_name: Optional[str] = getattr(cli_args, "name", None)
    script_path_arg_str: Optional[str] = getattr(cli_args, "script_path_arg", None)
    script_path: Optional[Path] = None

    if script_path_arg_str:
        # Ưu tiên đối số vị trí cho INPUT script
        script_path = Path(script_path_arg_str).expanduser().resolve()
        if not tool_name:
            # Nếu -n không được cung cấp, lấy tên từ script
            tool_name = script_path.stem
            logger.debug(f"Lấy tên tool từ script: {tool_name}")
        else:
            # Cả hai đều được cung cấp
            logger.debug(f"Sử dụng script {script_path_arg_str} và output name {tool_name}")

    elif tool_name:
        # KHÔNG có đối số vị trí, chỉ có -n
        # Dùng -n để đoán cả input và output
        logger.debug(f"Sử dụng tên từ cờ -n ({tool_name}) để đoán script input")
        script_path_str = f"scripts/{tool_name}.py"
        script_path = project_root / script_path_str
    
    else:
        logger.error("❌ Lỗi: Phải cung cấp tên tool (-n) hoặc đường dẫn script.")
        return False

    # 2. Xác thực Input
    if not script_path or not script_path.is_file():
        logger.error(
            f"❌ Lỗi: Script path không tồn tại hoặc không phải là file: {script_path}"
        )
        return False

    if not tool_name:
         logger.error(f"❌ Lỗi: Không thể xác định tên tool (output name).")
         return False

    try:
        rel_script_path = script_path.relative_to(project_root).as_posix()
    except ValueError:
        rel_script_path = script_path.as_posix()
        
    logger.info(
        f"Tool: {tool_name}, Script: {rel_script_path}"
    )

    # 3. Find Project Root
    root_arg_str: Optional[str] = getattr(cli_args, "root", None)
    initial_root, is_fallback = _find_project_root(logger, script_path, root_arg_str)

    final_root: Path
    try:
        if is_fallback and root_arg_str is None:
            final_root = resolve_root_interactively(
                logger=logger, fallback_path=initial_root
            )
        else:
            final_root = initial_root
    except SystemExit:
        return False

    logger.info(f"Root đã xác định cuối cùng: {final_root.as_posix()}")

    # 4. Determine modes
    modes_to_run: List[str]
    if getattr(cli_args, "multi_mode", False):
        modes_to_run = ["relative", "absolute"]
        logger.info("Chế độ Multi-Mode (-M) được kích hoạt (relative & absolute).")
    else:
        modes_to_run = [getattr(cli_args, "mode", DEFAULT_MODE)]

    # 5. Get other args
    venv_name: str = getattr(cli_args, "venv", DEFAULT_VENV)
    force: bool = getattr(cli_args, "force", False)
    output_arg_str: Optional[str] = getattr(cli_args, "output", None)
    output_arg_path = Path(output_arg_str).expanduser() if output_arg_str else None

    if output_arg_path and len(modes_to_run) > 1:
        logger.warning(
            f"⚠️ Cờ -o ({output_arg_path.name}) bị bỏ qua khi dùng -M (multi-mode)."
        )
        output_arg_path = None  # Hủy cờ -o nếu dùng -M

    all_success = True

    # 6. Loop and execute
    for mode in modes_to_run:
        logger.info(f"--- 🚀 Đang xử lý mode: {mode} ---")
        final_output_path: Path

        if output_arg_path:
            # Chỉ dùng -o nếu không phải multi-mode
            final_output_path = output_arg_path.resolve()
        else:
            # Tự động xác định đường dẫn
            # Luôn không tương tác nếu dùng -n hoặc -M
            is_non_interactive = getattr(cli_args, "name") or getattr(
                cli_args, "multi_mode"
            ) or getattr(cli_args, "script_path_arg")
            
            if tool_name and is_non_interactive:
                # Nếu dùng -n, -M, hoặc script_path_arg, chúng ta dùng logic mặc định (không tương tác)
                final_output_path = resolve_default_output_path(
                    tool_name, mode, final_root
                )
            else:
                # Dùng logic cũ (có thể tương tác) nếu chỉ chạy zrap (không tham số)
                final_output_path = resolve_output_path_interactively(
                    logger=logger,
                    tool_name=tool_name,
                    output_arg=None,  # đã check ở trên
                    mode=mode,
                    project_root=final_root,
                )

        final_content = _generate_wrapper_content(
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
            continue  # Thử mode tiếp theo (nếu có)

        result_for_executor = {
            "status": "ok",
            "final_content": final_content,
            "output_path": final_output_path,
            "force": force,
        }

        try:
            execute_zsh_wrapper_action(logger=logger, result=result_for_executor)
        except Exception as e:
            logger.error(f"❌ Lỗi khi thực thi ghi file (mode: {mode}): {e}")
            all_success = False

    return all_success