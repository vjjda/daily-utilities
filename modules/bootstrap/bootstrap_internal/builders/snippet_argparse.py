# Path: modules/bootstrap/bootstrap_internal/builders/snippet_argparse.py
from typing import Dict, Any, List
from pathlib import Path


from .builder_utils import get_cli_args

__all__ = ["build_argparse_arguments", "build_path_expands", "build_args_pass_to_core"]


def build_argparse_arguments(config: Dict[str, Any]) -> str:

    code_lines: List[str] = []
    args = get_cli_args(config)

    if not args:
        code_lines.append("    # (Không có đối số CLI nào được định nghĩa trong spec)")
        return "\n".join(code_lines)

    for arg in args:
        name = arg["name"]
        py_type_str = arg.get("type", "str")
        help_str = arg.get("help", f"Văn bản trợ giúp cho {name}.")
        is_argument = arg.get("is_argument", False)

        arg_params: List[str] = []

        if is_argument:
            arg_params.append(f'        "{name}",')
        else:
            name_flags = [f'"--{name}"']
            if "short" in arg:
                name_flags.insert(0, f"\"{arg['short']}\"")
            arg_params.append(f"        {', '.join(name_flags)},")

        if py_type_str == "bool":
            if arg.get("default", False) is True:
                arg_params.append(f'        action="store_false",')
            else:
                arg_params.append(f'        action="store_true",')
        elif py_type_str == "int":
            arg_params.append(f"        type=int,")
        else:
            arg_params.append(f"        type=str,")

        if is_argument:
            if "default" in arg:
                arg_params.append(f'        nargs="?",')
                arg_params.append(f"        default={repr(arg['default'])},")
        else:
            if py_type_str != "bool":
                if "default" in arg:
                    arg_params.append(f"        default={repr(arg['default'])},")
                else:
                    arg_params.append(f"        default=None,")

        arg_params.append(f"        help={repr(help_str)}")

        code_lines.append(f"    parser.add_argument(")
        code_lines.extend(arg_params)
        code_lines.append(f"    )")

    return "\n".join(code_lines)


def build_path_expands(config: Dict[str, Any]) -> str:

    code_lines: List[str] = []
    path_args = [arg for arg in get_cli_args(config) if arg.get("type") == "Path"]

    if not path_args:
        code_lines.append("    # (Không có đối số Path nào cần expand)")
        return "\n".join(code_lines)

    for arg in path_args:
        name = arg["name"]
        var_name = f"{name}_path"

        if arg.get("is_argument") and "default" not in arg:
            code_lines.append(f"    {var_name} = Path(args.{name}).expanduser()")
        else:
            code_lines.append(
                f"    {var_name} = Path(args.{name}).expanduser() if args.{name} else None"
            )

    return "\n".join(code_lines)


def build_args_pass_to_core(config: Dict[str, Any]) -> str:

    code_lines: List[str] = []
    args = get_cli_args(config)

    if not args:
        code_lines.append("        # (Không có đối số CLI nào để truyền)")
        return "\n".join(code_lines)

    for arg in args:
        name = arg["name"]

        if arg.get("type") == "Path":
            var_name = f"{name}_path"
            code_lines.append(f"        {name}={var_name},")
        else:
            code_lines.append(f"        {name}=args.{name},")

    return "\n".join(code_lines)
