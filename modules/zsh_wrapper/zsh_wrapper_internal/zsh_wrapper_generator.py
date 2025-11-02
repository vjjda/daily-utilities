# Path: modules/zsh_wrapper/zsh_wrapper_internal/zsh_wrapper_generator.py
import logging
import os
from pathlib import Path
from typing import Dict, Optional


# --- SỬA LỖI TẠI ĐÂY ---
# Đường dẫn cũ: Path(__file__).parent / "templates"
# Thêm .parent để đi lùi 1 cấp
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
# --- KẾT THÚC SỬA LỖI ---

__all__ = ["generate_wrapper_content"]


def _load_template(template_name: str) -> str:
    path = TEMPLATE_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy template: {template_name}")

    lines = path.read_text(encoding="utf-8").splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith("# Path:")]
    return "\n".join(filtered_lines)


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


def generate_wrapper_content(
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