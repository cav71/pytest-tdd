from __future__ import annotations
from pathlib import Path


def lookup_candidates(
    source: Path, sources_dir: Path, tests_dir: Path, sibling_testdir: bool = True
) -> list[Path]:
    """returna  list of test candidates for source

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


# TBD:
#   def get_tests_from_doc():
#   def test_from_comments():
