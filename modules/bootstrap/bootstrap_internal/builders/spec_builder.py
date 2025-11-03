# Path: modules/bootstrap/bootstrap_internal/builders/spec_builder.py
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logging_config import log_success
from utils.cli import launch_editor
from utils.core import load_project_config_section, load_text_template

from ...bootstrap_config import (
    PROJECT_CONFIG_FILENAME,
    CONFIG_SECTION_NAME,
    DEFAULT_BIN_DIR_NAME,
    DEFAULT_SCRIPTS_DIR_NAME,
    DEFAULT_MODULES_DIR_NAME,
    DEFAULT_DOCS_DIR_NAME,
    SPEC_TEMPLATE_FILENAME,
)

__all__ = ["run_init_spec_logic"]


def _generate_names_from_stem(stem: str) -> Dict[str, str]:

    tool_name = stem

    sanitized_name = stem.replace("-", "_").replace(".", "_")

    if sanitized_name.endswith("_spec"):
        sanitized_name = sanitized_name[:-5]

    if stem == "new_tool.spec":
        tool_name = "new_tool"
        sanitized_name = "new_tool"

    pascal_case_name = "".join(
        part.capitalize() for part in sanitized_name.split("_") if part
    )

    if not pascal_case_name:
        pascal_case_name = "NewTool"
        sanitized_name = "new_tool"
        tool_name = "new_tool"

    return {
        "meta_tool_name": tool_name,
        "meta_script_file": f"{sanitized_name}.py",
        "meta_module_name": sanitized_name,
        "meta_logger_name": pascal_case_name,
    }


def run_init_spec_logic(
    logger: logging.Logger,
    project_root: Path,
    init_spec_path_str: str,
    force: bool,
) -> None:

    target_spec_path = Path(init_spec_path_str).resolve()
    if target_spec_path.is_dir():
        logger.warning(
            f"⚠️ Đường dẫn '{init_spec_path_str}' là một thư mục. Đang tạo file 'new_tool.spec.toml' bên trong đó."
        )
        target_spec_path = target_spec_path / "new_tool.spec.toml"
    elif not target_spec_path.name.endswith(".spec.toml"):
        target_spec_path = target_spec_path.with_name(
            f"{target_spec_path.name}.spec.toml"
        )

    logger.info(f"   File spec đích: {target_spec_path.as_posix()}")

    if target_spec_path.exists() and not force:

        logger.error(f"❌ Lỗi: File spec đã tồn tại tại: {target_spec_path.as_posix()}")
        logger.error("   (Sử dụng -f hoặc --force để ghi đè)")
        sys.exit(1)
    elif target_spec_path.exists() and force:
        logger.warning(f"⚠️ File spec đã tồn tại. Sẽ ghi đè (do --force)...")

    logger.debug(f"Đang tìm {PROJECT_CONFIG_FILENAME} để kế thừa [layout]...")
    project_config_path = project_root / PROJECT_CONFIG_FILENAME

    project_bootstrap_config = load_project_config_section(
        project_config_path, CONFIG_SECTION_NAME, logger
    )

    layout_defaults: Dict[str, Any]
    if project_bootstrap_config:
        logger.info(
            f"   Tìm thấy '{PROJECT_CONFIG_FILENAME}'. Đang kế thừa [layout] từ section [bootstrap]."
        )
        layout_defaults = project_bootstrap_config
    else:
        logger.info(
            f"   Không tìm thấy '{PROJECT_CONFIG_FILENAME}'. Sử dụng layout mặc định."
        )
        layout_defaults = {
            "bin_dir": DEFAULT_BIN_DIR_NAME,
            "scripts_dir": DEFAULT_SCRIPTS_DIR_NAME,
            "modules_dir": DEFAULT_MODULES_DIR_NAME,
            "docs_dir": DEFAULT_DOCS_DIR_NAME,
        }

    spec_name = target_spec_path.name

    spec_stem = spec_name.removesuffix(".spec.toml")

    logger.info(f"   Đang tự động điền tên meta từ stem: '{spec_stem}'...")
    meta_names = _generate_names_from_stem(spec_stem)
    logger.debug(f"   Tên đã tạo: {meta_names}")

    format_values = {**layout_defaults, **meta_names}

    try:
        spec_template_path = project_root / SPEC_TEMPLATE_FILENAME
        template_content = load_text_template(spec_template_path, logger)

        final_content = template_content.format(
            layout_bin_dir=format_values.get("bin_dir", DEFAULT_BIN_DIR_NAME),
            layout_scripts_dir=format_values.get(
                "scripts_dir", DEFAULT_SCRIPTS_DIR_NAME
            ),
            layout_modules_dir=format_values.get(
                "modules_dir", DEFAULT_MODULES_DIR_NAME
            ),
            layout_docs_dir=format_values.get("docs_dir", DEFAULT_DOCS_DIR_NAME),
            meta_tool_name=format_values.get("meta_tool_name", "new_tool"),
            meta_script_file=format_values.get("meta_script_file", "new_tool.py"),
            meta_module_name=format_values.get("meta_module_name", "new_tool"),
            meta_logger_name=format_values.get("meta_logger_name", "NewTool"),
        )

        target_spec_path.parent.mkdir(parents=True, exist_ok=True)
        target_spec_path.write_text(final_content, encoding="utf-8")

        log_success(logger, f"Đã tạo file spec mẫu tại: {target_spec_path.as_posix()}")
        logger.info("   Vui lòng kiểm tra và chạy lại `btool`.")
        launch_editor(logger, target_spec_path)

    except Exception as e:
        logger.error(f"❌ Lỗi khi tạo file spec: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)
