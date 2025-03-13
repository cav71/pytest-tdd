# TODO:
#   def get_tests_from_doc():
#   def test_from_comments():

from __future__ import annotations

import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


def lookup_candidates(
    source: Path, sources_dir: Path, tests_dir: Path, sibling_testdir: bool = True
) -> list[Path]:
    """
    Returna  list of test candidates for source

    :param source: the module to look tests for
    :param sources_dir: where the sources are rooted
    :param tests_dir:
    """
    candidates = []
    relpath = source.relative_to(sources_dir)
    name = f"test_{source.name}"
    if sibling_testdir:
        candidates.append(source.parent / "tests" / name)
    candidates.append(tests_dir / relpath.parent / name)
    candidates.append(tests_dir / name)
    return candidates


def run(
    workdir: Path,
    module: str,
    candidates: list[Path],
    sources_dir: Path,
) -> tuple[int, dict[str, str | list[str] | None]]:
    env = os.environ.copy()

    env["PYTHONPATH"] = os.pathsep.join(
        [str(sources_dir), *env.get("PYTHONPATH", "").split(os.pathsep)]
    )
    stdout = workdir / "stdout.txt"
    stderr = workdir / "stderr.txt"
    xmlout = workdir / "xmlout.xml"

    cmdline = [
        "pytest",
        "-vv",
        "--junit-xml",
        xmlout,
    ]

    coverage = workdir / "coverage.json"
    cmdline.extend(
        [
            "--cov-reset",
            "--cov",
            module,
            "--cov-report",
            f"json:{coverage}",
        ]
    )

    cmd = [str(c) for c in [*cmdline, *candidates]]

    p = subprocess.Popen(
        cmd,
        cwd=str(workdir),
        stdout=stdout.open("w"),
        stderr=stderr.open("w"),
        env=env,
    )
    p.communicate()

    return p.returncode, {
        "cmd": cmd,
        "stdout": stdout.read_text(),
        "stderr": stderr.read_text(),
        "tests": xmlout.read_text() if xmlout.exists() else None,
        "coverage": coverage.read_text() if coverage.exists() else None,
    }


def process(source: Path, result: dict[str, str | None]) -> str:
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
    return f"{source.name} {tests}, {coverage}"
