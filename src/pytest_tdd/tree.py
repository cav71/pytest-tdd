# # tree -aF layouts/my-project
"""Implementation of a directory tree structure.

This module provides a simple implementation of a directory tree structure.
It allows you to:

    - create a tree instance out of a directory (`create`)
    - to find a node in the tree structure (`find`)
    - to dump the tree structure to a string (`dumps`, similar ro the
      `tree -aF` command in Linux)
    - to write the tree structure to a directory (`write`)
    - to plot the tree structure using graphviz

The TL;DR is::

    # generate a tree out of a path
    >>> root = tree.create(Path("src"))

    # prints the tree structure (same as `tree -aF`)
    >>> print(tree.dumps(root, nbs="\\\\u00A0"))
    /
    └── pytest_tdd/
        ├── __init__.py
        ├── __pycache__/
        │   ├── __init__.cpython-313.pyc
        │   ├── misc.cpython-313.pyc
        │   ├── script.cpython-313.pyc
        │   ├── tdd.cpython-313.pyc
        │   └── tree.cpython-313.pyc
        ├── misc.py
        ├── script.py
        ├── tdd.py
        └── tree.py

    # round trip!
    >>> assert tree.dumps(tree.parse(tree.dumps(root))) == tree.dumps(root)

    # find a node in the tree structure and print it
    >>> node = tree.find(root, ['pytest_tdd', '__pycache__'])
    >>> print(tree.dumps(node, nbs="\\\\u00A0"))
    __pycache__/
    ├── __init__.cpython-313.pyc
    ├── misc.cpython-313.pyc
    ├── script.cpython-313.pyc
    ├── tdd.cpython-313.pyc
    └── tree.cpython-313.pyc

    # write the tree structure under `tmp` directory
    >>> tree.write(Path("tmp"), node)

"""
from __future__ import annotations

import argparse
import shutil
import sys
import io
import collections
import dataclasses as dc
import enum
from pathlib import Path
from typing import TextIO


class NodeError(Exception):
    pass


class InvalidNodeType(NodeError):
    pass


class InvalidNodeName(NodeError):
    pass


class LocationError(NodeError):
    pass


class Kind(enum.IntEnum):
    DIR = 1
    FILE = 2


@dc.dataclass
class Node:
    name: str
    kind: Kind | None = None
    children: list[Node] = dc.field(default_factory=list)
    parent: Node | None = None

    def __post_init__(self) -> None:
        if self.name.endswith("/"):
            if self.kind is None:
                self.kind = Kind.DIR
            if self.kind != Kind.DIR:
                raise InvalidNodeName(f"cannot use {self.name=} for a non dir")
        assert self.kind
        self.name = self.name.rstrip("/")

    def append(self, node: Node) -> None:
        node.parent = self
        self.children.append(node)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"kind={self.kind.name if self.kind else self.kind} "
            f"parent={self.parent.name if self.parent else None} "
            f"children={len(self.children)} "
            f"at {hex(id(self))}>"
        )

    @property
    def xpath(self) -> list[str]:
        result = []
        cur: Node | None = self
        while cur is not None:
            result.append(cur.name)
            cur = cur.parent
        return list(reversed(result))

    @property
    def path(self) -> Path:
        return Path(*self.xpath)


def create(path: Path | str) -> Node:
    """
    Generates a tree out of path directory.

    Args:
        path: A Path object representing the directory to start the walk from.

    Returns:
        A Node object representing the root of the directory tree.

    Raises:
        InvalidNodeType: If the specified path is not a directory.

    Examples:

        To generate a tree out of a directory::

            >>> tree.create(Path("somedir"))
            Node(name='somedir', ...)
    """
    src = Path(path)
    if not src.is_dir():
        raise InvalidNodeType("path is not a directory", src)

    root = Node("", Kind.DIR)
    queue = collections.deque([root])
    while queue:
        n = len(queue)
        for i in range(n):
            cur = queue.popleft()
            if not (sub := (src / cur.path)).is_dir():
                continue
            for child in sorted(sub.glob("*")):
                node = Node(
                    child.name, Kind.DIR if child.is_dir() else Kind.FILE, parent=cur
                )
                cur.children.append(node)
                if child.is_dir():
                    queue.appendleft(node)
    return root


