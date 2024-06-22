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
TABULATION_VALUE_MAX = 40


def trunc(s: str, n: int = TRUNC_MAX) -> str:
    return (s[:n] + "...") if len(s) > n else s


def get_rsc_fname(fname: str) -> str:
    return f"{MODULE_DIR}/rsc/{fname}"


def read_object_file(fname: str) -> Tuple[List | Dict, Optional[Exception]]:
    data: Any = None
    with open(fname) as f:
        err: Optional[Exception] = None
        try:
            data = yaml.load(f, Loader=yaml.SafeLoader)
            return data, None
        except yaml.YAMLError as e:
            err = e
        try:
            data = json.load(f)
            return data, None
        except json.JSONDecodeError as e:
            err = e
        if err:
            return {}, err
    match data:
        case list() | dict():
            return data, None
        case _:
            return {}, Exception(
                f"Input file not JSON or YAML list or dict: {fname}"
            )


ListCfg = Dict[str, str]


def read_list_cfg(
    fname: Optional[str],
) -> Tuple[ListCfg, Optional[Exception]]:
    if not fname:
        return {}, None
    data: Any = {}
    with open(fname) as f:
        try:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        except yaml.YAMLError as e:
            return {}, e
    if not isinstance(data, dict):
        return {}, Exception(f"List cfg is not dict:\n{data}")
    for k, v in data.items():
        if not isinstance(k, str):
            return {}, Exception(f"Key not string: {k}")
        if not isinstance(v, str):
            return {}, Exception(f"Value not string: {v}")
    return data, None


def all_dicts(lst: List[Any]) -> bool:
    return all(isinstance(e, dict) for e in lst)


def multiline_aware_wrap(
    s: str, indent_wrapped: bool, width: int = TABULATION_VALUE_MAX
) -> str:
    lines = []
    for line in s.split("\n"):
        if len(line) <= width:
            lines.append(line)
            continue
        print(line)
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