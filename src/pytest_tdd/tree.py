# # tree -aF layouts/my-project
from __future__ import annotations

import sys
import io
import collections
import dataclasses as dc
import enum
from pathlib import Path
from typing import TextIO, TypeVar


IOType = TypeVar("IOType", io.StringIO, TextIO)


# import os
# import sys
# import collections
# from typing import Callable
# import argparse
#
# import click
#
#
class NodeError(Exception):
    pass


#
#
class NodeTypeError(NodeError):
    pass


#
#
# class NodeValueError(NodeError):
#     pass
#
#
class Kind(enum.IntEnum):
    DIR = 1
    FILE = 2


@dc.dataclass
class Node:
    name: str
    kind: Kind
    children: list[Node] = dc.field(default_factory=list)
    parent: Node | None = None

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
    def xpath(self) -> Path:
        result = []
        cur: Node | None = self
        while cur is not None:
            result.append(cur.name)
            cur = cur.parent  # type: ignore
        return Path(*reversed(result))


def walk(path: Path) -> Node:
    if not path.is_dir():
        raise NodeTypeError("path is not a directory", path)

    root = Node("", Kind.DIR)
    queue = collections.deque([root])
    while queue:
        n = len(queue)
        for i in range(n):
            cur = queue.popleft()
            if not (sub := (path / cur.xpath)).is_dir():
                continue
            for child in sorted(sub.glob("*")):
                node = Node(
                    child.name, Kind.DIR if child.is_dir() else Kind.FILE, parent=cur
                )
                cur.children.append(node)
                if child.is_dir():
                    queue.appendleft(node)
    return root


def find(loc: str, root: Node):
    pass


def create(path: Path, root: Node) -> None:
    # TODO implement this
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        dst = path / node.xpath
        if node.kind == Kind.FILE:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text("")
        else:
            dst.mkdir(parents=True, exist_ok=True)
            for child in node.children:
                queue.appendleft(child)


def dumps(root: Node) -> str:
    # TODO implement this
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
                        indent + ("    " if is_last else "│\u00A0\u00A0 "),
                        is_last2,
                    )
                )
        else:
            print(f"{indent}{'└──' if is_last else '├──'} {node.name}", file=buffer)
    return buffer.getvalue()


def plot(root: Node, buffer: IOType = sys.stdout) -> IOType:  # type: ignore
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

    txt = plot(root, io.StringIO()).getvalue()

    with NamedTemporaryFile() as out:
        out.write(txt.encode("utf-8"))
        out.flush()
        dot = Path(sys.executable).parent / "dot"
        check_call([str(c) for c in [dot, "-Tpng", "-odeleteme.png", out.name]])
        call(["open", "deleteme.png"])


