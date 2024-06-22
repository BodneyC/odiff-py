from dataclasses import dataclass
from enum import StrEnum
from typing import Optional


class OutputType(StrEnum):
    JSON = "json"
    TABLE = "table"
    STRING = "string"
    SIMPLE = "simple"


@dataclass
class CliOptions:
    output_type: OutputType
    list_cfg_fname: Optional[str]
    lfname: str
    rfname: str
    log_level: int
