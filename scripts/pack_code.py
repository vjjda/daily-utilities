#!/usr/bin/env python3
# Path: scripts/pack_code.py

"""
Entrypoint (command-line interface) for pcode (Pack Code).

This script handles:
1. Setting up `sys.path` for project imports.
2. Parsing command-line arguments using Argparse.
3. Configuring logging.
4. Handling configuration initialization requests (`--config-local`, `--config-project`).
5. Preparing a dictionary of basic CLI arguments for the core logic.
6. Invoking the core processing logic (`process_pack_code_logic`).
7. Invoking the execution logic (`execute_pack_code_action`) based on the results.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Final

# Set up sys.path to allow importing project modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    # Import shared utilities
    from utils.logging_config import setup_logging, log_success
    from utils.cli import handle_config_init_request
    from utils.core import parse_comma_list

    # Import pack_code specific components
    from modules.pack_code.pack_code_config import (
        DEFAULT_START_PATH, DEFAULT_EXTENSIONS, DEFAULT_IGNORE,
        DEFAULT_OUTPUT_DIR,
        PROJECT_CONFIG_FILENAME, CONFIG_FILENAME, CONFIG_SECTION_NAME
    )
    from modules.pack_code import (
        process_pack_code_logic,
        execute_pack_code_action,
    )
except ImportError as e:
    print(f"Error: Failed to import project utilities/modules. Error: {e}", file=sys.stderr)
    sys.exit(1)

# --- Constants Specific to this Entrypoint ---
MODULE_DIR: Final[Path] = PROJECT_ROOT / "modules" / "pack_code"
TEMPLATE_FILENAME: Final[str] = "pack_code.toml.template"

# Default values used for populating the config template during initialization
PCODE_DEFAULTS: Final[Dict[str, Any]] = {
    "output_dir": DEFAULT_OUTPUT_DIR,
    "extensions": list(parse_comma_list(DEFAULT_EXTENSIONS)), # Convert to list for TOML
    "ignore": list(parse_comma_list(DEFAULT_IGNORE)),       # Convert to list for TOML
}

def main():
    """Main function orchestrating the CLI execution."""

    # 1. Define Command-Line Argument Parser
    parser = argparse.ArgumentParser(
        description="Packs the content of multiple files/directories into a single text file.",
        epilog="Example: pcode ./src -e 'py,md' -o context.txt"
    )

    # --- Packing Options Group ---
    pack_group = parser.add_argument_group("Packing Options")
    pack_group.add_argument(
        "start_path",
        type=str,
        nargs="?", # Optional positional argument
        default=None, # Core logic will handle default/config value
        help='Path (file or directory) to start scanning. Defaults to "." or config value.'
    )
    pack_group.add_argument(
        "-o", "--output",
        type=str,
        default=None, # Core logic will calculate default if None
        help="Output file path. Defaults to '[output_dir]/<start_name>_context.txt' based on config."
    )
    pack_group.add_argument(
        "-S", "--stdout",
        action="store_true",
        help='Print the packed content to stdout instead of writing to a file.'
    )
    pack_group.add_argument(
        "-e", "--extensions",
        type=str,
        default=None, # Core logic merges this with config/defaults
        help="Include only these file extensions (e.g., 'py,md'). Supports +/-/~ operators."
    )
    pack_group.add_argument(
        "-I", "--ignore",
        type=str,
        default=None, # Core logic merges this with config/defaults
        help='Patterns (like .gitignore) to ignore (appended to config/defaults).'
    )
    pack_group.add_argument(
        "-N", "--no-gitignore",
        action="store_true",
        help='Do not respect .gitignore files.'
    )
    pack_group.add_argument(
        "-d", "--dry-run",
        action="store_true",
        help='Print the list of files that would be packed, without content.'
    )
    pack_group.add_argument(
        "--no-header",
        action="store_true",
        help="Do not print separator headers ('===== path/to/file.py =====')."
    )
    pack_group.add_argument(
        "--no-tree",
        action="store_true",
        help='Do not print the directory tree at the beginning of the output.'
    )
    pack_group.add_argument(
        "--copy",
        action="store_true",
        help="Copy the output *file* (not content) to the system clipboard after writing."
    )

    # --- Config Initialization Group (mutually exclusive with packing) ---
    config_group = parser.add_argument_group("Config Initialization (run separately)")
    config_group.add_argument(
        "-c", "--config-project",
        action="store_true",
        help=f"Initialize/update the [{CONFIG_SECTION_NAME}] section in {PROJECT_CONFIG_FILENAME}."
    )
    config_group.add_argument(
        "-C", "--config-local",
        action="store_true",
        help=f"Initialize/update the local {CONFIG_FILENAME} file."
    )

    args = parser.parse_args()

    # 2. Setup Logging
    logger = setup_logging(script_name="pcode")
    logger.debug("pcode script started.")

    # 3. Handle Configuration Initialization Request (if flags are present)
    try:
        config_action_taken = handle_config_init_request(
            logger=logger,
            config_project=args.config_project,
            config_local=args.config_local,
            module_dir=MODULE_DIR,
            template_filename=TEMPLATE_FILENAME,
            config_filename=CONFIG_FILENAME,
            project_config_filename=PROJECT_CONFIG_FILENAME,
            config_section_name=CONFIG_SECTION_NAME,
            base_defaults=PCODE_DEFAULTS
        )
        if config_action_taken:
            sys.exit(0) # Exit successfully after config initialization
    except Exception as e:
        logger.error(f"❌ Error during config initialization: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

    # 4. Prepare Basic Path Objects from CLI args
    # Core logic will handle resolving and further validation
    start_path_obj = Path(args.start_path).expanduser() if args.start_path else None
    output_path_obj = Path(args.output).expanduser() if args.output else None

    # 5. Prepare `cli_args` dictionary for Core Logic
    # Pass basic types and minimally processed paths
    cli_args_dict = {
        "start_path": start_path_obj, # Optional[Path]
        "output": output_path_obj,     # Optional[Path]
        "stdout": args.stdout,
        "extensions": args.extensions, # Optional[str]
        "ignore": args.ignore,       # Optional[str]
        "no_gitignore": args.no_gitignore,
        "dry_run": args.dry_run,
        "no_header": args.no_header,
        "no_tree": args.no_tree,
        "copy_to_clipboard": args.copy,
    }

    # 6. Run Core Logic and Executor
    try:
        # Core logic handles config loading, merging, scanning, packing
        result = process_pack_code_logic(
            logger=logger,
            cli_args=cli_args_dict,
        )

        # Executor handles side-effects based on the result
        if result:
            execute_pack_code_action(
                logger=logger,
                result=result
            )

        # Print success message unless in dry-run or stdout mode
        if not (args.dry_run or args.stdout) and result and result.get('status') == 'ok':
            log_success(logger, "Operation completed successfully.")

    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        logger.debug("Traceback:", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation interrupted by user.")
        sys.exit(1)