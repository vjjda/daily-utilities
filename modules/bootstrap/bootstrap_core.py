# Path: modules/bootstrap/bootstrap_core.py
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


from .bootstrap_internal import (
    generate_bin_wrapper,
    generate_script_entrypoint,
    generate_module_file,
    generate_module_init_file,
    generate_doc_file,
)


__all__ = [
    "process_bootstrap_logic",
]


def process_bootstrap_logic(
    logger: logging.Logger,
    config: Dict[str, Any],
    configured_paths: Dict[str, Path],
    cli_args: argparse.Namespace,
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

        generated_content = {
            "bin": generate_bin_wrapper(config),
            "script": generate_script_entrypoint(
                config, cli_interface_override=cli_args.interface
            ),
            "config": generate_module_file(config, "config"),
            "loader": generate_module_file(config, "loader"),
            "core": generate_module_file(config, "core"),
            "executor": generate_module_file(config, "executor"),
            "init": generate_module_init_file(config),
        }

        target_paths = {
            "bin": BIN_DIR / tool_name,
            "script": SCRIPTS_DIR / script_file,
            "config": module_path / f"{mod_name}_config.py",
            "loader": module_path / f"{mod_name}_loader.py",
            "core": module_path / f"{mod_name}_core.py",
            "executor": module_path / f"{mod_name}_executor.py",
            "init": module_path / "__init__.py",
        }

        if config.get("docs", {}).get("enabled", False):
            generated_content["docs"] = generate_doc_file(config)
            target_paths["docs"] = DOCS_DIR / "tools" / f"{tool_name}.md"

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng khi tạo nội dung code: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    return generated_content, target_paths, module_path
