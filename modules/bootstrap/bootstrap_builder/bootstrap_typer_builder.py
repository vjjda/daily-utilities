# Path: modules/bootstrap/bootstrap_builder/bootstrap_typer_builder.py

from typing import Dict, Any, List, Optional as TypingOptional


from ..bootstrap_config import TYPE_HINT_MAP, TYPING_IMPORTS
from ..bootstrap_utils import get_cli_args

__all__ = [
    "build_typer_app_code",
    "build_typer_path_expands",
    "build_typer_args_pass_to_core",
    "build_typer_main_signature",
]


def build_typer_app_code(config: Dict[str, Any]) -> str:
    cli_config = config.get("cli", {})
    help_config = cli_config.get("help", {})

    desc = help_config.get("description", f"Mô tả cho {config['meta']['tool_name']}.")
    epilog = help_config.get("epilog", "")

    code_lines = [
        f"app = typer.Typer(",
        f"    help={repr(desc)},",
        f"    epilog={repr(epilog)},",
        f"    add_completion=False,",
        f"    context_settings={{",
        f"        'help_option_names': ['--help', '-h'],",
        f"    }}",
        f")",
    ]
    return "\n".join(code_lines)


def build_typer_path_expands(config: Dict[str, Any]) -> str:
    code_lines: List[str] = []
    path_args = [arg for arg in get_cli_args(config) if arg.get("type") == "Path"]

    if not path_args:
        code_lines.append("    # (Không có đối số Path nào cần expand)")
        return "\n".join(code_lines)

    for arg in path_args:
        name = arg["name"]
        var_name = f"{name}_expanded"

        if arg.get("is_argument") and "default" not in arg:
            code_lines.append(f"    {var_name} = {name}.expanduser()")
        else:

            code_lines.append(
                f"    {var_name} = {name}.expanduser() if {name} else None"
            )

    return "\n".join(code_lines)


def build_typer_args_pass_to_core(config: Dict[str, Any]) -> str:
    code_lines: List[str] = []
    args = get_cli_args(config)

    if not args:
        code_lines.append("        # (Không có đối số CLI nào để truyền)")
        return "\n".join(code_lines)

    for arg in args:
        name = arg["name"]
        if arg.get("type") == "Path":

            var_name = f"{name}_expanded"
            code_lines.append(f"        {name}={var_name},")
        else:

            code_lines.append(f"        {name}={name},")

    return "\n".join(code_lines)


def build_typer_main_signature(config: Dict[str, Any]) -> str:
    code_lines: List[str] = [f"def main(", f"    ctx: typer.Context,"]

    args = get_cli_args(config)

    needs_optional = any(
        not arg.get("is_argument", False)
        and "default" not in arg
        and arg.get("type") != "bool"
        for arg in args
    )

    if needs_optional:

        pass

    for arg in args:
        name = arg["name"]
        spec_type = arg["type"]
        py_type = TYPE_HINT_MAP.get(spec_type, "str")
        help_str = arg.get("help", f"Tham số {name}.")

        default_repr: str = "..."
        type_hint = py_type

        is_argument = arg.get("is_argument", False)

        if "default" in arg:

            if py_type == "bool":

                default_repr = str(arg["default"]).capitalize()
            else:

                default_repr = f"DEFAULT_{name.upper()}"
        else:

            if py_type == "bool":
                default_repr = "False"
            else:
                if is_argument:

                    default_repr = "..."
                else:

                    default_repr = "None"

                    type_hint = f"Optional[{type_hint}]"

        if is_argument:
            code_lines.append(f"    {name}: {type_hint} = typer.Argument(")
            code_lines.append(f"        {default_repr},")
            code_lines.append(f"        help={repr(help_str)}")

            code_lines.append(f"    ),")
        else:
            code_lines.append(f"    {name}: {type_hint} = typer.Option(")
            code_lines.append(f"        {default_repr},")

            option_names: List[str] = []

            if "short" in arg:
                option_names.append(f"\"{arg['short']}\"")

            option_names.append(f'"--{name}"')

            code_lines.append(f"        {', '.join(option_names)},")

            code_lines.append(f"        help={repr(help_str)}")

            code_lines.append(f"    ),")

    code_lines.append(f"):")
    return "\n".join(code_lines)