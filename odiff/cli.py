from argparse import ArgumentParser, ArgumentTypeError
from logging import INFO, Logger, getLevelName
from typing import List

from odiff.logger import get_logger
from odiff.options import CliOptions, OutputType
from odiff.util import get_rsc_fname

log: Logger = get_logger("cli")


def parse(argv: List[str]) -> CliOptions:
    parser = ArgumentParser()

    def valid_log_level(s: str) -> int:
        s_upper = s.upper()
        if s_upper not in [
            "CRITICAL",
            "FATAL",
            "ERROR",
            "WARNING",
            "WARN",
            "INFO",
            "DEBUG",
            "NOTSET",
        ]:
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
        from os import access, R_OK
        from os.path import isfile

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
        "--list-cfg",
        "--cfg",
        "-c",
        required=False,
        type=valid_file,
        default=get_rsc_fname("list-cfg.yaml"),
        help="yaml config file for list indices",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=valid_file,
        help="two files to diff",
    )

    parsed = parser.parse_args(argv)

    match len(parsed.files):
        case 0:
            parsed.files = [get_rsc_fname("j1.json"), get_rsc_fname("j2.json")]
        case 2:
            valid_file(parsed.files[0])
            valid_file(parsed.files[1])
        case _:
            raise ArgumentTypeError(
                "Invalid number of positionals (expected two)"
            )

    return CliOptions(
        output_type=parsed.output_type,
        list_cfg_fname=parsed.list_cfg,
        lfname=parsed.files[0],
        rfname=parsed.files[1],
        log_level=parsed.log_level,
    )
