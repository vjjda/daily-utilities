# Path: modules/clip_diag/clip_diag_core.py

import hashlib
import re
import pyperclip
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from .clip_diag_config import GRAPHVIZ_PREFIX, MERMAID_PREFIX, DEFAULT_OUTPUT_DIR

__all__ = ["process_clipboard_content"]


DiagramResult = Dict[str, Any]


def _detect_diagram_type(content: str) -> Optional[str]:
    stripped_content = content.strip()
    lower_content = stripped_content.lower()

    unambiguous_mermaid = [
        "sequencediagram",
        "gantt",
        "classdiagram",
        "statediagram",
        "pie",
        "erdiagram",
        "flowchart",
    ]
    if any(lower_content.startswith(kw) for kw in unambiguous_mermaid):
        return "mermaid"

    if lower_content.startswith("graph "):
        first_line = lower_content.split("\n", 1)[0].strip()
        parts = first_line.split()
        if len(parts) > 1 and parts[1] in ["td", "lr", "bt", "rl"]:
            return "mermaid"

    graphviz_pattern = re.compile(
        r'^\s*(strict\s+)?(graph|digraph)(\s+([a-zA-Z0-9_]+|"[^"]*"))?\s*\{',
        re.IGNORECASE,
    )
    if graphviz_pattern.match(stripped_content):
        return "graphviz"

    return None


def _remove_comments(content: str, diagram_type: str) -> str:
    cleaned_content = content
    if diagram_type == "graphviz":

        pattern = re.compile(
            r'("(\\"|[^"])*")|(\'(\\\'|[^\'])*\')|(/\*[\s\S]*?\*/)|(#.*|//.*)',
            re.MULTILINE,
        )

        def replacer(match):

            if match.group(1) is not None or match.group(3) is not None:
                return match.group(0)

            return ""

        cleaned_content = pattern.sub(replacer, content)

    elif diagram_type == "mermaid":

        cleaned_content = re.sub(r"%%.*", "", content)

    cleaned_lines = [line for line in cleaned_content.splitlines() if line.strip()]
    return "\n".join(cleaned_lines)


def _filter_emoji(content: str, logger: logging.Logger) -> str:
    logger.info("🔍 Filtering emoji...")

    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f700-\U0001f77f"
        "\U0001f780-\U0001f7ff"
        "\U0001f800-\U0001f8ff"
        "\U0001f900-\U0001f9ff"
        "\U0001fa00-\U0001fa6f"
        "\U0001fa70-\U0001faff"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", content)


def _trim_leading_comments_and_whitespace(content: str) -> str:
    lines = content.splitlines()
    first_code_line_index = -1

    for i, line in enumerate(lines):
        stripped_line = line.strip()

        if not stripped_line:
            continue

        if stripped_line.startswith(("%%", "/*", "//", "#")):
            continue

        first_code_line_index = i
        break

    if first_code_line_index == -1:

        return ""

    return "\n".join(lines[first_code_line_index:])


def process_clipboard_content(
    logger: logging.Logger, filter_emoji: bool
) -> Optional[DiagramResult]:

    try:
        clipboard_content = pyperclip.paste()
        if not clipboard_content:
            logger.info("Clipboard is empty.")
            return None
    except Exception as e:
        logger.error(f"❌ Error reading clipboard: {e}")
        return None

    processed_content = clipboard_content.replace("\xa0", " ")

    if filter_emoji:
        processed_content = _filter_emoji(processed_content, logger)

    logger.info("🧹 Trimming leading comments/whitespace...")
    processed_content = _trim_leading_comments_and_whitespace(processed_content)

    if not processed_content.strip():
        logger.info("Content is empty after filtering and trimming.")
        return None

    diagram_type = _detect_diagram_type(processed_content)
    if not diagram_type:
        logger.error("❌ Could not find valid Graphviz or Mermaid code in clipboard.")
        return None

    logger.info(f"✨ Detected diagram type: {diagram_type.capitalize()}")

    logger.info("🧹 Filtering comments...")
    processed_content = _remove_comments(processed_content, diagram_type)

    if not processed_content.strip():
        logger.warning("Content is empty after comment filtering.")
        return None

    hashval = hashlib.sha1(processed_content.encode("utf-8")).hexdigest()[:12]

    if diagram_type == "graphviz":
        file_prefix = GRAPHVIZ_PREFIX
        source_ext = ".dot"
    else:
        file_prefix = MERMAID_PREFIX
        source_ext = ".mmd"

    source_filename = f"{file_prefix}-{hashval}{source_ext}"
    source_path = DEFAULT_OUTPUT_DIR / source_filename

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    return {
        "diagram_type": diagram_type,
        "content": processed_content,
        "source_path": source_path,
        "hash": hashval,
        "file_prefix": file_prefix,
    }