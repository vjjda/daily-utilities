# Path: modules/clip_diag/clip_diag_executor.py
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.core import run_command

from .clip_diag_config import APP_CONFIG, DOT_PATH, MMC_PATH

__all__ = ["execute_diagram_generation"]


def _get_app_to_open(result_type: str) -> str:
    if result_type == "dot":
        return APP_CONFIG["dot_app"]
    elif result_type == "mmd":
        return APP_CONFIG["mermaid_app"]
    elif result_type == "svg":
        return APP_CONFIG["svg_viewer_app"]
    elif result_type == "png":
        return APP_CONFIG["png_viewer_app"]
    return "Preview"


def execute_diagram_generation(
    logger: logging.Logger, result: Dict[str, Any], output_format: Optional[str]
) -> None:

    diagram_type: str = result["diagram_type"]
    source_path_abs: Path = result["source_path"]
    file_prefix: str = result["file_prefix"]
    hashval: str = result["hash"]
    source_dir: Path = source_path_abs.parent
    source_content: str = result["content"]

    try:
        if not source_path_abs.exists():
            with open(source_path_abs, "w", encoding="utf-8") as f:
                f.write(source_content)
            logger.info(f"✍️  Saved new source file: {source_path_abs.name}")
        else:
            logger.info(f"🔄 Source file already exists: {source_path_abs.name}")
    except IOError as e:
        logger.error(f"❌ Failed to write source file {source_path_abs.name}: {e}")
        return

    if output_format:
        output_ext = f".{output_format}"
        output_filename = f"{file_prefix}-{hashval}{output_ext}"
        output_path_abs = source_dir / output_filename
        app_to_open_output = _get_app_to_open(output_format)

        if output_path_abs.exists():
            logger.info(f"🖼️  Image file already exists: {output_filename}")
        else:

            logger.info(f"⏳ Converting to {output_format.upper()}...")

            command: List[str] = []
            if diagram_type == "graphviz":
                command = [
                    DOT_PATH,
                    f"-T{output_format}",
                    "-Gbgcolor=white",
                    str(source_path_abs),
                    "-o",
                    str(output_path_abs),
                ]
            else:
                command = [
                    MMC_PATH,
                    "-i",
                    str(source_path_abs),
                    "-o",
                    str(output_path_abs),
                ]

            try:
                success, error_msg = run_command(
                    command,
                    logger,
                    description=f"Convert {diagram_type} to {output_format.upper()}",
                )

                if not success:
                    logger.error(
                        "❌ Error converting diagram. Please check the source code syntax."
                    )
                    logger.debug(f"Conversion command failed: {error_msg}")

                    if diagram_type == "mermaid" and MMC_PATH not in error_msg:
                        logger.error(
                            "   (Mermaid error? Check syntax or try online editor)"
                        )
                    elif diagram_type == "graphviz" and DOT_PATH not in error_msg:
                        logger.error(
                            "   (Graphviz error? Check syntax with 'dot -v ...')"
                        )
                    return

                logger.info(f"✅ Image file created: {output_filename}")

            except Exception as e:
                logger.error(f"❌ An unexpected error occurred during conversion: {e}")
                return

        logger.info(f"👀 Opening image file with {app_to_open_output}...")
        open_command = ["open", "-a", app_to_open_output, str(output_path_abs)]
        run_command(open_command, logger, description=f"Opening {output_filename}")

    else:
        source_ext = source_path_abs.suffix.strip(".")
        app_to_open_source = _get_app_to_open(source_ext)

        logger.info(f"👩‍💻 Opening source file with {app_to_open_source}...")
        open_command = ["open", "-a", app_to_open_source, str(source_path_abs)]
        run_command(open_command, logger, description=f"Opening {source_path_abs.name}")
