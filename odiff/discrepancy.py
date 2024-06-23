from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
import re
from typing import Any, List

from odiff.util import TRUNC_MAX, multiline_aware_wrap, trunc


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
        return " | ".join(
            [
                self.variant,
                self.path,
                trunc(str(self.lvalue)),
                trunc(str(self.rvalue)),
            ]
        )

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
