import json
import sys
from logging import Logger
from pprint import pformat
from typing import Any, List, Tuple

from tabulate import tabulate

from odiff.cli import parse
from odiff.discrepancy import Discrepancies, Discrepancy
from odiff.logger import get_logger, set_default_log_level
from odiff.odiff import odiff
from odiff.options import CliOptions, OutputType
from odiff.util import ExitCode, read_object_file


log: Logger = get_logger("main")


def main(args: List[str] = []) -> ExitCode:
    """Application entrypoint if you wish to use this as a CLI"""
    args = args or sys.argv[1:]
    opts: CliOptions = parse(args)

    set_default_log_level(opts.log_level)
    log.setLevel(opts.log_level)

    lobj, robj, status = read_object_files(opts)
    if status != ExitCode.CLEAN:
        return status

    discrepancies: Discrepancies = odiff(
        lobj, robj, opts.config, opts.lfname, opts.rfname
    )

    try:
        print(format_discrepancies(opts.output_type, discrepancies, opts.raw))
    except Exception as e:
        print(repr(e))
        return ExitCode.INTERNAL_FAULT

    return ExitCode.CLEAN


def read_object_files(opts: CliOptions) -> Tuple[Any, Any, ExitCode]:
    lobj, err = read_object_file(opts.lfname)
    if err:
        if not isinstance(lobj, str):
            log.error(f"Failed to read object file ({opts.lfname})")
            return None, None, ExitCode.USER_FAULT
        log.warning(f"File not JSON or YAML, read as string ({opts.lfname})")
    robj, err = read_object_file(opts.rfname)
    if err:
        if not isinstance(robj, str):
            log.error(f"Failed to read object file ({opts.rfname})")
            return None, None, ExitCode.USER_FAULT
        log.warning(f"File not JSON or YAML, read as string ({opts.rfname})")
    return lobj, robj, ExitCode.CLEAN


def format_discrepancies(
    output_type: OutputType, discrepancies: Discrepancies, raw: bool
) -> str:
    match output_type:
        case OutputType.OBJECT:
            return pformat(discrepancies)
        case OutputType.JSON:
            return json.dumps([d.__dict__ for d in discrepancies], indent=2)
        case OutputType.SIMPLE:
            return "\n".join([str(d) for d in discrepancies])
        case OutputType.ONE_LINE:
            return "\n".join([d.one_line() for d in discrepancies])
        case OutputType.TABLE:
            return tabulate(
                [d.for_tabulation(raw) for d in discrepancies],
                headers=Discrepancy.tabulation_headers(raw),
                tablefmt="rounded_grid",
            )
        case o:
            raise Exception(f"Output type is not implemented ({o})")


if __name__ == "__main__":
    exit(main())
