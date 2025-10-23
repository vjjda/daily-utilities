# Path: scripts/internal/bootstrap_generator.py

"""
Bộ não tạo code cho bootstrap_tool.py.

Chịu trách nhiệm load template từ thư mục /bootstrap_templates/
và điền dữ liệu từ config TOML vào.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

# Đường dẫn đến thư mục chứa các file .template
TEMPLATE_DIR = Path(__file__).parent / "bootstrap_templates"

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

# --- NEW: Helper functions ---

def _get_default_args(argparse_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Helper to filter args that have a 'default' and are not 'store_true'."""
    default_args = []
    args_list = argparse_config.get('args', [])
    for arg in args_list:
        if 'default' in arg and arg.get('action') != 'store_true':
            default_args.append(arg)
    return default_args

def _build_config_constants(argparse_config: Dict[str, Any]) -> str:
    """Tạo code Python cho các hằng số default."""
    code_lines = []
    default_args = _get_default_args(argparse_config)
    
    if not default_args:
        code_lines.append("# (No default constants defined in tool.spec.toml)")
        
    for arg in default_args:
        name = arg['name']
        const_name = f"DEFAULT_{name.upper()}"
        # repr() tự động thêm dấu ngoặc kép cho chuỗi, giữ nguyên số
        const_value = repr(arg['default'])
        code_lines.append(f"{const_name} = {const_value}")
            
    return "\n".join(code_lines)

def _build_config_imports(module_name: str, argparse_config: Dict[str, Any]) -> str:
    """Tạo code Python cho các (import) hằng số default."""
    default_args = _get_default_args(argparse_config)
    
    if not default_args:
        return "# (No default constants to import)"
        
    const_names = []
    for arg in default_args:
        const_name = f"DEFAULT_{arg['name'].upper()}"
        const_names.append(const_name)
        
    import_list = ", ".join(const_names)
    return f"from modules.{module_name}.{module_name}_config import {import_list}"

def _build_argparse_code(argparse_config: Dict[str, Any]) -> str:
    """
    Tạo code Python cho phần parser.add_argument().
    """
    code_lines = []
    
    desc = argparse_config.get('description', "Mô tả cho tool mới.")
    epilog = argparse_config.get('epilog', "")
    
    code_lines.append(f'    parser = argparse.ArgumentParser(')
    code_lines.append(f'        description="{desc}",')
    code_lines.append(f'        epilog="{epilog}"')
    code_lines.append(f'    )')
    code_lines.append(f'')
    
    TYPE_MAP = {"int": "int", "float": "float", "str": "str"}
    
    args_list = argparse_config.get('args', [])
    if not args_list:
        code_lines.append("    # (Chưa có argument nào được định nghĩa trong tool.spec.toml)")
        
    for arg in args_list:
        # Tạo bản sao để pop an toàn
        arg_copy = arg.copy()
        
        name_or_flags = []
        kwargs_str = []
        name = arg_copy.pop('name')
        
        if arg_copy.pop('positional', False):
            name_or_flags.append(f'"{name}"')
        else:
            if 'short' in arg_copy: name_or_flags.append(f'"{arg_copy.pop("short")}"')
            if 'long' in arg_copy: name_or_flags.append(f'"{arg_copy.pop("long")}"')
        
        if 'type' in arg_copy and arg_copy['type'] in TYPE_MAP:
            kwargs_str.append(f"type={TYPE_MAP[arg_copy.pop('type')]}")
            
        if 'action' in arg_copy:
            kwargs_str.append(f'action="store_true"')
            arg_copy.pop('action')
            # Không xử lý default nếu là store_true
            if 'default' in arg_copy:
                arg_copy.pop('default')
            
        if 'choices' in arg_copy:
            kwargs_str.append(f"choices={arg_copy.pop('choices')}")
            
        # --- MODIFIED LOGIC: Sử dụng hằng số cho default ---
        if 'default' in arg_copy:
            const_name = f"DEFAULT_{name.upper()}"
            kwargs_str.append(f"default={const_name}")
            arg_copy.pop('default')
        # --- END MODIFIED LOGIC ---
            
        # Xử lý các key còn lại (ví dụ: help, nargs)
        for key, value in arg_copy.items():
            kwargs_str.append(f'{key}="{value}"' if isinstance(value, str) else f'{key}={value}')
            
        args_joined = ", ".join(name_or_flags)
        kwargs_joined = ", ".join(kwargs_str)
        code_lines.append(f"    parser.add_argument({args_joined}, {kwargs_joined})")


    code_lines.append(f"")
    code_lines.append(f"    args = parser.parse_args()")
    return "\n".join(code_lines)

# --- CÁC HÀM GENERATE CHÍNH ---

def generate_bin_wrapper(config: Dict[str, Any]) -> str:
    """Tạo nội dung cho file wrapper Zsh trong /bin/"""
    template = _load_template("bin_wrapper.zsh.template")
    return template.format(
        tool_name=config['meta']['tool_name'],
        script_file=config['meta']['script_file']
    )

def generate_script_entrypoint(config: Dict[str, Any]) -> str:
    """Tạo nội dung cho file entrypoint Python trong /scripts/"""
    template = _load_template("script_entrypoint.py.template")
    argparse_code = _build_argparse_code(config['argparse'])
    # --- NEW ---
    config_imports_code = _build_config_imports(config['module_name'], config['argparse'])
    # --- END NEW ---
    
    return template.format(
        script_file=config['meta']['script_file'],
        logger_name=config['meta']['logger_name'],
        module_name=config['module_name'],
        argparse_code=argparse_code,
        config_imports=config_imports_code # <-- Pass new placeholder
    )

def generate_module_file(config: Dict[str, Any], file_type: str) -> str:
    """Tạo nội dung cho các file _config, _core, _executor"""
    template_name_map = {
        "config": "module_config.py.template",
        "core": "module_core.py.template",
        "executor": "module_executor.py.template"
    }
    template_name = template_name_map[file_type]
    template = _load_template(template_name)
    
    # --- NEW: Thêm hằng số vào placeholder ---
    format_dict = {"module_name": config['module_name']}
    
    if file_type == "config":
        config_constants_code = _build_config_constants(config['argparse'])
        format_dict["config_constants"] = config_constants_code
    # --- END NEW ---

    # Dùng **kwargs để các template khác (core, executor)
    # bỏ qua placeholder 'config_constants' một cách an toàn
    return template.format(**format_dict)

def generate_doc_file(config: Dict[str, Any]) -> str:
    """Tạo file tài liệu Markdown (tùy chọn)"""
    template = _load_template("doc_file.md.template")
    
    return template.format(
        tool_name=config['meta']['tool_name'],
        short_description=config.get('docs', {}).get('short_description', f'Tài liệu cho {config["meta"]["tool_name"]}.')
    )