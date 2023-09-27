"""given a python module execute related tests.

Example:
    $> pytest-tdd \\
         --src src --tests tests \\
         src/mylibrary/mysubdir/hello.py
    or (the default)
    $> pytest-tdd src/mylibrary/mysubdir/hello.py

    This will look up (and run if found) the following tests:
    - tests/mylibrary/subdir/test_hello.py
    - tests/test_hello.py
"""
import argparse
import logging
from pathlib import Path
from pytest_tdd import misc, cli


log = logging.getLogger(__name__)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("source", type=Path, help="source to run tests for")
    parser.add_argument(
        "-t",
        "--test-dirs",
        dest="test_dirs",
        default=Path.cwd() / "tests",
        type=Path,
        help="root of tests",
    )
    parser.add_argument(
        "-s",
        "--source-dirs",
        dest="source_dirs",
        default=Path.cwd() / "tests",
        type=Path,
        help="root of tests",
    )


def process_options(options: argparse.Namespace, error: cli.ErrorFn):
    options.source_dirs = misc.list_of_paths(options.source_dirs)
    options.test_dirs = misc.list_of_paths(options.test_dirs)


def lookup_candidates(source: Path, test_dirs: list[Path]):
    raise RuntimeError("not-implemented")
    # candidates = [test_dirs / f"test_{source.name}"]
    # found = [c for c in candidates if c.exists()]
    # return found[0]


@cli.driver(add_arguments, process_options, doc=__doc__)
def main(source: Path, source_dirs: Path | list[Path], test_dirs: Path | list[Path]):
    log.info("source file: %s", source)
    log.debug("sources from: %s", source_dirs)
    log.debug("tests from: %s", test_dirs)
    return
    # tfile = lookup_candidates(source, test_dir)
    # log.info("found test in: %s", tfile)

    # from pytest import main

    # main(["-vvs", tfile])


if __name__ == "__main__":
    main()
    # group()
