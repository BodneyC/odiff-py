import json
import sys
from logging import Logger
from pprint import pprint
from typing import Any, List, Tuple

from tabulate import tabulate

from odiff.cli import parse
from odiff.discrepancy import Discrepancies, Discrepancy
from odiff.logger import get_logger, set_default_log_level
from odiff.odiff import diff_values, diff_dicts, diff_lists
from odiff.options import CliOptions, Config, OutputType
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

    discrepancies: Discrepancies = build_discrepancies(lobj, robj, opts.config)

    return print_discrepancies(opts.output_type, discrepancies)


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


def build_discrepancies(lobj: Any, robj: Any, config: Config) -> Discrepancies:
    match lobj, robj:
        case list(), list():
            return diff_lists(lobj, robj, config)
        case dict(), dict():
            return diff_dicts(lobj, robj, config)
        case _:
            return diff_values(lobj, robj, config)


def print_discrepancies(
    output_type: OutputType, discrepancies: Discrepancies
) -> ExitCode:
    match output_type:
        case OutputType.OBJECT:
            pprint(discrepancies)
        case OutputType.JSON:
            print(json.dumps([d.__dict__ for d in discrepancies], indent=2))
        case OutputType.SIMPLE:
            [print(str(d)) for d in discrepancies]
        case OutputType.ONE_LINE:
            [print(d.one_line()) for d in discrepancies]
        case OutputType.TABLE:
            print(
                tabulate(
                    [d.for_tabulation() for d in discrepancies],
                    headers=Discrepancy.tabulation_headers(),
                    tablefmt="rounded_grid",
                )
            )
        case o:
            log.error(f"Output type is not implemented ({o})")
            return ExitCode.USER_FAULT
    return ExitCode.CLEAN


if __name__ == "__main__":
    exit(main())
