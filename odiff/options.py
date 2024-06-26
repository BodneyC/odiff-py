from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, List


@dataclass
class OdiffConfig:
    list_indices: Dict[str, str] = field(default_factory=dict)
    exclusions: List[str] = field(default_factory=list)


class OutputType(StrEnum):
    JSON = "json"
    TABLE = "table"
    OBJECT = "object"
    SIMPLE = "simple"
    ONE_LINE = "one-line"


@dataclass
class CliOptions:
    output_type: OutputType
    lfname: str
    rfname: str
    log_level: int
    raw: bool
    config: OdiffConfig = field(default_factory=OdiffConfig)
