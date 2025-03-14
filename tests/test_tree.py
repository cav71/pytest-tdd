from __future__ import annotations

import collections
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

from pytest_tdd import tree as ptree

TREE = """
package2/modF.py
package2/__init__.py
package2/subpackageD/modH.py
package2/subpackageD/tests/test_modD.py
package2/subpackageC/modG.py
tests/test_modG.py
tests/test_modD.py
tests/package1/subpackageB/test_modC.py
tests/package1/test_modA.py
tests/subpackageC/test_modG.py
src/package1/subpackageA/modC.py
src/package1/subpackageA/__init__.py
src/package1/__init__.py
src/package1/modB.py
src/package1/modA.py
src/package1/subpackageB/tests/test_modD.py
src/package1/subpackageB/__init__.py
src/package1/subpackageB/modE.py
src/package1/subpackageB/modD.py
xyz/abc/
"""

EXPECTED = """\
/
├── package2/
│== ├── __init__.py
│== ├── modF.py
│== ├── subpackageC/
│== │== └── modG.py
│== └── subpackageD/
│==     ├── modH.py
│==     └── tests/
│==         └── test_modD.py
├── src/
│== └── package1/
│==     ├── __init__.py
│==     ├── modA.py
│==     ├── modB.py
│==     ├── subpackageA/
│==     │== ├── __init__.py
│==     │== └── modC.py
│==     └── subpackageB/
│==         ├── __init__.py
│==         ├── modD.py
│==         ├── modE.py
│==         └── tests/
│==             └── test_modD.py
├── tests/
│== ├── package1/
│== │== ├── subpackageB/
│== │== │== └── test_modC.py
│== │== └── test_modA.py
│== ├── subpackageC/
│== │== └── test_modG.py
│== ├── test_modD.py
│== └── test_modG.py
├── xyz/
│== └── abc/
└── zoo/
    └── bar/
        └── xxx
"""


def counting(root: ptree.Node) -> dict[ptree.Kind, int]:
    counters = {ptree.Kind.DIR: 0,
                 ptree.Kind.FILE: 0
    }
    queue = collections.deque([root])
    while queue:
        n = len(queue)
        for _ in range(n):
            node = queue.popleft()
            counters[node.kind] += 1
            queue.extendleft(node.children)
    return counters


def getfiles(path: Path) -> list[Path]:
    return sorted(p.relative_to(path) for p in path.rglob("*"))


def test_mktree_fixture(mktree):
    """create a dir tree (internal)"""
    dstdir = mktree(TREE)

    assert (dstdir / "package2/modF.py").exists()
    assert (dstdir / "xyz/abc").is_dir()

    dirs, files = 0, 0
    for path in dstdir.rglob("*"):
        if path.is_dir():
            dirs += 1
        else:
            files += 1
    assert files == 19
    assert dirs == 15


def test_create(mktree):
    dstdir = mktree(TREE)

    pytest.raises(
        ptree.InvalidNodeType, ptree.create,
        dstdir / "tests" / "test_modD.py")
    root = ptree.create(dstdir)

    # count all nodes
    assert counting(root) == {
        ptree.Kind.DIR: 16,  # it includes the root node
        ptree.Kind.FILE: 19
    }
    # to debug this:
    #   ptree.showtree(root)
    #   from subprocess import check_output
    #   print(check_output(["tree", "-aF", str(dstdir)], encoding="utf-8"))


def test_find(mktree, pretty):
    dstdir = mktree(TREE)
    root = ptree.create(dstdir)

    with pretty(msg="initial-check"):
        assert counting(root) == {
            ptree.Kind.DIR: 16,  # it includes the root node
            ptree.Kind.FILE: 19
        }

    with pretty(msg="find-an-existing-path"):
        node = ptree.find(root, "package2/subpackageD/tests/test_modD.py")
        assert node.xpath == [
            "", "package2", "subpackageD", "tests", "test_modD.py"
        ]
        assert node.kind == ptree.Kind.FILE
        assert counting(root) == {
            ptree.Kind.DIR: 16,  # it includes the root node
            ptree.Kind.FILE: 19
        }

    with pretty(msg="find-a-non-existing-root-dir"):
        assert ptree.find(root, "booo/") is None

    with pretty(msg="find-and-add-a-non-existing-root-dir"):
        node = ptree.find(root, "booo/", create=True)
        assert node.xpath == ["", "booo"]
        assert counting(root) == {
            ptree.Kind.DIR: 17,  # it includes the root node
            ptree.Kind.FILE: 19
        }

    with pretty(msg="find-a-non-existing-dir"):
        assert ptree.find(root, "zoo/bar/") is None

    with pretty(msg="find-and-add-a-non-existing-dir"):
        node = ptree.find(root, "zoo/bar/", create=True)
        assert node.xpath == ["", "zoo", "bar"]
        assert counting(root) == {
            ptree.Kind.DIR: 19,  # it includes the root node
            ptree.Kind.FILE: 19
        }

    with pretty(msg="find-a-non-existing-file"):
        assert ptree.find(root, "zoo/bar/xxx") is None

    with pretty(msg="find-and-add-a-non-existing-file"):
        node = ptree.find(root, "zoo/bar/xxx", create=True)
        assert node.xpath == ["", "zoo", "bar", "xxx"]
        assert counting(root) == {
            ptree.Kind.DIR: 19,  # it includes the root node
            ptree.Kind.FILE: 20
        }


