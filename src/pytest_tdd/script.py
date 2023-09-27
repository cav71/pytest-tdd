"""run tests related to a python module
"""
from pathlib import Path
import logging
import contextlib
import argparse

from . import cli


logger = logging.getLogger(__name__)


def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("-c", "--config", help="pyproject.toml file")
    parser.add_argument("-s", "--source", dest="sources", action="append", type=Path)
    parser.add_argument("-t", "--testdir", dest="testdirs", action="append", type=Path)
    parser.add_argument("target", type=Path)


def process_options(options: argparse.Namespace, error: cli.ErrorFn):
    pass


def isin(path: Path, subdir: Path):
    with contextlib.suppress(ValueError):
        return path.absolute().relative_to(subdir.absolute())
    return None


@cli.driver(add_arguments, process_options, __doc__)
def main(options):
    print(options)
    for path in options.sources or []:
        print("S {path=}")


if __name__ == "__main__":
    main()
