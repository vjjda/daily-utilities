# Path: tools/bootstrap_tool.py
import sys
import argparse
import logging
from pathlib import Path
from typing import Final, Dict, Any, Optional

try:
    import argcomplete
except ImportError:
    argcomplete = None

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from utils.logging_config import setup_logging, log_success
    from utils.cli import run_cli_app, ConfigInitializer, launch_editor
    from utils.core import load_project_config_section, load_text_template
    from modules.bootstrap import (
        orchestrate_bootstrap,
        CONFIG_SECTION_NAME,
        MODULE_DIR,
        TEMPLATE_FILENAME,
        BOOTSTRAP_DEFAULTS,
        PROJECT_CONFIG_FILENAME,
        DEFAULT_BIN_DIR_NAME,
        DEFAULT_SCRIPTS_DIR_NAME,
        DEFAULT_MODULES_DIR_NAME,
        DEFAULT_DOCS_DIR_NAME,
        SPEC_TEMPLATE_FILENAME,
    )
except ImportError as e:
    print(f"Lỗi: Không thể import utils hoặc gateway bootstrap: {e}", file=sys.stderr)
    sys.exit(1)


def _generate_names_from_stem(stem: str) -> Dict[str, str]:

    snake_case_name = stem.replace("-", "_")

    pascal_case_name = "".join(part.capitalize() for part in snake_case_name.split("_"))

    tool_name = stem

    return {
        "meta_tool_name": tool_name,
        "meta_script_file": f"{snake_case_name}.py",
        "meta_module_name": snake_case_name,
        "meta_logger_name": pascal_case_name,
    }


def handle_init_spec_request(
    logger: logging.Logger,
    init_spec_path_str: Optional[str],
    project_root: Path,
    force: bool,
) -> bool:
    if init_spec_path_str is None:
        return False

    logger.info(f"🚀 Yêu cầu khởi tạo file spec (chế độ -s)...")

    target_path = Path(init_spec_path_str).resolve()
    if target_path.is_dir():
        logger.warning(
            f"⚠️ Đường dẫn '{init_spec_path_str}' là một thư mục. Đang tạo file 'new_tool.spec.toml' bên trong đó."
        )
        target_path = target_path / "new_tool.spec.toml"
    elif not target_path.name.endswith(".spec.toml"):

        target_path = target_path.with_name(f"{target_path.name}.spec.toml")

    logger.info(f"   File spec đích: {target_path.as_posix()}")

    if target_path.exists() and not force:
        logger.error(f"❌ Lỗi: File spec đã tồn tại tại: {target_path.as_posix()}")
        logger.error("   (Sử dụng -f hoặc --force để ghi đè)")
        sys.exit(1)
    elif target_path.exists() and force:
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

    spec_stem = target_path.stem
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

        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(final_content, encoding="utf-8")

        log_success(logger, f"Đã tạo file spec mẫu tại: {target_path.as_posix()}")
        logger.info("   Vui lòng kiểm tra và chạy lại `btool`.")
        launch_editor(logger, target_path)

    except Exception as e:
        logger.error(f"❌ Lỗi khi tạo file spec: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    return True


def main():
    logger = setup_logging(script_name="Btool", console_level_str="INFO")
    logger.debug("Script bootstrap bắt đầu.")

    parser = argparse.ArgumentParser(
        description="Bootstrap (khởi tạo) một tool utility mới từ file *.spec.toml.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "spec_file_path_str",
        type=str,
        nargs="?",
        default=None,
        help="Đường dẫn đến file *.spec.toml (ví dụ: docs/drafts/new_tool.spec.toml).\n"
        "Bắt buộc cho chế độ chạy, tùy chọn cho -s hoặc -c.",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Ghi đè (overwrite) các file/thư mục đã tồn tại.",
    )

    run_group = parser.add_argument_group("Tùy chọn Chế độ Run (Mặc định)")
    run_group.add_argument(
        "-i",
        "--interface",
        type=str,
        choices=["typer", "argparse"],
        default=None,
        help="(Chế độ Run) Ghi đè loại interface (typer/argparse) được định nghĩa trong file spec.",
    )

    init_group = parser.add_argument_group("Tùy chọn Khởi tạo (Chạy riêng lẻ)")
    init_group.add_argument(
        "-s",
        "--init-spec",
        type=str,
        nargs="?",
        const=f"new_tool.spec.toml",
        dest="init_spec_path_str",
        help="Khởi tạo một file .spec.toml mới từ template.\n"
        "Tùy chọn cung cấp đường dẫn (ví dụ: -s 'path/to/my_spec.toml').\n"
        "Nếu không có đường dẫn, sẽ tạo 'new_tool.spec.toml' ở thư mục hiện tại.",
    )
    init_group.add_argument(
        "-c",
        "--config-project",
        action="store_true",
        help=f"Khởi tạo/cập nhật section [bootstrap] trong {PROJECT_CONFIG_FILENAME}.",
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    try:
        config_initializer = ConfigInitializer(
            logger=logger,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename="",
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            base_defaults=BOOTSTRAP_DEFAULTS,
        )
        config_initializer.check_and_handle_requests(
            argparse.Namespace(config_project=args.config_project, config_local=False)
        )
    except SystemExit:
        sys.exit(0)
    except Exception as e:
        logger.error(f"Lỗi khi chạy ConfigInitializer: {e}")
        sys.exit(1)

    try:
        init_spec_done = handle_init_spec_request(
            logger, args.init_spec_path_str, PROJECT_ROOT, args.force
        )
        if init_spec_done:
            sys.exit(0)
    except SystemExit:
        sys.exit(0)
    except Exception as e:
        logger.error(f"Lỗi khi chạy Init Spec: {e}")
        sys.exit(1)

    if not args.spec_file_path_str:
        parser.error(
            "Đối số 'spec_file_path_str' là bắt buộc khi không sử dụng -s hoặc -c."
        )
        sys.exit(1)

    run_cli_app(
        logger=logger,
        orchestrator_func=orchestrate_bootstrap,
        cli_args=args,
        project_root=PROJECT_ROOT,
    )


if __name__ == "__main__":
    main()
