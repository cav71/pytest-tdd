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
import enum
import json
import xml.etree.ElementTree as ET

from pathlib import Path
from pytest_tdd import misc, cli, tdd

log = logging.getLogger(__name__)


class Flags(enum.Flag):
    COUNT = enum.auto()
    COVERAGE = enum.auto()


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


def run(
    module: str, candidates: list[Path], config: Flags
) -> tuple[int, dict[str, str | None]]:
    with misc.mkdir() as outdir:
        stdout = outdir / "stdout.txt"
        stderr = outdir / "stderr.txt"
        xmlout = outdir / "xmlout.xml"
        coverage: Path | None = None
        cmd = [
            "pytest",
            "-vvs",
            "--junit-xml",
            xmlout,
        ]

        if config & Flags.COVERAGE:
            coverage = outdir / "coverage.json"
            cmd = [
                *cmd,
                "--cov-reset",
                "--cov",
                module,
                "--cov-report",
                f"json:{coverage}",
            ]
        cmd = [*cmd, *candidates]

        p = subprocess.Popen(
            [str(c) for c in cmd], stdout=stdout.open("w"), stderr=stderr.open("w")
        )
        p.communicate()
        return p.returncode, {
            "stdout": stdout.read_text(),
            "stderr": stderr.read_text(),
            "tests": xmlout.read_text(),
            "coverage": coverage.read_text() if coverage else None,
        }


def compute(source: Path, result: dict[str, str | None]) -> str:
    coverage = "coverage n/a"
    if result["coverage"]:
        cov = json.loads(result["coverage"])
        lines, total = cov["totals"]["covered_lines"], cov["totals"]["num_statements"]
        missing = cov["totals"]["missing_lines"]
        percent = round(
            100.0 * cov["totals"]["covered_lines"] / cov["totals"]["num_statements"], 2
        )
        coverage = (
            f"covered {lines} lines out of {total} ({percent}%, {missing=} lines)"
        )

    tests = "tests n/a"
    if result["tests"]:
        totals = {"errors": 0, "failures": 0, "skipped": 0, "tests": 0}
        testsuites = ET.fromstring(result["tests"])
        for testsuite in testsuites:
            totals["errors"] += int(testsuite.attrib.get("errors", 0))
            totals["failures"] += int(testsuite.attrib.get("failures", 0))
            totals["skipped"] += int(testsuite.attrib.get("skipped", 0))
            totals["tests"] += int(testsuite.attrib.get("tests", 0))
        tests = (
            f"run {totals['tests']} tests with {totals['failures']} "
            f"failures and {totals['errors']} errors"
        )
    return f"{source.name} {tests}, {coverage}%"


@cli.driver(add_arguments, process_options, doc=__doc__)
def main(source: Path, sources_dir: Path, tests_dir: Path) -> int:
    module = (
        str(source.relative_to(sources_dir).with_suffix(""))
        .replace("/", ".")
        .replace("\\", ".")
    )
    log.debug("sources from: %s", sources_dir)
    log.debug("tests from: %s", tests_dir)
    log.info("source file: %s (mod %s)", source, module)

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

    returncode, result = run(module, candidates, Flags.COVERAGE)
    # print("== STDERR ==")
    # print(misc.indent(result["stderr"]))
    # print("== STDOUT ==")
    # print(misc.indent(result["stdout"]))
    # print("== RESULTS ==")
    # print(misc.indent(result["tests"]))

    # if result["coverage"]:
    #     print("== COVERAGE ==")
    #     print(result["coverage"])
    # print(str(result["returncode"]))
    # print("== WOW ==")
    print(compute(source, result))
    return returncode


if __name__ == "__main__":
    sys.exit(main())
