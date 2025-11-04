# Path: modules/stubgen/stubgen_internal/gateway_processor.py
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


from .stubgen_parser import extract_module_list, collect_all_exported_symbols
from .stubgen_formatter import format_stub_content

__all__ = ["process_single_gateway"]


def process_single_gateway(
    init_file: Path,
    scan_root: Path,
    merged_config: Dict[str, Any],
    stub_template_str: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], int]:

    try:

        submodule_stems = extract_module_list(
            init_file, ast_module_list_name=merged_config["module_list_name"]
        )
        exported_symbols = collect_all_exported_symbols(
            init_file, submodule_stems, ast_all_list_name=merged_config["all_list_name"]
        )

        if not exported_symbols:

            return None, 0

        stub_content = format_stub_content(
            init_file, scan_root, exported_symbols, stub_template_str
        )
        return stub_content, len(exported_symbols)

    except Exception as e:
        logger.error(f"❌ Lỗi khi xử lý file {init_file.name}: {e}")
        return None, 0
