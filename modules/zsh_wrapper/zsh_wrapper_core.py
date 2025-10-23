# Path: modules/zsh_wrapper/zsh_wrapper_core.py

"""
Core logic for zsh_wrapper (zrap).
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import từ utils
from utils.core import find_git_root

# Thư mục chứa template của module này
TEMPLATE_DIR = Path(__file__).parent / "templates"

def _load_template(template_name: str) -> str:
    """Helper: Tải nội dung template."""
    path = TEMPLATE_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy template: {template_name}")
    return path.read_text(encoding='utf-8')

def _find_project_root(logger: logging.Logger, script_path: Path, root_arg: Optional[str]) -> Path:
    """Tìm Project Root, ưu tiên --root, sau đó là find_git_root."""
    if root_arg:
        logger.debug(f"Sử dụng Project Root được chỉ định: {root_arg}")
        return Path(root_arg).resolve()
    
    logger.debug(f"Đang tự động tìm Project Root (Git) từ: {script_path.parent}")
    # Chúng ta dùng find_git_root từ utils/core.py
    git_root = find_git_root(script_path.parent) 
    if git_root:
        logger.debug(f"Đã tìm thấy Git root: {git_root}")
        return git_root
    
    # Fallback
    logger.warning(f"Không tìm thấy Git root. Sử dụng thư mục cha của script làm Project Root.")
    return script_path.parent.resolve()

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
    """Điền template cho mode 'relative'."""
    
    # 1. Path từ thư mục output -> project root
    # (ví dụ: từ 'bin/' đi lên 'project/' -> '../')
    output_dir = paths["output_path"].parent
    try:
        project_root_rel_to_output = os.path.relpath(
            paths["project_root"], 
            start=output_dir
        )
    except ValueError:
        logger.error("Lỗi: Không thể tính đường dẫn tương đối. Project Root và Output dường như ở 2 ổ đĩa khác nhau.")
        raise
    
    # 2. Path từ project root -> script
    # (ví dụ: từ 'project/' đi xuống 'scripts/foo.py')
    script_path_rel_to_project = paths["script_path"].relative_to(paths["project_root"])
    
    # 3. Path từ project root -> venv
    venv_path_rel_to_project = paths["venv_path"].relative_to(paths["project_root"])
    
    # 4. Path từ project root -> output file (cho # Path: comment)
    output_path_rel_to_project = paths["output_path"].relative_to(paths["project_root"])

    return template_content.format(
        project_root_rel_to_output=project_root_rel_to_output,
        venv_path_rel_to_project=venv_path_rel_to_project.as_posix(),
        script_path_rel_to_project=script_path_rel_to_project.as_posix(),
        output_path_rel_to_project=output_path_rel_to_project.as_posix()
    )

def process_zsh_wrapper_logic(
    logger: logging.Logger, 
    args: Any
) -> Dict[str, Any]:
    """
    Hàm logic chính, phân tích, tính toán và tạo nội dung wrapper.
    """
    
    # 1. Lấy và kiểm tra các đường dẫn cơ bản
    script_path = Path(args.script_path).resolve()
    output_path = Path(args.output).resolve()
    
    if not script_path.exists() or not script_path.is_file():
        logger.error(f"❌ Lỗi: File script không tồn tại: {args.script_path}")
        raise FileNotFoundError(f"File không tìm thấy: {script_path}")
    
    # 2. Xác định các đường dẫn (Project, Venv)
    project_root = _find_project_root(logger, script_path, args.root)
    venv_path = project_root / args.venv
    
    paths = {
        "script_path": script_path,
        "output_path": output_path,
        "project_root": project_root,
        "venv_path": venv_path
    }
    logger.debug(f"Đã giải quyết các đường dẫn: {paths}")
    
    final_content = ""

    # 3. Xử lý theo mode
    if args.mode == "absolute":
        logger.info("Chế độ 'absolute': Tạo wrapper với đường dẫn tuyệt đối.")
        template = _load_template("absolute.zsh.template")
        final_content = _prepare_absolute_mode(template, paths)
        
    elif args.mode == "relative":
        logger.info("Chế độ 'relative': Tạo wrapper với đường dẫn tương đối.")
        template = _load_template("relative.zsh.template")
        final_content = _prepare_relative_mode(logger, template, paths)
    
    # 4. Trả về kết quả cho executor
    return {
        "status": "ok",
        "final_content": final_content,
        "output_path": output_path,
        "force": args.force
    }