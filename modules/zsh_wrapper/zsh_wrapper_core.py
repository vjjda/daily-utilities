# Path: modules/zsh_wrapper/zsh_wrapper_core.py

"""
Core logic for zsh_wrapper (zrap).
Handles orchestration and wrapper content generation.
"""

import logging
import os
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import utils
from utils.core import find_git_root

# Import các thành phần module
from .zsh_wrapper_helpers import resolve_output_path_interactively, resolve_root_interactively
from .zsh_wrapper_executor import execute_zsh_wrapper_action
from .zsh_wrapper_config import DEFAULT_MODE, DEFAULT_VENV

__all__ = ["run_zsh_wrapper"]

# Thư mục chứa template của module này
TEMPLATE_DIR = Path(__file__).parent / "templates"

def _load_template(template_name: str) -> str:
    """Helper: Tải nội dung template."""
    path = TEMPLATE_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy template: {template_name}")
    return path.read_text(encoding='utf-8')

def _find_project_root(logger: logging.Logger, script_path: Path, root_arg: Optional[str]) -> Tuple[Path, bool]:
    """
    Tìm Project Root, ưu tiên --root, sau đó là find_git_root.
    
    Returns:
        Tuple[Path, bool]: (project_root, is_fallback_required)
    """
    if root_arg:
        logger.debug(f"Sử dụng Project Root được chỉ định: {root_arg}")
        return Path(root_arg).expanduser().resolve(), False
    
    logger.debug(f"Đang tự động tìm Project Root (Git) từ: {script_path.parent}")
    git_root = find_git_root(script_path.parent) 
    if git_root:
        logger.debug(f"Đã tìm thấy Git root: {git_root}")
        return git_root, False
    
    # Nếu không tìm thấy .git, đề xuất thư mục cha của script làm root
    fallback_path = script_path.parent.resolve()
    logger.warning(f"Không tìm thấy Git root. Đề xuất Project Root dự phòng: {fallback_path}")
    return fallback_path, True # Yêu cầu fallback (tương tác)

def _prepare_absolute_mode(
    template_content: str, 
    paths: Dict[str, Path]
) -> str:
    """Điền template cho mode 'absolute'."""
    return template_content.format(
        project_root_abs=str(paths["project_root"]),
        venv_path_abs=str(paths["venv_path"]),
        script_path_abs=str(paths["script_path"])
    )

def _prepare_relative_mode(
    logger: logging.Logger,
    template_content: str, 
    paths: Dict[str, Path]
) -> str:
    """
    Điền template cho mode 'relative'.
    
    Raises:
        ValueError: Nếu output_path nằm ngoài project_root (không thể tính relpath).
    """
    output_dir = paths["output_path"].parent
    try:
        # Tính đường dẫn tương đối từ thư mục output LÊN project root
        project_root_rel_to_output = os.path.relpath(
            paths["project_root"], 
            start=output_dir
        )
    except ValueError as e:
        logger.error("Lỗi: Không thể tính đường dẫn tương đối.")
        logger.error("Project Root và Output dường như ở 2 ổ đĩa khác nhau.")
        raise e # Ném lỗi lên để _generate_wrapper_content xử lý
    
    # Tính đường dẫn tương đối TỪ project root XUỐNG venv/script
    script_path_rel_to_project = paths["script_path"].relative_to(paths["project_root"])
    venv_path_rel_to_project = paths["venv_path"].relative_to(paths["project_root"])
    output_path_rel_to_project = paths["output_path"].relative_to(paths["project_root"])

    return template_content.format(
        project_root_rel_to_output=project_root_rel_to_output,
        venv_path_rel_to_project=venv_path_rel_to_project.as_posix(),
        script_path_rel_to_project=script_path_rel_to_project.as_posix(),
        output_path_rel_to_project=output_path_rel_to_project.as_posix()
    )

