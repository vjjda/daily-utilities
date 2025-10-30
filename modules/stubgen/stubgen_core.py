# Path: modules/stubgen/stubgen_core.py
"""
Core logic for the Stub Generator (sgen) module.
Handles Orchestration (Pure Logic).
"""

import logging
import ast
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pathspec

# Import các thành phần của module
from .stubgen_parser import (
    extract_module_list,
    collect_all_exported_symbols
)
from .stubgen_loader import find_gateway_files, load_config_files
from .stubgen_merger import merge_stubgen_configs
from .stubgen_formatter import format_stub_content

# Import tiện ích chung
from utils.core import (
    load_text_template,
    compile_spec_from_patterns
)

MODULE_DIR = Path(__file__).parent
TEMPLATE_FILENAME = "pyi.py.template"

StubResult = Dict[str, Any]

__all__ = ["process_stubgen_logic"]


def process_stubgen_logic(
    logger: logging.Logger, 
    scan_root: Path,
    cli_args: argparse.Namespace,
    script_file_path: Path
) -> List[StubResult]:
    """
    Điều phối toàn bộ quá trình tạo stub (Logic thuần túy, không I/O ghi).
    Luồng xử lý:
    1. Tải template .pyi.template.
    2. Tải cấu hình từ file .toml (gọi Loader).
    3. Chuẩn bị config từ CLI.
    4. Hợp nhất config (gọi Merger).
    5. Biên dịch PathSpecs.
    6. Tìm các file gateway (gọi Loader).
    7. Phân tích AST (gọi Parser).
    8. Định dạng nội dung stub (gọi Formatter).
    9. Trả về danh sách các đối tượng kết quả (StubResult).
    Args:
        logger: Logger.
        scan_root: Thư mục gốc để quét.
        cli_args: Namespace đối số thô từ entrypoint.
        script_file_path: Đường dẫn của chính script sgen (để bỏ qua).
    Returns:
        List[StubResult]: Danh sách các dict chứa thông tin file stub.
    """
    
    # 1. Load Template (I/O Đọc)
    try:
        template_path = MODULE_DIR / TEMPLATE_FILENAME
        stub_template_str = load_text_template(template_path, logger)
    except Exception as e:
        logger.error(f"❌ Không thể tải PYI template: {e}")
        raise

    # 2. Load File Config (I/O Đọc)
    file_config = load_config_files(scan_root, logger)

    # 3. Chuẩn bị CLI Config
    cli_config: Dict[str, Optional[str]] = {
        "ignore": getattr(cli_args, 'ignore', None),
        "include": getattr(cli_args, 'include', None)
    }

    # 4. Hợp nhất Configs (gọi Merger)
    merged_config = merge_stubgen_configs(logger, cli_config, file_config)

    # 5. Biên dịch Specs
    final_include_spec: Optional['pathspec.PathSpec'] = compile_spec_from_patterns(
        merged_config["include_list"], 
        scan_root
    )
    
    # 6. Load: Tìm file gateway (I/O Đọc)
    gateway_files = find_gateway_files(
        logger=logger, 
        scan_root=scan_root,
        ignore_list=merged_config["ignore_list"], 
        include_spec=final_include_spec,
        dynamic_import_indicators=merged_config["indicators"],
        script_file_path=script_file_path
    )
    
    if not gateway_files:
        return []
        
    results: List[StubResult] = []
    logger.info(f"✅ Found {len(gateway_files)} dynamic gateways to process.")

    for init_file in gateway_files:
        
        # 7. Parse (AST)
        submodule_stems = extract_module_list(
            init_file, 
            ast_module_list_name=merged_config["module_list_name"]
        )
        exported_symbols = collect_all_exported_symbols(
            init_file, 
            submodule_stems, 
            ast_all_list_name=merged_config["all_list_name"]
        )
        
        if not exported_symbols:
            logger.warning(f"Skipping {init_file.name}: No exported symbols found.")
            continue

        # 8. Format (gọi Formatter)
        stub_content = format_stub_content(
            init_file, 
            scan_root, 
            exported_symbols,
            stub_template_str 
        )

        stub_path = init_file.with_suffix(".pyi")
        
        # 9. Gom kết quả (Pure Result Object)
        results.append({
            "init_path": init_file,
            "stub_path": stub_path,
            "content": stub_content,
            "symbols_count": len(exported_symbols),
            "rel_path": stub_path.relative_to(scan_root).as_posix()
        })
        
    return results