def test_write(mktree):
    """write a dir tree"""
    srcdir = mktree(TREE, subpath="src")
    dstdir = srcdir.parent / "dst"

    root = ptree.create(srcdir)
    ptree.write(dstdir, root)

    assert getfiles(srcdir) == getfiles(dstdir)


def test_dumps(mktree):
    srcdir = mktree(TREE, subpath="src")
    root = ptree.create(srcdir)

    assert ptree.find(root, "package2/subpackageD/tests/test_modD.py")

    assert not ptree.find(root, "zoo/bar/", create=False)
    assert ptree.find(root, "zoo/bar/", create=True)
    assert ptree.find(root, "zoo/bar/xxx", create=True)
    assert counting(root) == {
        ptree.Kind.DIR: 18,  # it includes the root node
        ptree.Kind.FILE: 20
    }

    assert ptree.dumps(root, nbs=" ") == EXPECTED.replace("=", " ")
    assert not (srcdir / "zoo" / "bar").exists()
    (srcdir / "zoo" / "bar").mkdir(parents=True, exist_ok=True)
    (srcdir / "zoo" / "bar" / "xxx").write_text("")
    assert ptree.dumps(root, nbs="=") == EXPECTED


@pytest.mark.skipif(sys.platform != "linux", reason=f"requires linux, not {os.name}")
@mock.patch.dict(os.environ, {"LOCAL": "1"})
def test_dumps_unix(mktree):
    from subprocess import check_output

    srcdir = mktree(TREE, subpath="src")
    expected = ptree.dumps(ptree.create(srcdir), nbs="\u00A0")

    # skip the initial and final lines
    found = check_output(["tree", "-aF", str(srcdir)], encoding="utf-8")
    # chopping the first and last lines
    found = "/\n" + "\n".join(found[:-2].split("\n")[1:-1])
    assert found == expected


def test_parse():
    txt = """\
└── src/
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
    ├── tests/
    │   ├── package1/
    │   │   ├── subpackageB/
    │   │   │   └── test_modC.py
    │   │   └── test_modA.py
    │   ├── subpackageC/
    │   │   └── test_modG.py
    │   ├── test_modD.py
    │   └── test_modG.py
    └── xyz/
        └── abc/
"""
    root = ptree.parse(txt)
    assert counting(root) == {
        ptree.Kind.DIR: 17,  # it includes the root node
        ptree.Kind.FILE: 19
    }


def test_roundtrip(mktree):
    def getfiles(path):
        return sorted(p.relative_to(path) for p in path.rglob("*"))

    # create a fs tree under srcdir
    leftdir = mktree(TREE, subpath="left")
    assert len(getfiles(leftdir)) == 34

    # generate the tree structure in root
    # and generate a fs dump under destdir
    root = ptree.create(leftdir)
    destdir = leftdir.parent / "right"
    assert len(getfiles(destdir)) == 0
    ptree.write(destdir, root)
    assert getfiles(leftdir) == getfiles(destdir)

    # generate a str representation of root
    txt = ptree.dumps(root)
    root = ptree.parse(txt)
    destdir = leftdir.parent / "right2"
    assert len(getfiles(destdir)) == 0
    ptree.write(destdir, root)
    assert getfiles(leftdir) == getfiles(destdir)


def test_conftest(mktree):
    srcdir = mktree("""
└── my-project/
    ├── src/
    │   └── my_package/
    │       └── module1.py
    └── tests/
        └── test_module1.py
""", subpath="x")
    root = ptree.create(srcdir)
    assert (root.name, root.kind) == ("", ptree.Kind.DIR)
    assert counting(root) == {
        ptree.Kind.FILE: 2,
        ptree.Kind.DIR: 4 + 1,
    }