def _generate_wrapper_content(
    logger: logging.Logger, 
    script_path: Path,
    output_path: Path,
    project_root: Path,
    venv_name: str,
    mode: str
) -> Optional[str]:
    """
    Tạo nội dung wrapper dựa trên các đường dẫn đã được xác định đầy đủ.
    Trả về nội dung (str) nếu thành công, None nếu lỗi.
    """
    venv_path = project_root / venv_name
    
    paths = {
        "script_path": script_path,
        "output_path": output_path,
        "project_root": project_root,
        "venv_path": venv_path
    }
    logger.debug(f"Đã giải quyết các đường dẫn cuối cùng: {paths}")
    
    final_content = ""
    try:
        if mode == "absolute":
            logger.info("Chế độ 'absolute': Tạo wrapper với đường dẫn tuyệt đối.")
            template = _load_template("absolute.zsh.template")
            final_content = _prepare_absolute_mode(template, paths)
            
        elif mode == "relative":
            logger.info("Chế độ 'relative': Tạo wrapper với đường dẫn tương đối.")
            template = _load_template("relative.zsh.template")
            final_content = _prepare_relative_mode(logger, template, paths)
        
        return final_content

    except ValueError: # Bắt lỗi từ _prepare_relative_mode (ổ đĩa khác)
        logger.error("❌ ERROR: When using 'relative' mode, the output file must be INSIDE the Project Root directory.")
        logger.error(f"   Output path: {paths['output_path'].as_posix()}")
        logger.error(f"   Project Root: {paths['project_root'].as_posix()}")
        logger.error("   Suggestion: Create the wrapper inside the project's 'bin' directory OR use 'absolute' mode (-m absolute).")
        return None # Trả về None báo lỗi
    except Exception as e:
        logger.error(f"❌ Lỗi không mong muốn khi tạo nội dung wrapper: {e}")
        return None

def run_zsh_wrapper(logger: logging.Logger, cli_args: argparse.Namespace) -> bool:
    """
    Hàm điều phối chính cho zsh_wrapper (Orchestrator).
    
    Xử lý việc xác định đường dẫn (tương tác nếu cần),
    tạo nội dung wrapper và thực thi ghi file.

    Args:
        logger: Logger.
        cli_args: Namespace đối số thô từ entrypoint (scripts/zsh_wrapper.py).

    Returns:
        True nếu thành công, False nếu thất bại.
    """
    
    # 1. Lấy và kiểm tra đường dẫn script ban đầu
    try:
        script_path_str = getattr(cli_args, 'script_path_arg')
        script_path = Path(script_path_str).expanduser().resolve()
        if not script_path.is_file():
            logger.error(f"❌ Lỗi: Script path không tồn tại hoặc không phải là file: {script_path}")
            return False
    except Exception as e:
        logger.error(f"❌ Lỗi xử lý đường dẫn script: {e}")
        return False

    # 2. Xác định Project Root (tương tác nếu cần)
    root_arg_str: Optional[str] = getattr(cli_args, 'root', None)
    initial_root, is_fallback = _find_project_root(logger, script_path, root_arg_str)
    
    final_root: Path
    try:
        if is_fallback and root_arg_str is None: # Chỉ hỏi nếu root chưa được chỉ định và cần fallback
            final_root = resolve_root_interactively(logger=logger, fallback_path=initial_root)
        else:
            final_root = initial_root
    except SystemExit: # Bắt SystemExit nếu người dùng chọn Quit
        return False # Coi như thất bại

    logger.info(f"Root đã xác định cuối cùng: {final_root.as_posix()}")

    # 3. Xác định Output Path (tương tác nếu cần)
    output_arg_str: Optional[str] = getattr(cli_args, 'output', None)
    output_arg_path = Path(output_arg_str).expanduser() if output_arg_str else None
    mode: str = getattr(cli_args, 'mode', DEFAULT_MODE)
    
    try:
        final_output_path = resolve_output_path_interactively(
            logger=logger, 
            script_path=script_path, 
            output_arg=output_arg_path, 
            mode=mode,
            project_root=final_root
        )
    except SystemExit: # Bắt SystemExit nếu người dùng chọn Quit
        return False # Coi như thất bại

    # 4. Lấy các tham số còn lại
    venv_name: str = getattr(cli_args, 'venv', DEFAULT_VENV)
    force: bool = getattr(cli_args, 'force', False)

    # 5. Tạo nội dung wrapper (Logic thuần túy)
    final_content = _generate_wrapper_content(
        logger=logger,
        script_path=script_path,
        output_path=final_output_path,
        project_root=final_root,
        venv_name=venv_name,
        mode=mode
    )

    if final_content is None:
        logger.error("❌ Không thể tạo nội dung wrapper.")
        return False # Lỗi đã được log bên trong _generate_wrapper_content

    # 6. Chuẩn bị kết quả cho Executor
    result_for_executor = {
        "status": "ok",
        "final_content": final_content,
        "output_path": final_output_path,
        "force": force,
    }

    # 7. Thực thi (Ghi file, Chmod)
    try:
        execute_zsh_wrapper_action(logger=logger, result=result_for_executor)
        return True # Thành công
    except Exception as e:
        # Lỗi I/O hoặc chmod đã được log bên trong executor
        # hoặc lỗi không mong muốn khác
        logger.error(f"❌ Lỗi trong quá trình thực thi ghi file: {e}")
        return False # Thất bại