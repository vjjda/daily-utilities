# Path: modules/bootstrap/bootstrap_internal/builders/tool_generator.py
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from modules.zsh_wrapper import generate_wrapper_content


from ..bootstrap_loader import load_template


from .snippet_config import (
    build_config_constants,
    build_config_all_list,
    build_config_imports,
)

from .snippet_typer import (
    build_typer_app_code,
    build_typer_path_expands,
    build_typer_args_pass_to_core,
    build_typer_main_signature,
)

from .snippet_argparse import (
    build_argparse_arguments,
    build_path_expands as build_argparse_path_expands,
    build_args_pass_to_core as build_argparse_args_pass_to_core,
)

__all__ = [
    "generate_script_entrypoint",
    "generate_module_file",
    "generate_module_init_file",
    "generate_doc_file",
    "process_bootstrap_logic",
]


def generate_bin_wrapper(config: Dict[str, Any]) -> str:

    template = load_template("bin_wrapper.zsh.template")
    return template.format(
        tool_name=config["meta"]["tool_name"], script_file=config["meta"]["script_file"]
    )


def generate_script_entrypoint(
    config: Dict[str, Any], cli_interface_override: Optional[str] = None
) -> str:

    cli_config = config.get("cli", {})
    cli_help_config = cli_config.get("help", {})

    interface_type = cli_interface_override or cli_config.get("interface", "typer")

    config_imports_code = build_config_imports(config["module_name"], config)

    if interface_type == "argparse":
        template = load_template("script_entrypoint_argparse.py.template")

        argparse_args_code = build_argparse_arguments(config)
        path_expands_code = build_argparse_path_expands(config)
        args_pass_code = build_argparse_args_pass_to_core(config)

        raw_description = cli_help_config.get(
            "description", f"Mô tả cho {config['meta']['tool_name']}."
        )
        raw_epilog = cli_help_config.get("epilog", "")

        formatted_description = repr(raw_description)
        formatted_epilog = repr(raw_epilog)

        argcomplete_imports_code = """
try:
    import argcomplete
except ImportError:
    argcomplete = None
"""
        argcomplete_logic_code = """
    if argcomplete:
        argcomplete.autocomplete(parser)
"""

        return template.format(
            tool_name=config["meta"]["tool_name"],
            script_file=config["meta"]["script_file"],
            logger_name=config["meta"]["logger_name"],
            module_name=config["module_name"],
            config_imports=config_imports_code,
            cli_description=formatted_description,
            cli_epilog=formatted_epilog,
            argparse_arguments=argparse_args_code,
            argparse_path_expands=path_expands_code,
            argparse_args_pass_to_core=args_pass_code,
            argcomplete_imports=argcomplete_imports_code,
            argcomplete_logic=argcomplete_logic_code,
        )

    else:

        template = load_template("script_entrypoint_typer.py.template")

        typer_app_code = build_typer_app_code(config)
        typer_main_sig = build_typer_main_signature(config)
        typer_path_expands = build_typer_path_expands(config)
        typer_args_pass = build_typer_args_pass_to_core(config)

        return template.format(
            tool_name=config["meta"]["tool_name"],
            script_file=config["meta"]["script_file"],
            logger_name=config["meta"]["logger_name"],
            module_name=config["module_name"],
            config_imports=config_imports_code,
            typer_app_code=typer_app_code,
            typer_main_function_signature=typer_main_sig,
            typer_path_expands=typer_path_expands,
            typer_args_pass_to_core=typer_args_pass,
        )


def generate_module_file(config: Dict[str, Any], file_type: str) -> str:

    template_name_map = {
        "config": "module_config.py.template",
        "core": "module_core.py.template",
        "executor": "module_executor.py.template",
        "loader": "module_loader.py.template",
    }
    template_name = template_name_map[file_type]
    template = load_template(template_name)

    format_dict = {"module_name": config["module_name"]}

    if file_type == "config":
        config_constants_code = build_config_constants(config)
        config_all_code = build_config_all_list(config)
        format_dict["config_constants"] = config_constants_code
        format_dict["config_all_constants"] = config_all_code

    return template.format(**format_dict)


def generate_module_init_file(config: Dict[str, Any]) -> str:

    template = load_template("module_init.py.template")
    module_name = config["module_name"]

    config_constants_str = build_config_all_list(config)

    if config_constants_str:
        constants_list = [c.strip().strip('"') for c in config_constants_str.split(",")]

        config_import_block = f"from .{module_name}_config import ("
        config_import_block += "\n" + "\n".join(
            f"    {const}," for const in constants_list
        )
        config_import_block += "\n)"

        config_all_block = "\n".join(f'    "{const}",' for const in constants_list)
    else:
        config_import_block = "# (Không có hằng số config nào để import)"
        config_all_block = "# (Không có hằng số config nào trong __all__)"

    return template.format(
        module_name=module_name,
        config_import_block=config_import_block,
        config_all_block=config_all_block,
    )


def generate_doc_file(config: Dict[str, Any]) -> str:

    template = load_template("doc_file.md.template")

    return template.format(
        tool_name=config["meta"]["tool_name"],
        short_description=config.get("docs", {}).get(
            "short_description", f'Tài liệu cho {config["meta"]["tool_name"]}.'
        ),
    )


def process_bootstrap_logic(
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
                config, cli_interface_override=cli_args.interface
            ),
            "config": generate_module_file(config, "config"),
            "loader": generate_module_file(config, "loader"),
            "core": generate_module_file(config, "core"),
            "executor": generate_module_file(config, "executor"),
            "init": generate_module_init_file(config),
        }

        if config.get("docs", {}).get("enabled", False):
            generated_content["docs"] = generate_doc_file(config)
            target_paths["docs"] = DOCS_DIR / "tools" / f"{tool_name}.md"

    except Exception as e:
        logger.error(f"❌ Lỗi nghiêm trọng khi tạo nội dung code: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    return generated_content, target_paths, module_path
