import re
from logging import Logger
from typing import Any, Dict, Hashable, List, Optional, Set, Tuple

from odiff.discrepancy import Discrepancies, Discrepancy
from odiff.logger import get_logger
from odiff.options import OdiffConfig
from odiff.util import all_dicts


log: Logger = get_logger("odiff")


def odiff(
    lobj: Any,
    robj: Any,
    config: OdiffConfig,
    lfname: str = "",
    rfname: str = "",
) -> Discrepancies:
    match lobj, robj:
        case list(), list():
            discrepancies = diff_lists(lobj, robj, config)
        case dict(), dict():
            discrepancies = diff_dicts(lobj, robj, config)
        case _:
            discrepancies = diff_values(lobj, robj, config)
    build_unified_diffs(discrepancies, lfname, rfname)
    return discrepancies


def diff_dicts(
    d1: Dict[str, Any],
    d2: Dict[str, Any],
    config: OdiffConfig,
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
        if _path_to_key(subpath) in config.exclusions:
            _log_discrepency(subpath)
            continue
        discrepancies.append(Discrepancy.sub(subpath, d2[k]))
    for k, v in d1.items():
        subpath: str = _append_path_element(path, k, is_from_array)
        if _path_to_key(subpath) in config.exclusions:
            _log_discrepency(subpath)
            continue
        if k not in d2:
            discrepancies.append(Discrepancy.add(subpath, d1[k]))
            continue
        discrepancies.extend(diff_values(v, d2[k], config, subpath))
    return discrepancies


def diff_lists(
    l1: List[Any],
    l2: List[Any],
    config: OdiffConfig,
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
    if list_cfg_key in config.list_indices:
        list_cfg_id = config.list_indices[list_cfg_key]
    d1, l1_non_compliant = _separate_compliant_list(list_cfg_id, l1)
    d2, l2_non_compliant = _separate_compliant_list(list_cfg_id, l2)
    discrepancies: Discrepancies = _simple_diff_lists(
        f"{path}[]", l1_non_compliant, l2_non_compliant
    )
    discrepancies.extend(diff_dicts(d1, d2, config, path, is_from_array=True))
    return discrepancies


# TODO: Just could be much more robust
def diff_values(
    v1: Any, v2: Any, config: OdiffConfig, subpath: str = ""
) -> Discrepancies:
    if _path_to_key(subpath) in config.exclusions:
        _log_discrepency(subpath)
        return []
    match v1:
        case dict():
            if not isinstance(v2, dict):
                return [Discrepancy.mod(subpath, v1, v2)]
            return diff_dicts(v1, v2, config, subpath)
        case list():
            list_cfg_key = _path_to_key(subpath)
            if all_dicts(v1) and list_cfg_key in config.list_indices:
                return diff_lists(v1, v2, config, list_cfg_key, subpath)
            return _simple_diff_lists(f"{subpath}[]", v1, v2)
        case _:
            try:
                v1 = float(v1)
                v2 = float(v2)
            except Exception:
                pass
            if v1 != v2:
                return [Discrepancy.mod(subpath, v1, v2)]
            return []


def build_unified_diffs(
    discrepancies: Discrepancies, lfname: str = "", rfname: str = ""
):
    [d.build_unified_diff(lfname, rfname) for d in discrepancies]


def _log_discrepency(path: str):
    log.warn(f"Discrepancy found for path '.{path}' but was excluded")


def _append_path_element(orig: str, curr: str, is_from_array: bool) -> str:
    path: str = orig
    if len(orig) > 0 and not is_from_array:
        path += "."
    if is_from_array:
        path += f"[{curr}]"
    else:
        path += curr
    return path


def _path_to_key(path: str) -> str:
    return "." + re.sub(r"\[([^\]]*)\]", "[]", path)


def _simple_diff_lists(
    path: str, l1: List[Any], l2: List[Any]
) -> Discrepancies:
    discrepancies: Discrepancies = []
    missing_in_l1: List[Any] = [e for e in l2 if e not in l1]
    missing_in_l2: List[Any] = [e for e in l1 if e not in l2]
    if len(missing_in_l1) > 0 or len(missing_in_l2) > 0:
        discrepancies.append(
            Discrepancy.mod(
                path, [e for e in missing_in_l1], [e for e in missing_in_l2]
            )
        )
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
