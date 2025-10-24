# Path: scripts/internal/bootstrap_generator.py

"""
Bộ não tạo code cho bootstrap_tool.py.

Chịu trách nhiệm load template từ thư mục /bootstrap_templates/
và điền dữ liệu từ config TOML vào.
(Đã refactor cho Typer và SRP)
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

# Đường dẫn đến thư mục chứa các file .template
TEMPLATE_DIR = Path(__file__).parent / "bootstrap_templates"
# Ánh xạ type TOML sang Python type hint
TYPE_HINT_MAP = {"int": "int", "str": "str", "bool": "bool", "Path": "Path"}
# Các type cần import từ 'typing'
TYPING_IMPORTS = {"Optional", "List"}


def _load_template(template_name: str) -> str:
    """Helper: Đọc nội dung từ một file template."""
    try:
        template_path = TEMPLATE_DIR / template_name
        return template_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logging.error(f"Lỗi nghiêm trọng: Không tìm thấy template '{template_name}'")
        raise
    except Exception as e:
        logging.error(f"Lỗi khi đọc template '{template_name}': {e}")
        raise

# --- Helper functions (Đã viết lại) ---

def _get_cli_args(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Helper: Lấy danh sách [[cli.args]] từ config."""
    return config.get('cli', {}).get('args', [])

def _build_config_constants(config: Dict[str, Any]) -> str:
    """Tạo code Python cho các hằng số default."""
    code_lines = []
    default_args = [arg for arg in _get_cli_args(config) if 'default' in arg]
    
    if not default_args:
        code_lines.append("# (No default constants defined in tool.spec.toml)")
        
    for arg in default_args:
        name = arg['name']
        const_name = f"DEFAULT_{name.upper()}"
        # repr() tự động thêm dấu ngoặc kép cho chuỗi, giữ nguyên số
        const_value = repr(arg['default'])
        code_lines.append(f"{const_name} = {const_value}")
            
    return "\n".join(code_lines)

def _build_config_all_constants(config: Dict[str, Any]) -> str:
    """Tạo danh sách __all__ cho file config."""
    default_args = [arg for arg in _get_cli_args(config) if 'default' in arg]
    if not default_args:
        return "" # Trả về rỗng
        
    const_names = []
    for arg in default_args:
        const_name = f"DEFAULT_{arg['name'].upper()}"
        const_names.append(f'"{const_name}"') # Thêm dấu ngoặc kép
            
    return ", ".join(const_names)

def _build_config_imports(module_name: str, config: Dict[str, Any]) -> str:
    """Tạo code Python cho các (import) hằng số default."""
    default_args = [arg for arg in _get_cli_args(config) if 'default' in arg]
    
    if not default_args:
        return "# (No default constants to import)"
        
    const_names = []
    for arg in default_args:
        const_name = f"DEFAULT_{arg['name'].upper()}"
        const_names.append(const_name)
        
    import_list = ", ".join(const_names)
    return f"from modules.{module_name}.{module_name}_config import {import_list}"

def _build_typer_app_code(config: Dict[str, Any]) -> str:
    """Tạo code Typer App() từ [cli.help]."""
    help_config = config.get('cli', {}).get('help', {})
    desc = help_config.get('description', f"Mô tả cho {config['meta']['tool_name']}.")
    epilog = help_config.get('epilog', "")
    
    code_lines = [
        f"app = typer.Typer(",
        f"    help=\"{desc}\",",
        f"    epilog=\"{epilog}\",",
        f"    add_completion=False,",
        f"    context_settings={{'help_option_names': ['--help', '-h']}}",
        f")"
    ]
    return "\n".join(code_lines)

def _build_typer_path_expands(config: Dict[str, Any]) -> str:
    """Tạo code .expanduser() cho các tham số Path."""
    code_lines = []
    path_args = [arg for arg in _get_cli_args(config) if arg.get('type') == 'Path']
    if not path_args:
        code_lines.append("# (No Path arguments to expand)")
        
    for arg in path_args:
        name = arg['name']
        # Tạo biến mới với suffix _expanded
        code_lines.append(f"    {name}_expanded = {name}.expanduser() if {name} else None")
            
    return "\n".join(code_lines)

def _build_typer_args_pass_to_core(config: Dict[str, Any]) -> str:
    """Tạo các kwargs để truyền vào hàm core_logic."""
    code_lines = []
    args = _get_cli_args(config)
    if not args:
        code_lines.append("            # (No CLI args to pass)")
        
    for arg in args:
        name = arg['name']
        # Nếu là Path, truyền biến _expanded
        if arg.get('type') == 'Path':
            code_lines.append(f"            {name}={name}_expanded,")
        else:
            code_lines.append(f"            {name}={name},")
            
    return "\n".join(code_lines)

