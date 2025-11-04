# Path: modules/bootstrap/bootstrap_internal/builders/builder_utils.py
from typing import Any, Dict, List

__all__ = ["get_cli_args"]


def get_cli_args(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    return config.get("cli", {}).get("args", [])
