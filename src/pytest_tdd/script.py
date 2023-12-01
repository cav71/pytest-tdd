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
import os
import sys
import logging
import subprocess
import json
import dataclasses as dc
import xml.etree.ElementTree as ET

from pathlib import Path
import click


from pytest_tdd import misc, tdd

log = logging.getLogger(__name__)


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
        "-vvs",
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
    return f"{source.name} {tests}, {coverage}"


@click.command()
@click.argument("source", type=click.Path(path_type=Path))  # type: ignore
@click.option(
    "-t",
    "--tests-dir",
    default="tests",
    type=click.Path(exists=True, file_okay=False, path_type=Path),  # type: ignore
)
@click.option(
    "-s",
    "--sources-dir",
    default="src",
    type=click.Path(exists=True, file_okay=False, path_type=Path),  # type: ignore
)
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet", count=True)
@click.option("-k", "--keep", is_flag=True, help="keep results on error")
@click.pass_context
def main(ctx, source, sources_dir, tests_dir, verbose, quiet, keep):
    level = min(max(verbose - quiet, -1), 1)
    logging.basicConfig(
        level=logging.DEBUG
        if level > 0
        else logging.INFO
        if level == 0
        else logging.WARNING
    )

    tests_dir = tests_dir.absolute()
    sources_dir = sources_dir.absolute()
    source = source.absolute()

    @dc.dataclass
    class C:
        tempdir: Path = Path()  # type: ignore

    ctx.ensure_object(C)
    ctx.obj.tempdir = ctx.with_resource(misc.mkdir(keep=keep))

    module = (
        str(source.relative_to(sources_dir).with_suffix(""))
        .replace("/", ".")
        .replace("\\", ".")
    )
    log.debug("module: %s", module)
    log.debug("sources from: %s", sources_dir)
    log.debug("tests from: %s", tests_dir)
    log.debug("source file: %s (mod %s)", source, module)

    candidates = tdd.lookup_candidates(source, sources_dir, tests_dir)

    # filter out candidates
    to_be_run = []
    for candidate in candidates:
        found = "found" if candidate.exists() else "not found"
        if candidate.exists():
            to_be_run.append(candidate)
        log.debug("file %s %s", found, candidate)
    candidates = to_be_run

    # manages a failure
    retcode, result = run(ctx.obj.tempdir, module, candidates, sources_dir)
    if retcode:
        msgs = []
        msgs.append("cmd:")
        msgs.append(f"|  {' '.join(result['cmd'])}")
        log.warning("failed to run tests")
        log.warning("\n".join(msgs))
        if result["stderr"].strip():
            log.warning("stderr:\n%s", misc.indent(result["stderr"], "|  "))
        if result["stdout"].strip():
            log.warning("stdout:\n%s", misc.indent(result["stdout"], "|  "))

    if keep:
        log.warning("preserving dir %s", ctx.obj.tempdir)

    print(compute(source, result))
    return retcode


if __name__ == "__main__":
    sys.exit(main() or 0)
