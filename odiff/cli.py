import sys
from argparse import ArgumentParser, ArgumentTypeError
from logging import INFO, Logger, getLevelName
from os import access, R_OK
from os.path import isfile
from typing import List

from dacite import DaciteError, from_dict

from odiff.logger import VALID_LOG_LEVELS, get_logger
from odiff.options import CliOptions, OdiffConfig, OutputType
from odiff.util import read_yaml_file

log: Logger = get_logger("cli")


def config_from_fname(fname: str) -> OdiffConfig:
    obj, err = read_yaml_file(fname)
    if err:
        raise ArgumentTypeError(f"Filed to read config file: {fname})")
    try:
        return from_dict(
            OdiffConfig, {k.replace("-", "_"): v for k, v in obj.items()}
        )
    except DaciteError as e:
        raise ArgumentTypeError(e)


def parse(argv: List[str]) -> CliOptions:
    parser = ArgumentParser()

    def valid_log_level(s: str) -> int:
        s_upper = s.upper()
        if s_upper not in VALID_LOG_LEVELS:
            raise ArgumentTypeError(f"Invalid log level ({s})")
        return getLevelName(s_upper)

    parser.add_argument(
        "--log-level",
        required=False,
        type=valid_log_level,
        default=INFO,
        help="log level name",
    )

    def valid_file(fname: str) -> str:
        if isfile(fname) and access(fname, R_OK):
            return fname
        raise ArgumentTypeError(f"File ({fname}) not readable")

    parser.add_argument(
        "--output-type",
        "--output",
        "-o",
        required=False,
        type=OutputType,
        default=OutputType.TABLE,
        help="report output flavour",
    )
    parser.add_argument(
        "--config",
        "-c",
        required=False,
        type=config_from_fname,
        help="yaml config file",
    )

    def contains_colon(s: str) -> str:
        if len(s.split(":")) < 2:
            raise ArgumentTypeError(f"Colon not in value: {s}")
        return s

    parser.add_argument(
        "--list-index",
        "--li",
        required=False,
        action="append",
        type=contains_colon,
        default=[],
        help="list indices not in config",
    )

    parser.add_argument(
        "--raw",
        "-r",
        required=False,
        action="store_true",
        default=False,
        help="display raw objects instead of unified diff",
    )

    parser.add_argument(
        "--exclusion",
        "--exc",
        required=False,
        action="append",
        type=str,
        default=[],
        help="exclusions not in config",
    )

    parser.add_argument(
        "files",
        nargs="*",
        type=valid_file,
        help="two files to diff",
    )

    parsed = parser.parse_args(argv)

    if len(parsed.files) != 2:
        parser.print_usage(file=sys.stderr)
        print("Invalid number of positionals (expected two)", file=sys.stderr)
        exit(1)

    config = parsed.config if parsed.config else OdiffConfig()

    for e in parsed.list_index:
        split = e.split(":", maxsplit=1)
        k, v = split[0].strip(), split[1].strip()
        config.list_indices[k] = v

    for e in parsed.exclusion:
        config.exclusions.append(e)

    return CliOptions(
        output_type=parsed.output_type,
        config=config,
        raw=parsed.raw,
        lfname=parsed.files[0],
        rfname=parsed.files[1],
        log_level=parsed.log_level,
    )
