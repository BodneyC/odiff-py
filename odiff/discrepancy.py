from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from enum import StrEnum
import json
import re
from typing import Any, List

from odiff.util import (
    RAW_OBJECT_COLUMN_MAX_W,
    PATH_COLUMN_MAX_W,
    TRUNC_MAX,
    multiline_aware_wrap,
    trunc,
)


class Variant(StrEnum):
    """Types of object variations"""

    ADD = "addition"
    SUB = "subtraction"
    MOD = "modification"


@dataclass()
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
    unified_diff: str = ""

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

    def one_line(self) -> str:
        return "|".join(
            [self.variant, self.path, str(self.lvalue), str(self.rvalue)]
        )

    @staticmethod
    def _format_value(value: Any) -> str:
        return multiline_aware_wrap(
            json.dumps(value, indent=2),
            indent_wrapped=True,
            width=RAW_OBJECT_COLUMN_MAX_W,
        )

    def for_tabulation(self, raw: bool) -> List[str | Any]:
        """Format the Discrepancy for tabulation"""
        width_path: str = re.sub(r"\[([^\]]{5,})\]", r"[\n  \1\n]", self.path)
        table: List[str] = [
            str(self.variant),
            multiline_aware_wrap(
                f".{width_path}", indent_wrapped=True, width=PATH_COLUMN_MAX_W
            ),
        ]
        if raw:
            table.extend(
                [
                    self._format_value(self.lvalue),
                    self._format_value(self.rvalue),
                ]
            )
        else:
            table.append(
                multiline_aware_wrap(
                    self.unified_diff,
                    indent_wrapped=True,
                    width=RAW_OBJECT_COLUMN_MAX_W * 2,
                )
            )
        return table

    def build_unified_diff(self, lfname: str = "", rfname: str = ""):
        larr: List[str] = json.dumps(self.lvalue, indent=2).splitlines(True)
        rarr: List[str] = json.dumps(self.rvalue, indent=2).splitlines(True)
        self.unified_diff = "".join(
            unified_diff(larr, rarr, fromfile=lfname, tofile=rfname, n=10)
        )

    @staticmethod
    def tabulation_headers(raw: bool) -> List[str]:
        """List of headers for use with tabulation"""
        if raw:
            return ["Variant", "Path", "Lvalue", "Rvalue"]
        return ["Variant", "Path", "Unified Diff"]

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