def _build_typer_main_function_signature(config: Dict[str, Any]) -> str:
    """Tạo chữ ký hàm def main(...) cho Typer."""
    code_lines = [
        f"def main(",
        f"    ctx: typer.Context,"
    ]
    
    args = _get_cli_args(config)
    
    for arg in args:
        name = arg['name']
        py_type = TYPE_HINT_MAP.get(arg['type'], 'str')
        help_str = arg.get('help', f"The {name} argument.")
        
        # Xử lý default và Optional
        if 'default' in arg:
            default_const = f"DEFAULT_{name.upper()}"
            type_hint = py_type # "int"
        else:
            # Không có default (trừ bool)
            if py_type == 'bool':
                # Cờ bool không có default là False
                default_const = "False"
                type_hint = "bool"
            else:
                default_const = "None"
                type_hint = f"Optional[{py_type}]"
        
        # Xử lý Argument vs Option
        if arg.get('is_argument', False):
            # Đây là Positional Argument
            code_lines.append(f"    {name}: {type_hint} = typer.Argument(")
            code_lines.append(f"        {default_const},")
            code_lines.append(f"        help=\"{help_str}\"")
            code_lines.append(f"    ),")
        else:
            # Đây là Option (flag)
            code_lines.append(f"    {name}: {type_hint} = typer.Option(")
            code_lines.append(f"        {default_const},")
            
            # Thêm cờ ngắn (ví dụ: "-L")
            if 'short' in arg:
                code_lines.append(f"        \"{arg['short']}\",")
                
            # Thêm cờ dài (ví dụ: "--level")
            code_lines.append(f"        \"--{name}\",")
            code_lines.append(f"        help=\"{help_str}\"")
            code_lines.append(f"    ),")

    code_lines.append(f"):")
    return "\n".join(code_lines)


# --- CÁC HÀM GENERATE CHÍNH ---

def generate_bin_wrapper(config: Dict[str, Any]) -> str:
    """Tạo nội dung cho file wrapper Zsh trong /bin/"""
    # (Không thay đổi)
    template = _load_template("bin_wrapper.zsh.template")
    return template.format(
        tool_name=config['meta']['tool_name'],
        script_file=config['meta']['script_file']
    )

def generate_script_entrypoint(config: Dict[str, Any]) -> str:
    """Tạo nội dung cho file entrypoint Python trong /scripts/"""
    template = _load_template("script_entrypoint.py.template")
    
    # (Gọi các hàm generator mới)
    config_imports_code = _build_config_imports(config['module_name'], config)
    typer_app_code = _build_typer_app_code(config)
    typer_main_sig = _build_typer_main_function_signature(config)
    typer_path_expands = _build_typer_path_expands(config)
    typer_args_pass = _build_typer_args_pass_to_core(config)

    return template.format(
        script_file=config['meta']['script_file'],
        logger_name=config['meta']['logger_name'],
        module_name=config['module_name'],
        config_imports=config_imports_code,
        typer_app_code=typer_app_code,
        typer_main_function_signature=typer_main_sig,
        typer_path_expands=typer_path_expands,
        typer_args_pass_to_core=typer_args_pass
    )

def generate_module_file(config: Dict[str, Any], file_type: str) -> str:
    """Tạo nội dung cho các file _config, _core, _executor, _loader"""
    template_name_map = {
        "config": "module_config.py.template",
        "core": "module_core.py.template",
        "executor": "module_executor.py.template",
        "loader": "module_loader.py.template", # (Mới)
    }
    template_name = template_name_map[file_type]
    template = _load_template(template_name)
    
    format_dict = {"module_name": config['module_name']}
    
    if file_type == "config":
        config_constants_code = _build_config_constants(config)
        config_all_code = _build_config_all_constants(config)
        format_dict["config_constants"] = config_constants_code
        format_dict["config_all_constants"] = config_all_code
    
    return template.format(**format_dict)

def generate_module_init_file(config: Dict[str, Any]) -> str:
    """Tạo file gateway __init__.py."""
    template = _load_template("module_init.py.template")
    return template.format(module_name=config['module_name'])

def generate_doc_file(config: Dict[str, Any]) -> str:
    """Tạo file tài liệu Markdown (tùy chọn)"""
    # (Không thay đổi)
    template = _load_template("doc_file.md.template")
    
    return template.format(
        tool_name=config['meta']['tool_name'],
        short_description=config.get('docs', {}).get('short_description', f'Tài liệu cho {config["meta"]["tool_name"]}.')
    )