def find(root: Node, loc: str | list[str], create: bool = False) -> Node | None:
    """
    Find a node starting from root tree.

    Args:
        root: parsed tree root node
        loc: lookup for a node starting from root tree, can be a string or a list of strings.
        create: if `loc` does not exist in the tree, create it if `create` is True, otherwise return None.

    Returns:
        node pointing to the location if found, otherwise None.

    Examples:

        To lookup for a path::

            >>> find(root, ['a', 'b', 'c'])
            None # if the a/b/c does not exist in the tree

            >>> find(root, ['a', 'b', 'c'], create=True)
            Node(name='c', ...)

    """
    if isinstance(loc, str):
        lloc = collections.deque(loc.rstrip("/").split("/"))
        if loc.endswith("/"):
            lloc[-1] = f"{lloc[-1]}/"
    else:
        lloc = collections.deque(loc[:])
    kind = Kind.FILE
    if lloc[-1].endswith("/"):
        kind = Kind.DIR
        lloc[-1] = lloc[-1].rstrip("/")
    for i in range(len(lloc)):
        lloc[i] = lloc[i].rstrip("/")

    def lookup(node: Node, key: str) -> list[Node]:
        return [child for child in node.children if child.name == key]

    cur = root
    while lloc:
        path = lloc.popleft()
        found = lookup(cur, path)
        if not found:
            if create:
                if cur.kind == Kind.FILE:
                    raise InvalidNodeType(
                        f"cannot insert {path=} under {cur=}", cur, path
                    )
                cur.append(Node(path.rstrip("/"), Kind.DIR if lloc else kind))
            else:
                return None
        cur = lookup(cur, path)[0]

    return cur


def write(path: Path | str, root: Node) -> None:
    """
    Writes a tree structure under path.

    The function iteratively processes the given root node and its children
    generating a filesystem dump of `root`.

    Args:
        path: The base directory where the tree structure will be created.
        root: The root node of the tree structure to be written, which determines the
            hierarchy of files and directories to be generated.
    """
    dstdir = Path(path)

    if not dstdir.exists():
        dstdir.mkdir(parents=True, exist_ok=True)

    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        dst = dstdir / node.path
        dst.relative_to(dst)
        if node.kind == Kind.FILE:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text("")
        else:
            dst.mkdir(parents=True, exist_ok=True)
            for child in node.children:
                queue.appendleft(child)


def dumps(root: Node, nbs: str = " ") -> str:
    """
    Returns a string representation of the tree structure.

    The string representation consists of a tree structure
    with each node represented by a line: this is equivalent to the
    output of the `tree -aF` command uf nbs is "\\\\u00A0".

    Args:
        root: the root node of the tree structure
        nbs: the string used to represent the indentation of
             the nodes in the tree structure.

    Returns:
        The string representation of the tree structure.

    """
    # use nbs="\u00A0" when comparing tree -aF

    buffer = io.StringIO()
    queue = collections.deque([(root, "", True)])
    counter = 0
    head = True
    while queue:
        counter += 1
        node, indent, is_last = queue.pop()
        if node.kind == Kind.DIR:
            pre = "" if head else "└── " if is_last else "├── "
            print(f"{indent}{pre}{node.name}/", file=buffer)
            for i, child in enumerate(reversed(node.children)):
                is_last2 = i == 0
                mid = indent + ("    " if is_last else f"│{nbs}{nbs} ")
                if head:
                    mid = "" if is_last else f"│{nbs}{nbs} "
                queue.append(
                    (
                        child,
                        mid,
                        is_last2,
                    )
                )
            if head:
                head = False
        else:
            print(f"{indent}{'└──' if is_last else '├──'} {node.name}", file=buffer)
    return buffer.getvalue()


