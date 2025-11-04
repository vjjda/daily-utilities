# Path: modules/bootstrap/bootstrap_internal/bootstrap_runner.py
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple

from utils.logging_config import log_success


from .builders.script_builder import generate_script_entrypoint
from .builders.module_builder import generate_module_file, generate_module_init_file
from .builders.doc_builder import generate_doc_file


from .bootstrap_loader import load_spec_file
from modules.zsh_wrapper import generate_wrapper_content
from ..bootstrap_executor import execute_bootstrap_action
from ..bootstrap_config import (
    DEFAULT_BIN_DIR_NAME,
    DEFAULT_SCRIPTS_DIR_NAME,
    DEFAULT_MODULES_DIR_NAME,
    DEFAULT_DOCS_DIR_NAME,
)

__all__ = ["run_bootstrap_logic"]


def _generate_all_content_and_paths(
    logger: logging.Logger,
    config: Dict[str, Any],
    configured_paths: Dict[str, Path],
    cli_args: argparse.Namespace,
    project_root: Path,
) -> Tuple[Dict[str, str], Dict[str, Path], Path]:
    BIN_DIR = configured_paths["BIN_DIR"]
    SCRIPTS_DIR = configured_paths["SCRIPTS_DIR"]
    MODULES_DIR = configured_paths["MODULES_DIR"]
    DOCS_DIR = configured_paths["DOCS_DIR"]

    try:
        tool_name = config["meta"]["tool_name"]
        script_file = config["meta"]["script_file"]
        module_name = config["meta"]["module_name"]
        config["module_name"] = module_name

        if "logger_name" not in config["meta"]:
            config["meta"]["logger_name"] = tool_name.capitalize()

        logger.debug(f"Tên Tool: {tool_name}")
        logger.debug(f"File Script: {script_file}")
        logger.debug(f"Tên Module: {module_name}")
        logger.debug(f"Tên Logger: {config['meta']['logger_name']}")

    except KeyError as e:
        logger.error(f"❌ File spec thiếu key bắt buộc trong [meta]: {e}")
        sys.exit(1)

    module_path = MODULES_DIR / module_name

    try:
        mod_name = config["module_name"]

        target_paths = {
            "bin": BIN_DIR / tool_name,
            "script": SCRIPTS_DIR / script_file,
            "config": module_path / f"{mod_name}_config.py",
            "loader": module_path / f"{mod_name}_loader.py",
            "core": module_path / f"{mod_name}_core.py",
            "executor": module_path / f"{mod_name}_executor.py",
            "init": module_path / "__init__.py",
        }

        def get_rel_path(key: str) -> str:
            try:
                return target_paths[key].relative_to(project_root).as_posix()
            except ValueError:
                logger.warning(f"Không thể tính relative_path cho {key}")
                return target_paths[key].name

        rel_paths = {
            "script": get_rel_path("script"),
            "config": get_rel_path("config"),
            "loader": get_rel_path("loader"),
            "core": get_rel_path("core"),
            "executor": get_rel_path("executor"),
            "init": get_rel_path("init"),
        }

        bin_wrapper_content = generate_wrapper_content(
            logger=logger,
            script_path=target_paths["script"],
            output_path=target_paths["bin"],
            project_root=project_root,
            venv_name=".venv",
            mode="relative",
        )

        if bin_wrapper_content is None:
            logger.error("❌ Lỗi khi tạo nội dung bin wrapper từ logic zrap.")
            sys.exit(1)

        generated_content = {
            "bin": bin_wrapper_content,
            "script": generate_script_entrypoint(
                config,
                cli_interface_override=cli_args.interface,
                relative_path=rel_paths["script"],
            ),
            "config": generate_module_file(
                config, "config", relative_path=rel_paths["config"]
            ),
            "loader": generate_module_file(
                config, "loader", relative_path=rel_paths["loader"]
            ),
            "core": generate_module_file(
                config, "core", relative_path=rel_paths["core"]
            ),
            "executor": generate_module_file(
                config, "executor", relative_path=rel_paths["executor"]
            ),
            "init": generate_module_init_file(config, relative_path=rel_paths["init"]),
        }

        if config.get("docs", {}).get("enabled", False):

            generated_content["docs"] = generate_doc_file(config)
            target_paths["docs"] = DOCS_DIR / "tools" / f"{tool_name}.md"

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng khi tạo nội dung code: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    return generated_content, target_paths, module_path


def run_bootstrap_logic(
    logger: logging.Logger, cli_args: argparse.Namespace, project_root: Path
) -> None:
    spec_file_path_str = getattr(cli_args, "spec_file_path_str", None)

    if not spec_file_path_str:
        raise ValueError(
            "Lỗi logic: run_bootstrap_logic được gọi mà không có spec_file_path_str."
        )

    spec_file_path = Path(spec_file_path_str).expanduser().resolve()

    if not spec_file_path.is_file() or not spec_file_path.name.endswith(".spec.toml"):
        logger.error(
            "❌ Lỗi: Đường dẫn cung cấp không phải là file *.spec.toml hợp lệ."
        )
        logger.error(f"   Đã nhận: {spec_file_path.as_posix()}")
        sys.exit(1)

    logger.info("🚀 Bắt đầu bootstrap:")
    try:
        spec_rel_path = spec_file_path.relative_to(project_root).as_posix()
    except ValueError:
        spec_rel_path = spec_file_path.as_posix()
    logger.info(f"   File Spec: {spec_rel_path}")

    config_spec = load_spec_file(logger, spec_file_path)

    layout_config = config_spec.get("layout", {})
    if not layout_config:
        logger.error(
            f"❌ Lỗi: File spec '{spec_file_path.name}' thiếu section [layout] bắt buộc."
        )
        logger.error(
            f"   Gợi ý: Chạy `btool -s {spec_file_path.as_posix()}` để tạo lại file spec với cấu trúc đúng."
        )
        sys.exit(1)

    logger.debug(f"Đã tải cấu hình [layout] từ file spec: {layout_config}")

    bin_dir_name = layout_config.get("bin_dir", DEFAULT_BIN_DIR_NAME)
    scripts_dir_name = layout_config.get("scripts_dir", DEFAULT_SCRIPTS_DIR_NAME)
    modules_dir_name = layout_config.get("modules_dir", DEFAULT_MODULES_DIR_NAME)
    docs_dir_name = layout_config.get("docs_dir", DEFAULT_DOCS_DIR_NAME)

    configured_paths = {
        "BIN_DIR": project_root / bin_dir_name,
        "SCRIPTS_DIR": project_root / scripts_dir_name,
        "MODULES_DIR": project_root / modules_dir_name,
        "DOCS_DIR": project_root / docs_dir_name,
    }
    logger.debug(f"Đã giải quyết các đường dẫn cấu hình: {configured_paths}")

    (generated_content, target_paths, module_path) = _generate_all_content_and_paths(
        logger=logger,
        config=config_spec,
        configured_paths=configured_paths,
        cli_args=cli_args,
        project_root=project_root,
    )

    logger.info(
        f"   Thư mục Module: {module_path.relative_to(project_root).as_posix()}"
    )

    execute_bootstrap_action(
        logger=logger,
        generated_content=generated_content,
        target_paths=target_paths,
        module_path=module_path,
        project_root=project_root,
        force=cli_args.force,
    )

    log_success(
        logger, "\n✨ Bootstrap hoàn tất! Cấu trúc file cho tool mới đã sẵn sàng."
    )
