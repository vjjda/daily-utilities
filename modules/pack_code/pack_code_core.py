# Path: modules/pack_code/pack_code_core.py
"""
Core logic for pack_code (Orchestrator).

Responsible for coordinating the packing process including loading configuration,
scanning files, resolving filters, generating the directory tree, reading file
contents, and assembling the final output string. This module contains pure
business logic with read I/O for configuration and file content.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING, Iterable, Tuple

# Import module components
from .pack_code_scanner import scan_files
from .pack_code_tree import generate_tree_string
from .pack_code_loader import load_files_content, load_config_files
from .pack_code_resolver import (
    resolve_start_and_scan_paths,
    resolve_filters,
    resolve_output_path
)
from .pack_code_builder import assemble_packed_content
from .pack_code_config import DEFAULT_START_PATH # Needed for default path resolution

__all__ = ["process_pack_code_logic"]


def process_pack_code_logic(
    logger: logging.Logger,
    cli_args: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Main logic function (Orchestrator) for pack_code.

    Coordinates loading configuration, scanning, filtering, tree generation,
    reading content, and packing. Handles read I/O for config and content only.

    Args:
        logger: The logger instance.
        cli_args: A dictionary containing processed CLI arguments from the entrypoint.
                  Expected keys include 'start_path' (Optional[Path]), 'output' (Optional[Path]),
                  'stdout' (bool), 'extensions' (Optional[str]), 'ignore' (Optional[str]),
                  'no_gitignore' (bool), 'dry_run' (bool), 'no_header' (bool),
                  'no_tree' (bool), 'copy_to_clipboard' (bool).

    Returns:
        A dictionary ("Result Object") containing data for the Executor:
        {
            'status': 'ok' | 'empty' | 'error',
            'final_content': str (if status='ok'),
            'output_path': Optional[Path] (path before expansion, if status='ok'),
            'stdout': bool,
            'dry_run': bool,
            'copy_to_clipboard': bool,
            'file_list_relative': List[Path] (relative to scan_root),
            'scan_root': Path (resolved absolute path),
            'tree_string': str (potentially empty),
            'no_tree': bool,
            'message': str (if status='error')
        }
    """
    logger.info("Core logic running...")

    try:
        # 1. Determine the directory to load configuration from
        start_path_from_cli: Optional[Path] = cli_args.get("start_path")
        # Use start_path if provided, otherwise CWD
        temp_path_for_config = start_path_from_cli if start_path_from_cli else Path.cwd().resolve()

        config_load_dir: Path
        if temp_path_for_config.is_file():
            config_load_dir = temp_path_for_config.parent
        else: # Directory or CWD
            config_load_dir = temp_path_for_config

        logger.debug(f"Loading configuration from: {config_load_dir.as_posix()}")
        file_config = load_config_files(config_load_dir, logger)

        # 2. Extract primary boolean flags
        dry_run: bool = cli_args.get("dry_run", False)
        no_tree: bool = cli_args.get("no_tree", False)

        # 3. Resolve start path and scan root (Git root or fallback)
        start_path, scan_root = resolve_start_and_scan_paths(
            logger, start_path_from_cli # Pass Optional[Path]
        )

        # 4. Resolve filters (extensions, ignore, submodules)
        ext_filter_set, ignore_spec, submodule_paths = resolve_filters(
            logger, cli_args, file_config, scan_root
        )

        # 5. Scan for files based on resolved filters
        files_to_pack = scan_files(
            logger, start_path, ignore_spec, ext_filter_set, submodule_paths, scan_root
        )

        if not files_to_pack:
            logger.warning("No files found matching the criteria.")
            return {'status': 'empty'}
        logger.info(f"Found {len(files_to_pack)} file(s) to pack.")

        # 6. Generate directory tree string (if needed)
        tree_str = ""
        if not no_tree:
            logger.debug("Generating directory tree...")
            tree_str = generate_tree_string(start_path, files_to_pack, scan_root)

        # 7. Read file content (if not a pure dry run)
        files_content: Dict[Path, str] = {}
        # Only skip reading if dry_run is true AND no_tree is true
        if not (dry_run and no_tree):
            files_content = load_files_content(logger, files_to_pack, scan_root)

        # 8. Assemble final packed content string
        final_content = assemble_packed_content(
            files_to_pack=files_to_pack,
            files_content=files_content,
            scan_root=scan_root,
            tree_str=tree_str,
            no_header=cli_args.get("no_header", False),
            dry_run=dry_run, # Builder skips content if dry_run
        )

        # 9. Resolve the output file path (prioritizing CLI)
        final_output_path = resolve_output_path(
            logger, cli_args, file_config, start_path
        )

        # 10. Return the Result Object for the Executor
        return {
            'status': 'ok',
            'final_content': final_content,
            'output_path': final_output_path, # May be None
            'stdout': cli_args.get("stdout", False),
            'dry_run': dry_run,
            'copy_to_clipboard': cli_args.get("copy_to_clipboard", False),
            'file_list_relative': [p.relative_to(scan_root) for p in files_to_pack],
            'scan_root': scan_root,
            'tree_string': tree_str, # May be empty
            'no_tree': no_tree
        }

    except FileNotFoundError as e:
        # Raised by resolve_start_and_scan_paths if start_path is invalid
        logger.error(f"❌ {e}")
        return {'status': 'error', 'message': str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in pack_code core logic: {e}")
        logger.debug("Traceback:", exc_info=True)
        return {'status': 'error', 'message': f"Unexpected error: {e}"}