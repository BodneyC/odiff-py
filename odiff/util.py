from io import SEEK_SET
import os
import json
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

import yaml

MODULE_DIR: str = os.path.dirname(os.path.realpath(__file__))


class ExitCode(IntEnum):
    CLEAN = 0
    USER_FAULT = 1
    INTERNAL_FAULT = 2
    FILE_IO = 3
    MODULE = 4


TRUNC_MAX = 100
RAW_OBJECT_COLUMN_MAX_W = 50
PATH_COLUMN_MAX_W = 30


def trunc(s: str, n: int = TRUNC_MAX) -> str:
    return (s[:n] + "...") if len(s) > n else s


def read_yaml_file(fname: str) -> Tuple[Dict, Optional[Exception]]:
    data: Any = None
    with open(fname) as f:
        try:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        except Exception as e:
            return {}, e
    match data:
        case dict():
            return data, None
        case _:
            return {}, Exception(
                f"Input file not JSON or YAML list or dict: {fname}"
            )


def read_object_file(
    fname: str,
) -> Tuple[List | Dict | str, Optional[Exception]]:
    data: Any = None
    with open(fname) as f:
        err: Optional[Exception] = None
        try:
            data = yaml.load(f, Loader=yaml.SafeLoader)
            return data, None
        except yaml.YAMLError as e:
            err = e
        f.seek(SEEK_SET)
        try:
            data = json.load(f)
            return data, None
        except json.JSONDecodeError as e:
            err = e
        f.seek(SEEK_SET)
        if err:
            return f.read(), err
    match data:
        case list() | dict():
            return data, None
        case _:
            return {}, Exception(
                f"Input file not JSON or YAML list or dict: {fname}"
            )


def all_dicts(lst: List[Any]) -> bool:
    return all(isinstance(e, dict) for e in lst)


def multiline_aware_wrap(s: str, indent_wrapped: bool, width: int) -> str:
    lines = []
    for line in s.split("\n"):
        if len(line) <= width:
            lines.append(line)
            continue
        prefix: str = (len(line) - len(line.lstrip())) * " "
        if indent_wrapped:
            prefix += "  "
        first, remainder = line[:width], line[width:]
        lines.append(first)
        lines.extend(
            [
                prefix + remainder[i : i + width]
                for i in range(0, len(remainder), width)
            ]
        )
    return "\n".join(lines)
