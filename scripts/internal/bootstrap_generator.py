#!/usr/bin/env python3
# Path: scripts/internal/bootstrap_generator.py

"""
Bộ não tạo code cho bootstrap_tool.py.

Chịu trách nhiệm load template từ thư mục /bootstrap_templates/
và điền dữ liệu từ config TOML vào.
"""

import logging
from pathlib import Path
from typing import Dict, Any

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

def _build_argparse_code(argparse_config: Dict[str, Any]) -> str:
    """
    Tạo code Python cho phần parser.add_argument().
    (Logic này giữ nguyên, vì nó là logic Python thuần túy)
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
        name_or_flags = []
        kwargs_str = []
        name = arg.pop('name')
        
        if arg.pop('positional', False):
            name_or_flags.append(f'"{name}"')
        else:
            if 'short' in arg: name_or_flags.append(f'"{arg.pop("short")}"')
            if 'long' in arg: name_or_flags.append(f'"{arg.pop("long")}"')
        
        if 'type' in arg and arg['type'] in TYPE_MAP:
            kwargs_str.append(f"type={TYPE_MAP[arg.pop('type')]}")
            
        if 'action' in arg:
            kwargs_str.append(f'action="store_true"')
            arg.pop('action')
            
        if 'choices' in arg:
            kwargs_str.append(f"choices={arg.pop('choices')}")
            
        for key, value in arg.items():
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
    
    return template.format(
        script_file=config['meta']['script_file'],
        logger_name=config['meta']['logger_name'],
        module_name=config['module_name'],
        argparse_code=argparse_code
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
    
    return template.format(
        module_name=config['module_name']
    )

def generate_doc_file(config: Dict[str, Any]) -> str:
    """Tạo file tài liệu Markdown (tùy chọn)"""
    template = _load_template("doc_file.md.template")
    
    return template.format(
        tool_name=config['meta']['tool_name'],
        short_description=config.get('docs', {}).get('short_description', f'Tài liệu cho {config["meta"]["tool_name"]}.')
    )