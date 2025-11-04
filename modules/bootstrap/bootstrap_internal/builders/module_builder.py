# Path: modules/bootstrap/bootstrap_internal/builders/module_builder.py
from typing import Any, Dict

from ..bootstrap_loader import load_template
from .snippet_config import (
    build_config_all_list,
    build_config_constants,
)

__all__ = ["generate_module_file", "generate_module_init_file"]


def generate_module_file(
    config: Dict[str, Any], file_type: str, relative_path: str
) -> str:
    template_name_map = {
        "config": "module_config.py.template",
        "core": "module_core.py.template",
        "executor": "module_executor.py.template",
        "loader": "module_loader.py.template",
    }
    template_name = template_name_map[file_type]
    template = load_template(template_name)

    format_dict = {
        "module_name": config["module_name"],
        "relative_path": relative_path,
    }

    if file_type == "config":
        config_constants_code = build_config_constants(config)
        config_all_code = build_config_all_list(config)
        format_dict["config_constants"] = config_constants_code
        format_dict["config_all_constants"] = config_all_code

    return template.format(**format_dict)


def generate_module_init_file(config: Dict[str, Any], relative_path: str) -> str:
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
        relative_path=relative_path,
    )
