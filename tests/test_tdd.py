import os
import functools
from pytest_tdd import tdd


def test_lookup(test_tree, tmp_path):
    test_tree(tmp_path)

    sources_dir = tmp_path / "src"
    tests_dir = tmp_path / "tests"

    lookup = functools.partial(
        tdd.lookup_candidates, sources_dir=sources_dir, tests_dir=tests_dir
    )

    candidates = lookup(tmp_path / "src/package1/modA.py")

    found = set(str(p.relative_to(tmp_path)).replace(os.sep, "/") for p in candidates)
    assert found == {
        "src/package1/tests/test_modA.py",
        "tests/package1/test_modA.py",
        "tests/test_modA.py",
    }
