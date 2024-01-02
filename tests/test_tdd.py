import os
import functools
import json
from pathlib import Path

from pytest_tdd import tdd
import xml.etree.ElementTree as ET


def test_lookup(mktree):
    rootdir = mktree("""
├── package2/
│   ├── __init__.py
│   ├── modF.py
│   ├── subpackageC/
│   │   └── modG.py
│   └── subpackageD/
│       ├── modH.py
│       └── tests/
│           └── test_modD.py
├── src/
│   └── package1/
│       ├── __init__.py
│       ├── modA.py
│       ├── modB.py
│       ├── subpackageA/
│       │   ├── __init__.py
│       │   └── modC.py
│       └── subpackageB/
│           ├── __init__.py
│           ├── modD.py
│           ├── modE.py
│           └── tests/
│               └── test_modD.py
└── tests/
    ├── package1/
    │   ├── subpackageB/
    │   │   └── test_modC.py
    │   └── test_modA.py
    ├── subpackageC/
    │   └── test_modG.py
    ├── test_modD.py
    └── test_modG.py
""")

    sources_dir = rootdir / "src"
    tests_dir = rootdir / "tests"

    lookup = functools.partial(
        tdd.lookup_candidates, sources_dir=sources_dir, tests_dir=tests_dir
    )

    candidates = lookup(rootdir / "src/package1/modA.py")

    found = set(str(p.relative_to(rootdir)).replace(os.sep, "/") for p in candidates)
    assert found == {
        "src/package1/tests/test_modA.py",
        "tests/package1/test_modA.py",
        "tests/test_modA.py",
    }


def test_run_simple(mktree):
    workdir = mktree("""
├── src/
│   └── package/
│       ├── __init__.py
│       └── subpackage/
│           ├── __init__.py
│           └── mod.py
└── tests/
    ├── package/
    │   ├── subpackage/
    │   │   └── test_mod.py
    │   └── test_mod.py
    ├── subpackage/
    │   └── test_mod.py
    └── test_mod.py
""")

    src = workdir / "src" / "package" / "subpackage" / "mod.py"
    src.write_text("""
def func1(val):
    return val*2
    
def func2(val):
    return val*2
""")

    candidates = [
        workdir / "tests" / "package" / "subpackage" / "test_mode.py",
    ]

    candidates[0].write_text("""
import pytest
from package.subpackage import mod

@pytest.mark.parametrize("val,expected", [ 
    (1, 2), 
    (2, 4),
    (3, 99),
    (4, 8),
])
def test_func1(val, expected):
    assert mod.func1(val) == expected
""")
    ret, out = tdd.run(
        workdir,
        "package",
        candidates,
        workdir / "src"
    )

    assert ret == 1

    coverage = json.loads(out["coverage"])
    assert len(coverage["files"]) == 3
    assert (
            coverage["files"][str(Path("src/package/subpackage/mod.py"))]
            ["summary"]["percent_covered"] == 75.0
    )
    assert coverage["totals"]["percent_covered"] == 75.0

    tests = ET.fromstring(out["tests"])
    assert len(tests) == 1
    assert tests[0].attrib["failures"] == '1'
    assert tests[0].attrib["tests"] == '4'
    assert tests[0].attrib["skipped"] == '0'


def test_process(resolver):
    # import xml.dom; print(xml.dom.minidom.parseString(out["tests"]).toprettyxml())
    result = {
        "coverage": resolver.resolve("coverage.json").read_text(),
        "tests": resolver.resolve("junit.xml").read_text(),
    }
    assert result
