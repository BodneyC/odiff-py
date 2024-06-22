from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, List


@dataclass
class Config:
    list_indices: Dict[str, str] = field(default_factory=dict)
    exclusions: List[str] = field(default_factory=list)


class OutputType(StrEnum):
    JSON = "json"
    TABLE = "table"
    STRING = "string"
    SIMPLE = "simple"
    ONE_LINE = "one-line"


@dataclass
class CliOptions:
    output_type: OutputType
    lfname: str
    rfname: str
    log_level: int
    config: Config = field(default_factory=Config)
