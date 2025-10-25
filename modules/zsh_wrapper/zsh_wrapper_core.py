# Path: modules/zsh_wrapper/zsh_wrapper_core.py

"""
Core logic for zsh_wrapper (zrap).
"""

import logging
import os
from pathlib import Path
# --- MODIFIED: Thêm Tuple vào import ---
from typing import Dict, Any, List, Optional, Tuple
# --- END MODIFIED ---

# Import từ utils
from utils.core import find_git_root

__all__ = ["process_zsh_wrapper_logic"]

# Thư mục chứa template của module này
TEMPLATE_DIR = Path(__file__).parent / "templates"

def _load_template(template_name: str) -> str:
    """Helper: Tải nội dung template."""
    path = TEMPLATE_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy template: {template_name}")
    return path.read_text(encoding='utf-8')

# --- MODIFIED: Thay đổi hàm để trả về Tuple[Path, bool] ---
def _find_project_root(logger: logging.Logger, script_path: Path, root_arg: Optional[str]) -> Tuple[Path, bool]:
    """
    Tìm Project Root, ưu tiên --root, sau đó là find_git_root.
    Trả về (project_root, is_fallback_required).
    """
    if root_arg:
        logger.debug(f"Sử dụng Project Root được chỉ định: {root_arg}")
        return Path(root_arg).resolve(), False
    
    logger.debug(f"Đang tự động tìm Project Root (Git) từ: {script_path.parent}")
    # Chúng ta dùng find_git_root từ utils/core.py
    git_root = find_git_root(script_path.parent) 
    if git_root:
        logger.debug(f"Đã tìm thấy Git root: {git_root}")
        return git_root, False
    
    # Fallback case (Git root not found)
    fallback_path = script_path.parent.resolve()
    logger.warning(f"Không tìm thấy Git root. Đề xuất Project Root dự phòng: {fallback_path}")
    return fallback_path, True # <-- Trả về đường dẫn dự phòng VÀ cờ True
# --- END MODIFIED ---

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

# --- MODIFIED: Cập nhật hàm chính để trả về trạng thái fallback ---
def process_zsh_wrapper_logic(
    logger: logging.Logger, 
    args: Any
) -> Dict[str, Any]:
    """
    Hàm logic chính, phân tích, tính toán và tạo nội dung wrapper.
    
    Nếu args.output là None, chỉ chạy logic xác định Project Root.
    """
    
    # 1. Lấy và kiểm tra các đường dẫn cơ bản
    script_path = Path(args.script_path).resolve()
    
    # 2. Xác định Project Root
    project_root, is_fallback = _find_project_root(logger, script_path, args.root)

    # 2.5. Nếu cần fallback VÀ người dùng CHƯA chỉ định root tường minh
    if is_fallback and args.root is None: # Thêm kiểm tra args.root is None để chỉ chạy khi tự động tìm thấy
        # Trả về đối tượng báo hiệu cho entry point (scripts/zsh_wrapper.py)
        # để nó tiến hành hỏi người dùng.
        return {
            "status": "fallback_required",
            "fallback_path": project_root, # Đường dẫn dự phòng
            "script_path": script_path,
            "output_path": None, # Chưa có
            "venv": args.venv,
            "mode": args.mode,
            "force": args.force,
        }
    
    # --- NEW: BƯỚC THOÁT SỚM (Chỉ chạy để xác định Project Root) ---
    if args.output is None:
        return {
            "status": "ok",
            "project_root_abs": project_root.resolve(), # Trả về Root đã resolve/tìm được
            # Không có final_content/output_path
        }
    # --- END NEW ---

    # (Tiếp tục xử lý nếu Project Root đã được xác định hợp lệ VÀ args.output đã có)
    output_path = Path(args.output).resolve()
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
    # ... (Phần này không đổi: Tạo final_content) ...
    if args.mode == "absolute":
        logger.info("Chế độ 'absolute': Tạo wrapper với đường dẫn tuyệt đối.")
        template = _load_template("absolute.zsh.template")
        final_content = _prepare_absolute_mode(template, paths)
        
    elif args.mode == "relative":
        logger.info("Chế độ 'relative': Tạo wrapper với đường dẫn tương đối.")
        template = _load_template("relative.zsh.template")
        try:
            final_content = _prepare_relative_mode(logger, template, paths)
        except ValueError:
            logger.error("❌ ERROR: When using 'relative' mode, the output file must be INSIDE the Project Root directory.")
            logger.error(f"   Output path: {paths['output_path'].as_posix()}")
            logger.error(f"   Project Root: {paths['project_root'].as_posix()}")
            logger.error("   Suggestion: Create the wrapper inside the project's 'bin' directory HOẶC sử dụng 'absolute' mode (-m absolute).")
            return {
                "status": "error",
                "message": "Relative path calculation failed."
            }

    # 4. Trả về kết quả cho executor
    return {
        "status": "ok",
        "final_content": final_content,
        "output_path": output_path,
        "force": args.force,
        "project_root_abs": project_root.resolve(), # Giữ lại để nhất quán
    }
# --- END MODIFIED ---