def parse(txt: str) -> Node | None:
    plevel = 0
    sep = "─ "
    result = []
    context: collections.deque[str] = collections.deque()
    for line in txt.split("\n"):
        if sep not in line:
            continue
        index = line.find(sep) + len(sep)
        level = index // 4
        key = line[index:].rstrip()
        if level > plevel:
            context.append(key)
            plevel = level
        elif level == plevel:
            result.append(list(context))
            context[-1] = key
        else:
            result.append(list(context))
            for _ in range(plevel - level + 1):
                context.pop()
            context.append(key)
            plevel = level
    if context:
        result.append(list(context))

    root = Node("/")
    for path in result:
        find(root, path, create=True)
    return root


def plot(root: Node, buffer: TextIO = sys.stdout) -> TextIO:
    print("digraph {", file=buffer)

    mapper = {}
    counter = 0
    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        key, val = f"n-{counter:05}", node.name
        mapper[hex(id(node))] = (key, val)
        print(f'  "{key}" [label="{val}"]', file=buffer)

        for n in reversed(node.children or []):
            queue.appendleft(n)
        counter += 1

    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        start = mapper[hex(id(node))]

        for n in reversed(node.children or []):
            end = mapper[hex(id(n))]
            print(f'  "{start[0]}" -> "{end[0]}"', file=buffer)
            queue.appendleft(n)

    print("}", file=buffer)
    return buffer


def showtree(root: Node) -> None:  # pragma: no cover
    from time import sleep
    from contextlib import ExitStack
    from tempfile import NamedTemporaryFile
    from subprocess import check_call, call

    if sys.platform not in {"linux", "darwin"}:
        raise NotImplementedError(f"cannot use this on {sys.platform}")

    buffer = plot(root, io.StringIO())
    if not hasattr(buffer, "getvalue"):
        return
    txt = buffer.getvalue()

    with ExitStack() as stack:
        dotout = stack.enter_context(NamedTemporaryFile())
        pngout = stack.enter_context(NamedTemporaryFile(suffix=".png"))
        dotout.write(txt.encode("utf-8"))
        dotout.flush()
        if not (exe := shutil.which("dot")):
            raise FileNotFoundError("cannot find dot executable, install graphviz")
        cmd = [
            exe,
            "-Tpng",
            f"-o{pngout.name}",
            dotout.name,
        ]
        check_call([str(c) for c in cmd])
        pngout.file.flush()
        if sys.platform == "darwin":
            call(["open", pngout.name])
        elif sys.platform == "linux":
            call(["xdg-open", pngout.name])
        sleep(1)


def main() -> None:
    class F(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass

    parser = argparse.ArgumentParser(
        formatter_class=F,
        description="parse srcdir into a tree structure",
        epilog="""
walks the srcdir and creates a tree structure applying some operations:

  --into dumps the tree structure into a new directory
  --display dumps the tree structure into png file using graphviz
  --graphviz dumps the tree structure into a dot file
  
 """)
    parser.add_argument("srcdir", type=Path, help="source directory")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-i", "--into", type=Path, help="destination directory")
    group.add_argument("--graphviz", action="store_true", help="write the structure to a png file")
    group.add_argument("--display", action="store_true", help="write the structure to a png file")
    args = parser.parse_args()

    if not args.srcdir.exists():
        parser.error(f"dir not found, {args.srcdir}")
    if not args.srcdir.is_dir():
        parser.error(f"path is not a dir, {args.srcdir}")

    root = create(args.srcdir)

    if args.into:
        write(args.into, root)
    elif args.graphviz:
        print(plot(root))
    elif args.display:
        showtree(root)
    else:
        root.name = args.srcdir
        print(dumps(root))


if __name__ == "__main__":
    main()