#     name: str = ""
#     kind: str = "file"
#     children: list[Node] = dc.field(default_factory=list)
#     parent: Node | None = None
#     xpath: list[str] = dc.field(default_factory=list)
#
#     # TODO add this
#     def __post_init__(self):
#         if self.name.endswith("/") or self.name.endswith("\\"):
#             self.kind = "dir"
#             self.name = self.name[:-1]
#
#     def append(self, node: None) -> Node:
#         self.children.append(node)
#         node.parent = self
#         return self
#
#     @property
#     def level(self) -> int:
#         counter = 0
#         cur = self
#         while cur:
#             cur = cur.parent
#             counter += 1
#         return counter
#
#     @property
#     def path(self) -> str:
#         key = []
#         cur = self
#         while cur:
#             key.append(cur.name)
#             cur = cur.parent  # type: ignore
#         return "".join(reversed(key))
#
#     def __repr__(self) -> str:
#         return f"<Node xpath={'/'.join(self.xpath)} kind={self.kind}>"
#         key = []
#         cur = self
#         while cur:
#             key.append(cur.name)
#             cur = cur.parent
#         return f"<None key={''.join(reversed(key))}>"
#
#
# def dfs(root: Node, fn: Callable[[Node], None]) -> None:
#     queue = collections.deque([root])
#     while queue:
#         node = queue.popleft()
#         fn(node)
#         for child in node.children:
#             queue.appendleft(child)  # type: ignore
#
#
# @dc.dataclass
# class Tree:
#     root: Node
#
#     def __post_init__(self):
#         self.root.xpath = [self.root.name]
#
#     def touch(self, dest: list[str] | tuple[str, ...], kind: str | None = None):
#         kind = kind or (
#             "dir" if (dest[-1].endswith("/") or dest[-1].endswith("\\")) else "file"
#         )
#         key = [ d.rstrip("/").rstrip("\\") for d in dest ]
#
#
#         breakpoint()
#         #assert self.root.xpath[0] ==
#         key[:1], f"{dest=} should be rooted in {self.root.xpath}"
#         if self.root.xpath[0] != key[0]:
#             for child in self.root.children:
#                 if child.xpath[1] == key[0]:
#                     cur = child
#                     break
#             else:
#                 pass
#
#         cur = self.root
#         for level, k in enumerate(key):
#             if cur.xpath[level] != k:
#                 pass
#
#         queue = collections.deque([self.root])
#
#         level = 0
#         while queue and level < len(key):
#             n = len(queue)
#             nodes = []
#             for i in range(n):
#                 node = queue.popleft()
#                 nodes.append(node)
#             for node in nodes:
#                 if found:= [c for c in node.children if c.xpath[level] == key[level]]:
#                     for child in found:
#                         queue.appendleft(child)
#                 else:
#                     node = Node(parent=parent, kind="dir")
#                     parent = node
#             level += 1
#
#
#
#
#         def make_node(
#             parent: Node, key: list[str] | tuple[str, ...], nkind: str | None = None
#         ) -> Node:
#             if parent.kind != "dir":
#                 raise NodeTypeError(f"trying to insert {key} under {parent}")
#             name = key[-1].rstrip("/").rstrip("\\")
#             found = [child for child in parent.children if (child.xpath[-1] == name)]
#             if found:
#                 breakpoint()
#                 raise NodeValueError(
#                     f"trying to insert under {parent} a duplicate node {name}"
#                 )
#
#             node = Node(name=name, kind="dir" if nkind is None else kind)
#             node.xpath = [*parent.xpath, name]
#             node.parent = parent
#             return node
#
#         assert self.root, "no root defined"
#         cur = self.root
#         level, n = 0, len(dest)
#         breakpoint()
#         while level < n:
#             key = dest[level].rstrip("/").rstrip("\\")
#             if key == cur.xpath[level]:
#                 pass
#             elif found := [c for c in cur.children if c.xpath[-1] == key]:
#                 cur = found[0]
#             else:
#                 node = make_node(cur, dest[: level + 1])
#
#             continue
#
#             #while (level < len(cur.xpath)) and cur.xpath[level] == key:
#             #    level += 1
#             #    continue
#             #cond = cur.xpath[level] != dest[level].rstrip("/").rstrip("\\")
#             #cond = cond or not cur.children
#             #while level < len(cur.xpath):
#             #    pass
#             if level >= (len(cur.xpath)):
#                 pass
#             if cur.xpath[-1] != key:
#                 node = make_node(cur, dest[: level + 1])
#                 cur.children.append(node)
#                 found = [ child for child
#                 in cur.children if child.xpath[level] == key]
#                 cur = found[0]
#             level += 1
#
#         if level == (n - 1):
#             node = make_node(cur, dest[: level + 1], nkind=kind)
#             cur.children.append(node)
#             pass
#
#     def append(self, dest: list[str] | tuple[str, ...]) -> None:
#         def make_node(parent: Node, key: list[str] | tuple[str, ...]):
#             node = Node(name=key[-1], kind="dir" if key[-1].endswith("/") else "file")
#             node.parent = parent
#             return node
#
#         cur = self.root
#         level = 0
#         n = len(dest)
#         while level < n:
#             for child in cur.children:
#                 if child.name == dest[level]:
#                     cur = child  # type: ignore
#                     break
#             else:
#                 node = make_node(cur, dest[: level + 1])
#                 cur.children.append(node)
#                 cur = cur.children[-1]  # type: ignore
#
#             level += 1
#
#     def generate(self, dryrun: bool = True):
#         def maker(node):
#             path = Path(node.path)
#             if node.kind == "dir":
#                 if dryrun:
#                     print(f"  mkdir -p {path}")
#                 else:
#                     path.mkdir(exist_ok=True, parents=True)
#             else:
#                 if dryrun:
#                     print(f"  touch    {node.path}")
#                 else:
#                     path.touch()
#
#         if dryrun:
#             print("Will generate:")
#         dfs(self.root, maker)
#
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
