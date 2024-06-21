from __future__ import annotations

from enum import StrEnum
from dataclasses import dataclass
import re
from typing import Any, Dict, Hashable, List, Set, Tuple
from textwrap import wrap

from tabulate import tabulate

from odiff.util import (
    get_aux_json,
    get_aux_yaml,
    trunc,
    TRUNC_MAX,
    TABULATION_VALUE_MAX,
)


class Variant(StrEnum):
    ADD = "addition"
    SUB = "subtraction"
    MOD = "modification"


@dataclass
class Discrepancy:
    variant: Variant
    path: str
    lvalue: Any
    rvalue: Any

    def __str__(self) -> str:
        s: str = f"{self.variant} @ {self.path} : "
        if len(str(self.lvalue)) > TRUNC_MAX:
            s += "\n  "
        s += trunc(str(self.lvalue)) + " -> "
        if len(str(self.lvalue)) > TRUNC_MAX:
            s += "\n  "
        s += trunc(str(self.rvalue))
        return s

    def for_tabulation(self) -> List[str | Any]:
        width_path: str = re.sub(r"\[([^\]]{5,})\]", r"[\n  \1\n]", self.path)
        return [
            str(self.variant),
            width_path,
            "\n".join(wrap(str(self.lvalue), width=TABULATION_VALUE_MAX)),
            "\n".join(wrap(str(self.rvalue), width=TABULATION_VALUE_MAX)),
        ]

    @staticmethod
    def tabulation_headers() -> List[str]:
        return ["Variant", "Path", "Lvalue", "Rvalue"]

    @staticmethod
    def add(path: str, lvalue: Any) -> Discrepancy:
        return Discrepancy(Variant.ADD, f".{path}", lvalue, None)

    @staticmethod
    def sub(path: str, rvalue: Any) -> Discrepancy:
        return Discrepancy(Variant.SUB, f".{path}", None, rvalue)

    @staticmethod
    def mod(path: str, lvalue: Any, rvalue: Any) -> Discrepancy:
        return Discrepancy(Variant.MOD, f".{path}", lvalue, rvalue)


def _simple_diff_lists(
    path: str, l1: List[Any], l2: List[Any]
) -> List[Discrepancy]:
    discrepancies: List[Discrepancy] = []
    missing_in_l1: List[Any] = [e for e in l2 if e not in l1]
    if len(missing_in_l1) > 0:
        discrepancies.append(Discrepancy.sub(path, [e for e in missing_in_l1]))
    missing_in_l2: List[Any] = [e for e in l1 if e not in l2]
    if len(missing_in_l2) > 0:
        discrepancies.append(Discrepancy.add(path, [e for e in missing_in_l2]))
    return discrepancies


def _separate_compliant_list(
    list_key: str, list_of_dicts: List[dict]
) -> Tuple[Dict[str, dict], List[dict]]:
    compliant: Dict[str, dict] = {}
    non_compliant: List[dict] = []
    for e in list_of_dicts:
        if list_key in e and isinstance(e[list_key], Hashable):
            compliant[e[list_key]] = e
        else:
            non_compliant.append(e)
    return compliant, non_compliant


def diff_lists(
    l1: List[dict],
    l2: List[dict],
    list_cfg: Dict[str, str],
    list_cfg_key: str,
    path: str = "",
) -> List[Discrepancy]:
    list_cfg_id = list_cfg[list_cfg_key]
    d1, l1_non_compliant = _separate_compliant_list(list_cfg_id, l1)
    d2, l2_non_compliant = _separate_compliant_list(list_cfg_id, l2)
    discrepancies: List[Discrepancy] = _simple_diff_lists(
        f"{path}[]", l1_non_compliant, l2_non_compliant
    )
    discrepancies.extend(dict_diff(d1, d2, list_cfg, path, is_from_array=True))
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


def dict_diff(
    j1: dict,
    j2: dict,
    list_cfg: Dict[str, str],
    path: str = "",
    is_from_array: bool = False,
) -> List[Discrepancy]:
    discrepancies: List[Discrepancy] = []
    missing_in_j1: Set[str] = j2.keys() - j1.keys()
    for k in missing_in_j1:
        subpath: str = _append_path_element(path, k, is_from_array)
        discrepancies.append(Discrepancy.sub(subpath, j2[k]))
    for k, v in j1.items():
        subpath: str = _append_path_element(path, k, is_from_array)
        if k not in j2:
            discrepancies.append(Discrepancy.add(subpath, j1[k]))
            continue
        match v:
            case dict():
                if not isinstance(j2[k], dict):
                    discrepancies.append(Discrepancy.mod(subpath, v, j2[k]))
                else:
                    discrepancies.extend(dict_diff(v, j2[k], list_cfg, subpath))
            case list():
                list_cfg_key = re.sub(r"\[([^\]]*)\]", "[]", subpath)
                if (
                    all(isinstance(e, dict) for e in v)
                    and list_cfg_key in list_cfg
                ):
                    discrepancies.extend(
                        diff_lists(v, j2[k], list_cfg, list_cfg_key, subpath)
                    )
                else:
                    discrepancies.extend(
                        _simple_diff_lists(f"{subpath}[]", v, j2[k])
                    )
            case _:
                if v != j2[k]:
                    discrepancies.append(Discrepancy.mod(subpath, v, j2[k]))
    return discrepancies


def odiff():
    j1: dict = get_aux_json("j1.json")[0]
    j2: dict = get_aux_json("j2.json")[0]
    list_cfg: Dict[str, str] = get_aux_yaml("cfg.yaml")
    discrepancies = dict_diff(j1, j2, list_cfg)
    print(
        tabulate(
            [d.for_tabulation() for d in discrepancies],
            headers=Discrepancy.tabulation_headers(),
            tablefmt="rounded_grid",
        )
    )


if __name__ == "__main__":
    odiff()
