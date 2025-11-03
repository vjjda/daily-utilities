# Path: modules/bootstrap/bootstrap_internal/bootstrap_generator.py
from typing import Dict, Any, Optional


from .bootstrap_loader import load_template

from .bootstrap_config_builder import (
    build_config_constants,
    build_config_all_list,
    build_config_imports,
)
from .bootstrap_typer_builder import (
    build_typer_app_code,
    build_typer_path_expands,
    build_typer_args_pass_to_core,
    build_typer_main_signature,
)
from .bootstrap_argparse_builder import (
    build_argparse_arguments,
    build_path_expands as build_argparse_path_expands,
    build_args_pass_to_core as build_argparse_args_pass_to_core,
)

__all__ = [
    "generate_script_entrypoint",
    "generate_module_file",
    "generate_module_init_file",
    "generate_doc_file",
]


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
    return template.format(module_name=config["module_name"])


def generate_doc_file(config: Dict[str, Any]) -> str:

    template = load_template("doc_file.md.template")

    return template.format(
        tool_name=config["meta"]["tool_name"],
        short_description=config.get("docs", {}).get(
            "short_description", f'Tài liệu cho {config["meta"]["tool_name"]}.'
        ),
    )
