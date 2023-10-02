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
from __future__ import annotations
import sys
import argparse
import logging
import subprocess
from pathlib import Path
from pytest_tdd import misc, cli, tdd

log = logging.getLogger(__name__)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("source", type=Path, help="source to run tests for")

    parser.add_argument(
        "-t",
        "--tests-dir",
        default="tests",
        type=Path,
        help="root of tests",
    )
    parser.add_argument(
        "-s",
        "--sources-dir",
        default="src",
        type=Path,
        help="root of sources",
    )


def process_options(options: argparse.Namespace, error: cli.ErrorFn):
    options.source = options.source.absolute()
    options.sources_dir = (Path.cwd() / options.sources_dir).absolute()
    options.tests_dir = (Path.cwd() / options.tests_dir).absolute()


def run(candidates: list[Path]):
    with misc.mkdir() as outdir:
        cmd = ["pytest", "-vvs", *candidates]
        stdout = outdir / "stdout.txt"
        stderr = outdir / "stderr.txt"
        p = subprocess.Popen(
            [str(c) for c in cmd], stdout=stdout.open("w"), stderr=stderr.open("w")
        )
        p.communicate()
        print("== STDERR ==")
        print(misc.indent(stderr.read_text()))
        print("== STDOUT ==")
        print(misc.indent(stdout.read_text()))
        print("== RETCOD ==")
        print(str(p.returncode))
        return p.returncode


@cli.driver(add_arguments, process_options, doc=__doc__)
def main(source: Path, sources_dir: Path, tests_dir: Path):
    log.info("source file: %s", source)
    log.debug("sources from: %s", sources_dir)
    log.debug("tests from: %s", tests_dir)

    candidates = tdd.lookup_candidates(source, sources_dir, tests_dir)
    # filter out candidates
    to_be_run = []
    for candidate in candidates:
        if not candidate.exists():
            log.debug("skipping missing candidate %s", candidate)
        else:
            log.debug("adding candidate %s", candidate)
            to_be_run.append(candidate)
    candidates = to_be_run
    return run(candidates)


if __name__ == "__main__":
    sys.exit(main())
