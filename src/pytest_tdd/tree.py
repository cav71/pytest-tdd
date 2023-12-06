# tree -aF layouts/my-project

from __future__ import annotations
import os
import sys
import collections
from typing import Callable
from pathlib import Path
import argparse
import dataclasses as dc

import click


class NodeError(Exception):
    pass


class NodeTypeErrror(NodeError):
    pass


class NodeValueError(NodeError):
    pass


@dc.dataclass
class Node:
    name: str = ""
    kind: str = "file"
    children: list[Node] = dc.field(default_factory=list)
    parent: Node | None = None
    xpath: list[str] = dc.field(default_factory=list)

    # TODO add this
    def __post_init__(self):
        if self.name.endswith("/") or self.name.endswith("\\"):
            self.kind = "dir"
            self.name = self.name[:-1]

    def append(self, node: None) -> Node:
        self.children.append(node)
        node.parent = self
        return self

    @property
    def level(self) -> int:
        counter = 0
        cur = self
        while cur:
            cur = cur.parent
            counter += 1
        return counter

    @property
    def path(self) -> str:
        key = []
        cur = self
        while cur:
            key.append(cur.name)
            cur = cur.parent  # type: ignore
        return "".join(reversed(key))

    def __repr__(self) -> str:
        return f"<Node xpath={'/'.join(self.xpath)} kind={self.kind}>"
        key = []
        cur = self
        while cur:
            key.append(cur.name)
            cur = cur.parent
        return f"<None key={''.join(reversed(key))}>"


def dfs(root: Node, fn: Callable[[Node], None]) -> None:
    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        fn(node)
        for child in node.children:
            queue.appendleft(child)  # type: ignore


@dc.dataclass
class Tree:
    root: Node

    def __post_init__(self):
        self.root.xpath = [self.root.name]

    def touch(self, dest: list[str] | tuple[str, ...], kind: str | None = None):
        kind = kind or (
            "dir" if (dest[-1].endswith("/") or dest[-1].endswith("\\")) else "file"
        )

        def make_node(
            parent: Node, key: list[str] | tuple[str, ...], nkind: str | None = None
        ) -> Node:
            if parent.kind != "dir":
                raise NodeTypeErrror(f"trying to insert {key} under {parent}")
            name = key[-1].rstrip("/").rstrip("\\")
            found = [child for child in parent.children if (child.xpath[-1] == name)]
            if found:
                breakpoint()
                raise NodeValueError(
                    f"trying to insert under {parent} a duplicate node {name}"
                )

            node = Node(name=name, kind="dir" if nkind is None else kind)
            node.xpath = [*parent.xpath, name]
            node.parent = parent
            return node

        assert self.root, "no root defined"
        cur = self.root
        breakpoint()
        level, n = 0, len(dest)
        while level < (n - 1):
            if cur.xpath[level] != dest[level]:
                node = make_node(cur, dest[: level + 1])
                cur.children.append(node)

            found = [ child for child in cur.children if child.xpath[level] == dest[level]]
            cur = found[0]
            level += 1

        if level == (n - 1):
            node = make_node(cur, dest[: level + 1], nkind=kind)
            cur.children.append(node)
            pass

    def append(self, dest: list[str] | tuple[str, ...]) -> None:
        def make_node(parent: Node, key: list[str] | tuple[str, ...]):
            node = Node(name=key[-1], kind="dir" if key[-1].endswith("/") else "file")
            node.parent = parent
            return node

        cur = self.root
        level = 0
        n = len(dest)
        while level < n:
            for child in cur.children:
                if child.name == dest[level]:
                    cur = child  # type: ignore
                    break
            else:
                node = make_node(cur, dest[: level + 1])
                cur.children.append(node)
                cur = cur.children[-1]  # type: ignore

            level += 1

    def generate(self, dryrun: bool = True):
        def maker(node):
            path = Path(node.path)
            if node.kind == "dir":
                if dryrun:
                    print(f"  mkdir -p {path}")
                else:
                    path.mkdir(exist_ok=True, parents=True)
            else:
                if dryrun:
                    print(f"  touch    {node.path}")
                else:
                    path.touch()

        if dryrun:
            print("Will generate:")
        dfs(self.root, maker)


def ls(path):
    from collections import deque

    root = Node(path.name, "dir")
    for sub in path.rglob("*"):
        cur = root
        subpath = sub.relative_to(path)
        queue = deque(str(subpath).split(os.sep))
        while queue:
            node = queue.popleft()
            child = ([c for c in cur.children if c.name == node] or [None])[0]
            if not child:
                node = Node(
                    node, "dir" if queue else "dir" if subpath.is_dir() else "file"
                )
                cur.children.append(node)
                cur = cur.children[-1]
            else:
                cur = child
    return root


def parse(txt: str) -> Tree:
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

    tree = Tree(Node("", "dir"))
    for key in result:
        tree.append(key)
    return tree


def generate(dstdir: Path, txt: str) -> list[str]:
    tree = parse(txt)
    tree.root.name = f"{dstdir.resolve()}{os.sep}"
    tree.generate(dryrun=False)
    result = []
    for path in sorted(dstdir.rglob("*")):
        rpath = str(path.relative_to(dstdir)).replace(os.sep, "/")
        result.append(f"{rpath}/" if path.is_dir() else f"{rpath}")
    return result


@click.group()
def main():
    pass


@main.command()
@click.argument("destdir", type=click.Path(path_type=Path))  # type: ignore
@click.option("-g", "--generate", is_flag=True)
@click.argument("src", type=click.File("r"))
def create(destdir, src, generate):
    """regenerates a new directory tree from the `tree -aF` output
src/pytest_tdd/tree.py
    \b
    Eg.
        # this will regenerate the directory tree layouts/my-project 
        # under destdir

        tree -aF layouts/my-project | \\
          python -m pytest_tdd.tree create --generate destdir -
    """
    if destdir.exists():
        raise click.UsageError(f"dest dir present '{destdir}'")

    tree = parse(src.read())
    tree.root.name = str(destdir.expanduser().resolve()) + "/"
    tree.generate(not generate)


def xmain():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["ls", "tojson"])
    parser.add_argument("value", nargs="?", type=Path)
    args = parser.parse_args()

    # tree -aF layouts/my-project
    if args.command == "ls":
        if not args.value or not args.value.exists():
            parser.error(f"missing or not existing {args.value=}")
        ls(args.value)
    else:
        if args.value in {"-", None}:
            tree = parse(sys.stdin.read())
        else:
            tree = parse(args.value.read_text())
        dfs(tree.root, lambda n: print(f" {n=}"))
        breakpoint()
        pass


if __name__ == "__main__":
    main()
