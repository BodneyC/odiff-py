from __future__ import annotations

import json
import re
import sys
from enum import StrEnum
from dataclasses import dataclass
from logging import Logger
from pprint import pprint
from typing import (
    Any,
    Dict,
    Hashable,
    List,
    Optional,
    Set,
    Tuple,
)

from tabulate import tabulate

from odiff.cli import parse
from odiff.logger import get_logger, set_default_log_level
from odiff.options import CliOptions, OutputType
from odiff.util import (
    ExitCode,
    ListCfg,
    all_dicts,
    read_list_cfg,
    read_object_file,
    trunc,
    TRUNC_MAX,
    multiline_aware_wrap,
)


class Variant(StrEnum):
    """Types of object variations"""

    ADD = "addition"
    SUB = "subtraction"
    MOD = "modification"


@dataclass
class Discrepancy:
    """Structure for a found discrepancy between object

    :param variant: :class:`odiff.main.Variant`, the type of discrepancy
    :param path: str, the path through the objects being compared (JQ-ish)
    :param lvalue: `typing.Any`, the value if found in the first object
    :param rvalue: `typing.Any`, the value if found in the second object
    """

    variant: Variant
    path: str
    lvalue: Any
    rvalue: Any

    def __str__(self) -> str:
        s: str = f"{self.variant} @ .{self.path} : "
        multiline: bool = (
            len(str(self.lvalue)) > TRUNC_MAX
            or len(str(self.rvalue)) > TRUNC_MAX
        )
        s += "[\n  " if multiline else ""
        s += trunc(str(self.lvalue))
        s += "\n]" if multiline else ""
        s += " -> "
        s += "[\n  " if multiline else ""
        s += trunc(str(self.rvalue))
        s += "\n]" if multiline else ""
        return s

    @staticmethod
    def _format_value(value: Any) -> str:
        match value:
            case list() | dict():
                s: str = json.dumps(value, indent=2)
                return multiline_aware_wrap(s, indent_wrapped=True)
            case _:
                return multiline_aware_wrap(str(value), indent_wrapped=False)

    def for_tabulation(self) -> List[str | Any]:
        """Format the Discrepancy for tabulation"""
        width_path: str = re.sub(r"\[([^\]]{5,})\]", r"[\n  \1\n]", self.path)
        return [
            str(self.variant),
            f".{width_path}",
            self._format_value(self.lvalue),
            self._format_value(self.rvalue),
        ]

    @staticmethod
    def tabulation_headers() -> List[str]:
        """List of headers for use with tabulation"""
        return ["Variant", "Path", "Lvalue", "Rvalue"]

    @staticmethod
    def add(path: str, lvalue: Any) -> Discrepancy:
        """Create an ADD discrepancy with the provided left-value"""
        return Discrepancy(Variant.ADD, path, lvalue, None)

    @staticmethod
    def sub(path: str, rvalue: Any) -> Discrepancy:
        """Create a SUB discrepancy with the provided right-value"""
        return Discrepancy(Variant.SUB, path, None, rvalue)

    @staticmethod
    def mod(path: str, lvalue: Any, rvalue: Any) -> Discrepancy:
        """Create a MOD discrepancy with both right and left values"""
        return Discrepancy(Variant.MOD, path, lvalue, rvalue)


type Discrepancies = List[Discrepancy]


def _simple_diff_lists(
    path: str, l1: List[Any], l2: List[Any]
) -> Discrepancies:
    discrepancies: Discrepancies = []
    missing_in_l1: List[Any] = [e for e in l2 if e not in l1]
    if len(missing_in_l1) > 0:
        discrepancies.append(Discrepancy.sub(path, [e for e in missing_in_l1]))
    missing_in_l2: List[Any] = [e for e in l1 if e not in l2]
    if len(missing_in_l2) > 0:
        discrepancies.append(Discrepancy.add(path, [e for e in missing_in_l2]))
    return discrepancies


def _separate_compliant_list(
    list_key: Optional[str], list_of_dicts: List[Any]
) -> Tuple[Dict[str, dict], List[Any]]:
    if not list_key:
        return {}, list_of_dicts
    compliant: Dict[str, dict] = {}
    non_compliant: List[Any] = []
    for e in list_of_dicts:
        if (
            list_key in e
            and isinstance(e, dict)
            and isinstance(e[list_key], Hashable)
        ):
            compliant[e[list_key]] = e
        else:
            non_compliant.append(e)
    return compliant, non_compliant


