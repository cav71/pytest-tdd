from __future__ import annotations
import os
import collections

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

def test_mktree_fixture(mktree):
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


def test_walk(mktree):
    dstdir = mktree(TREE)

    pytest.raises(ptree.NodeTypeError, ptree.walk, dstdir / "tests" / "test_modD.py")
    root = ptree.walk(dstdir)

    # count all nodes
    counters = { ptree.Kind.DIR: 0,
                 ptree.Kind.FILE: 0
    }
    queue = collections.deque([root])
    while queue:
        n = len(queue)
        for _ in range(n):
            node = queue.popleft()
            counters[node.kind] += 1
            queue.extendleft(node.children)
    assert counters == {
        ptree.Kind.DIR: 16,  # it includes the root node
        ptree.Kind.FILE: 19
    }
    # to debug this:
    #   ptree.showtree(root)
    #   from subprocess import check_output
    #   print(check_output(["tree", "-aF", str(dstdir)], encoding="utf-8"))

def test_create(mktree):
    srcdir = mktree(TREE, "src")
    dstdir = srcdir.parent / "dst"

    root = ptree.walk(srcdir)
    left = list(sorted({
        (path.relative_to(srcdir), path.is_dir())
        for path in srcdir.rglob("*")
    }))

    ptree.create(dstdir, root)
    right = list(sorted({
        (path.relative_to(dstdir), path.is_dir())
        for path in dstdir.rglob("*")
    }))
    assert left == right


@pytest.mark.skipif(os.getenv("LOCAL") != "1", reason="set LOCAL=1 to run this test")
def test_dumps(mktree):
    from subprocess import check_output
    srcdir = mktree(TREE, "src")
    root = ptree.walk(srcdir)
    found = ptree.dumps(root.children[0])

    # skip the initial and final lines
    expected = check_output(["tree", "-aF", str(srcdir)], encoding="utf-8")
    expected = "\n".join(expected.strip().split("\n")[1:-1])
    assert found == expected



# def getnodes(tree: ptree.Tree) -> list[str]:
#     values = []
#
#     def acc(node):
#         values.append(node.path)
#
#     ptree.dfs(tree.root, acc)
#     return values
#
#
# def test_node():
#     a = N("A")
#     b = N("B")
#     c = N("C")
#     root = a.append(b).append(c)
#     assert root.level == 1
#     assert b.level == 2
#
#
# def test_dfs():
#     root = N(
#         "A",
#         children=[
#             N(
#                 "B",
#                 children=[
#                     N("B1"),
#                     N(
#                         "B2",
#                         children=[
#                             N("B21"),
#                         ],
#                     ),
#                 ],
#             ),
#             N(
#                 "C",
#                 children=[
#                     N("C1"),
#                 ],
#             ),
#             N("D", children=[]),
#         ],
#     )
#
#     values = []
#
#     def acc(node):
#         values.append(node.name)
#
#     ptree.dfs(root, acc)
#     assert values == ["A", "D", "C", "C1", "B", "B2", "B21", "B1"]
#
#
# def test_tree_append():
#     tree = ptree.Tree(N("A/"))
#
#     tree.touch(["A/", "B/"])
#     tree.touch(["A/", "B/", "C1/"])
#     tree.touch(["A/", "B/", "B1"])
#     tree.touch(["A/", "B/", "B2"])
#     return
#
#     # tree.append(["A/",])
#     # tree.append(["A/", "B/"])
#     # tree.append(["A/", "B/", "C1/"])
#     # tree.append(["A/", "B/", "B1"])
#     # tree.append(["A/", "B/", "B2"])
#
#     # tree.append("A/B/C1".split("/"))
#     # tree.append("A/B/B1".split("/"))
#     # tree.append("A/B/B2".split("/"))
#     # tree.append("A/C/C1/C1a".split("/"))
#     # tree.append("A/D".split("/"))
#     assert getnodes(tree) == [
#         "/root/",
#         "/root/A/",
#         "/root/A/B/",
#         "/root/A/B/B2",
#         "/root/A/B/B1",
#         "/root/A/B/C1/",
#     ]
#
#     breakpoint()
#     tree.touch(["A/", "B"])
#     pytest.raises(ptree.NodeValueError, tree.touch, ["A/", "B"])
#
#
# def test_generate(tmp_path):
#     found = ptree.generate(
#         tmp_path,
#         """
# my-project/
# ├── src/
# │   └── my_package/
# │       └── module1.py
# └── tests/
#     └── test_module1.py
#
# """,
#     )
#     assert set(found) == {
#         "src/",
#         "src/my_package/",
#         "src/my_package/module1.py",
#         "src/tests/",
#         "src/tests/test_module1.py",
#     }
