# # tree -aF layouts/my-project
from __future__ import annotations

import sys
import io
import collections
import dataclasses as dc
import enum
from pathlib import Path
from typing import TextIO


class NodeError(Exception):
    pass


class NodeTypeError(NodeError):
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
    kind: Kind
    children: list[Node] = dc.field(default_factory=list)
    parent: Node | None = None

    def __post_init__(self):
        if self.name.endswith("/"):
            if self.kind != Kind.DIR:
                raise InvalidNodeName(f"cannot use {self.name=} for a non dir")
        self.name = self.name.rstrip("/")

    def append(self, node: Node) -> None:
        node.parent = self
        self.children.append(node)

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"kind={self.kind} "
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
            cur = cur.parent  # type: ignore
        return list(reversed(result))

    @property
    def path(self) -> Path:
        return Path(*self.xpath)


def create(path: Path) -> Node:
    """
    Generates a tree out of path directory.

    Args:
        path: A Path object representing the directory to start the walk from.

    Returns:
        A Node object representing the root of the directory tree.

    Raises:
        NodeTypeError: If the specified path is not a directory.

    """
    if not path.is_dir():
        raise NodeTypeError("path is not a directory", path)

    root = Node("", Kind.DIR)
    queue = collections.deque([root])
    while queue:
        n = len(queue)
        for i in range(n):
            cur = queue.popleft()
            if not (sub := (path / cur.path)).is_dir():
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
    """find a node starting from root tree"""
    if isinstance(loc, str):
        lloc = collections.deque(loc.rstrip("/").split("/"))
        if loc.endswith("/"):
            lloc[-1] = f"{lloc[-1]}/"
    else:
        lloc = collections.deque(loc)
    kind = Kind.FILE
    if lloc[-1].endswith("/"):
        kind = Kind.DIR
        lloc[-1] = lloc[-1].rstrip("/")

    def lookup(node: Node, key: str) -> list[Node]:
        return [child for child in node.children if child.name == key]

    cur = root
    while lloc:
        path = lloc.popleft()
        found = lookup(cur, path)
        if not found:
            if create:
                cur.append(Node(path.rstrip("/"), Kind.DIR if lloc else kind))
            else:
                return None
        cur = lookup(cur, path)[0]

    return cur


def write(path: Path, root: Node) -> None:
    # TODO implement this
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        dst = path / node.path
        if node.kind == Kind.FILE:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text("")
        else:
            dst.mkdir(parents=True, exist_ok=True)
            for child in node.children:
                queue.appendleft(child)


def dumps(root: Node, nbs: str = " ") -> str:
    # use nbs="\u00A0" when comparing tree -aF

    buffer = io.StringIO()
    queue = collections.deque([(root, "", True)])
    counter = 0
    while queue:
        counter += 1
        node, indent, is_last = queue.pop()
        if node.kind == Kind.DIR:
            print(f"{indent}{'└──' if is_last else '├──'} {node.name}/", file=buffer)
            for i, child in enumerate(reversed(node.children)):
                is_last2 = i == 0
                queue.append(
                    (
                        child,
                        indent + ("    " if is_last else f"│{nbs}{nbs} "),
                        is_last2,
                    )
                )
        else:
            print(f"{indent}{'└──' if is_last else '├──'} {node.name}", file=buffer)
    return buffer.getvalue()


def parse(txt: str) -> Node | None:
    SEP = "├└│─\xa0"
    SEPS = f"{SEP} "

    def flevel(txt):
        for index, c in enumerate(txt):
            if c in SEPS:
                continue
            return int(index / 4), txt[index:]
        return 0, None

    def skip(txt):
        if not txt.strip():
            return True
        return line.lstrip()[:1] not in SEP

    result = []
    plevel = None
    data = []
    for line in txt.split("\n"):
        # print(f" > {line.rstrip()} {skip(line)}")
        if skip(line):
            continue
        level, name = flevel(line)
        if plevel is None:
            plevel = level

        if level > plevel:
            data.append(name)
        elif level < plevel:
            data = [*data[:-2], name]
        elif level == plevel:
            data = [*data[:-1], name]
        result.append(data[:])
        plevel = level
    result.sort()

    return None


def plot(root: Node, buffer: TextIO = sys.stdout) -> TextIO:  # type: ignore
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
    from tempfile import NamedTemporaryFile
    from subprocess import check_call, call

    buffer = plot(root, io.StringIO())
    if not hasattr(buffer, "getvalue"):
        return
    txt = buffer.getvalue()

    with NamedTemporaryFile() as out:
        out.write(txt.encode("utf-8"))
        out.flush()
        dot = Path(sys.executable).parent / "dot"
        check_call([str(c) for c in [dot, "-Tpng", "-odeleteme.png", out.name]])
        call(["open", "deleteme.png"])


#
# def ls(path):
#     from collections import deque
#
#     root = Node(path.name, "dir")
#     for sub in path.rglob("*"):
#         cur = root
#         subpath = sub.relative_to(path)
#         queue = deque(str(subpath).split(os.sep))
#         while queue:
#             node = queue.popleft()
#             child = ([c for c in cur.children if c.name == node] or [None])[0]
#             if not child:
#                 node = Node(
#                     node, "dir" if queue else "dir" if subpath.is_dir() else "file"
#                 )
#                 cur.children.append(node)
#                 cur = cur.children[-1]
#             else:
#                 cur = child
#     return root
#
#
# tree = Tree(Node("", "dir"))
# for key in result:
#     tree.append(key)
# return tree


#
#
# def generate(dstdir: Path, txt: str) -> list[str]:
#     tree = parse(txt)
#     tree.root.name = f"{dstdir.resolve()}{os.sep}"
#     tree.generate(dryrun=False)
#     result = []
#     for path in sorted(dstdir.rglob("*")):
#         rpath = str(path.relative_to(dstdir)).replace(os.sep, "/")
#         result.append(f"{rpath}/" if path.is_dir() else f"{rpath}")
#     return result
#
#
# @click.group()
# def main():
#     pass
#
#
# @main.command()
# @click.argument("destdir", type=click.Path(path_type=Path))  # type: ignore
# @click.option("-g", "--generate", is_flag=True)
# @click.argument("src", type=click.File("r"))
# def create(destdir, src, generate):
#     """regenerates a new directory tree from the `tree -aF` output
# src/pytest_tdd/tree.py
#     \b
#     Eg.
#         # this will regenerate the directory tree layouts/my-project
#         # under destdir
#
#         tree -aF layouts/my-project | \\
#           python -m pytest_tdd.tree create --generate destdir -
#     """
#     if destdir.exists():
#         raise click.UsageError(f"dest dir present '{destdir}'")
#
#     tree = parse(src.read())
#     tree.root.name = str(destdir.expanduser().resolve()) + "/"
#     tree.generate(not generate)
#
#
# def xmain():
#     parser = argparse.ArgumentParser()
#     parser.add_argument("command", choices=["ls", "tojson"])
#     parser.add_argument("value", nargs="?", type=Path)
#     args = parser.parse_args()
#
#     # tree -aF layouts/my-project
#     if args.command == "ls":
#         if not args.value or not args.value.exists():
#             parser.error(f"missing or not existing {args.value=}")
#         ls(args.value)
#     else:
#         if args.value in {"-", None}:
#             tree = parse(sys.stdin.read())
#         else:
#             tree = parse(args.value.read_text())
#         dfs(tree.root, lambda n: print(f" {n=}"))
#         breakpoint()
#         pass
#
#
# if __name__ == "__main__":
#     main()
