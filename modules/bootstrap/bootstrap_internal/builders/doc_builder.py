# Path: modules/bootstrap/bootstrap_internal/builders/doc_builder.py
from typing import Dict, Any

from ..bootstrap_loader import load_template

__all__ = ["generate_doc_file"]


def generate_doc_file(config: Dict[str, Any]) -> str:
    template = load_template("doc_file.md.template")

    return template.format(
        tool_name=config["meta"]["tool_name"],
        short_description=config.get("docs", {}).get(
            "short_description", f'Tài liệu cho {config["meta"]["tool_name"]}.'
        ),
    )