def diff_lists(
    l1: List[Any],
    l2: List[Any],
    list_cfg: ListCfg,
    list_cfg_key: str = ".",
    path: str = "",
) -> Discrepancies:
    """Find discrepancies between two lists

    The naive list comparison, element by element, has an obvious flaw: the
     comparison of removed elements may offset two otherwise identical lists.

    For primitives, you can compare other elements in a Levenstein-ish way, but
     not really for a list of objects; you could of course, but what if two
     objects that refer to the same "thing" differ slightly and it's that
     difference we care about?

    For that, we need to compare by some unique key, say a '.id' or similar,
     that's what we're doing with `list_cfg`, a map of paths through the
     object(s) to uniqlistue keys

    :param l1: List[Any], the "left" list against which to compare
    :param l2: List[Any], the "right" list against which to compare
    :param list_cfg: List configuration for index-based comparisons
    :param list_cfg_key: Key in `list_cfg` to index
    :param path: Path through any calling objects

    :return: List of discrepancies
    :rtype: Discrepancies
    """
    list_cfg_id: Optional[str] = None
    if list_cfg_key in list_cfg:
        list_cfg_id = list_cfg[list_cfg_key]
    d1, l1_non_compliant = _separate_compliant_list(list_cfg_id, l1)
    d2, l2_non_compliant = _separate_compliant_list(list_cfg_id, l2)
    discrepancies: Discrepancies = _simple_diff_lists(
        f"{path}[]", l1_non_compliant, l2_non_compliant
    )
    discrepancies.extend(diff_dicts(d1, d2, list_cfg, path, is_from_array=True))
    return discrepancies


def _append_path_element(orig: str, curr: str, is_from_array: bool) -> str:
    path: str = orig
    if len(orig) > 0 and not is_from_array:
        path += "."
    if is_from_array:
        path += f"[{curr}]"
    else:
        path += curr
    return path


def _compare_values(
    v1: Any, v2: Any, subpath: str, list_cfg: ListCfg
) -> Discrepancies:
    match v1:
        case dict():
            if not isinstance(v2, dict):
                return [Discrepancy.mod(subpath, v1, v2)]
            return diff_dicts(v1, v2, list_cfg, subpath)
        case list():
            list_cfg_key = "." + re.sub(r"\[([^\]]*)\]", "[]", subpath)
            if all_dicts(v1) and list_cfg_key in list_cfg:
                return diff_lists(v1, v2, list_cfg, list_cfg_key, subpath)
            return _simple_diff_lists(f"{subpath}[]", v1, v2)
        case _:
            if v1 != v2:
                return [Discrepancy.mod(subpath, v1, v2)]
            return []


def diff_dicts(
    d1: Dict[str, Any],
    d2: Dict[str, Any],
    list_cfg: ListCfg,
    path: str = "",
    is_from_array: bool = False,
) -> Discrepancies:
    """Find discrepancies between two dictionaries

    :param r1: Dict[str, Any], the "left" list against which to compare
    :param r2: Dict[str, Any], the "right" list against which to compare
    :param list_cfg: List configuration for index-based comparisons
    :param path: Path through any calling objects
    :param is_from_array: Whether these are dictionaries being compared with
        lists already being compared

    :return: List of discrepancies
    :rtype: Discrepancies
    """
    discrepancies: Discrepancies = []
    missing_in_j1: Set[str] = d2.keys() - d1.keys()
    for k in missing_in_j1:
        subpath: str = _append_path_element(path, k, is_from_array)
        discrepancies.append(Discrepancy.sub(subpath, d2[k]))
    for k, v in d1.items():
        subpath: str = _append_path_element(path, k, is_from_array)
        if k not in d2:
            discrepancies.append(Discrepancy.add(subpath, d1[k]))
            continue
        discrepancies.extend(_compare_values(v, d2[k], subpath, list_cfg))
    return discrepancies


def odiff(args: List[str] = []) -> ExitCode:
    """Application entrypoint if you wish to use this as a CLI"""
    args = args or sys.argv[1:]
    opts: CliOptions = parse(args)

    set_default_log_level(opts.log_level)

    log: Logger = get_logger("odiff")

    lobj, err = read_object_file(opts.lfname)
    if err:
        log.error(f"Failed to read object file ({opts.lfname})")
        return ExitCode.USER_FAULT
    robj, err = read_object_file(opts.rfname)
    if err:
        log.error(f"Failed to read object file ({opts.lfname})")
        return ExitCode.USER_FAULT

    list_cfg, err = read_list_cfg(opts.list_cfg_fname)
    if err:
        log.error(f"Failed to read list config file ({opts.list_cfg_fname})")
        return ExitCode.USER_FAULT

    discrepancies: Discrepancies = []
    match lobj, robj:
        case list(), list():
            discrepancies = diff_lists(lobj, robj, list_cfg)
        case dict(), dict():
            discrepancies = diff_dicts(lobj, robj, list_cfg)
        case _:
            log.error(
                f"Files ({opts.lfname}, {opts.rfname}) do not have matching outer types"
            )
            return ExitCode.USER_FAULT

    match opts.output_type:
        case OutputType.STRING:
            pprint(discrepancies)
        case OutputType.JSON:
            print(json.dumps([d.__dict__ for d in discrepancies], indent=2))
        case OutputType.SIMPLE:
            [print(str(d)) for d in discrepancies]
        case OutputType.TABLE:
            print(
                tabulate(
                    [d.for_tabulation() for d in discrepancies],
                    headers=Discrepancy.tabulation_headers(),
                    tablefmt="rounded_grid",
                )
            )
        case o:
            log.error(f"Unknown output type ({o})")
            return ExitCode.USER_FAULT

    return ExitCode.CLEAN


if __name__ == "__main__":
    exit(odiff())
