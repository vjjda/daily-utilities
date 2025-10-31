# Path: utils/core/parsing.py
import re
from typing import Union, Set, Tuple

__all__ = ["parse_comma_list", "parse_cli_set_operators"]


def parse_comma_list(value: Union[str, None]) -> Set[str]:
    if not value:
        return set()

    return {item.strip() for item in value.split(",") if item.strip()}


def parse_cli_set_operators(cli_string: str) -> Tuple[Set[str], Set[str], Set[str]]:
    overwrite_set: Set[str] = set()
    add_set: Set[str] = set()
    subtract_set: Set[str] = set()

    if not cli_string:
        return overwrite_set, add_set, subtract_set

    matches = re.findall(r"([+~]?)((?:[^~+])+)", cli_string)

    if not matches:

        return overwrite_set, add_set, subtract_set

    first_operator, first_items_str = matches[0]
    first_items_set = parse_comma_list(first_items_str)

    if not first_operator:

        overwrite_set.update(first_items_set)
    elif first_operator == "+":
        add_set.update(first_items_set)
    elif first_operator == "~":
        subtract_set.update(first_items_set)

    for operator, items_str in matches[1:]:
        items_set = parse_comma_list(items_str)
        if operator == "+":
            add_set.update(items_set)
        elif operator == "~":
            subtract_set.update(items_set)

    return overwrite_set, add_set, subtract_set
