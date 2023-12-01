# tree -aF layouts/my-project

from __future__ import annotations
import os
import sys
from typing import Literal
from pathlib import Path
import argparse
import dataclasses as dc

import click

from pytest_tdd.acbox import trees


@dc.dataclass
class Node(trees.N):
    name: str = ""
    kind: Literal["dir"] | Literal["file"] = "file"

    def level(self):
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

    def __repr__(self):
        key = []
        cur = self
        while cur:
            key.append(cur.name)
            cur = cur.parent
        return f"<None key={''.join(reversed(key))}>"


@dc.dataclass
class Tree:
    root: Node

    def append(self, key: list[str] | tuple[str]) -> None:
        def make_node(parent: Node, key: list[str]):
            node = Node(name=key[-1], kind="dir" if key[-1].endswith("/") else "file")
            node.parent = parent
            return node

        trees.append(self.root, key, "name", make_node)  # type: ignore

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
        trees.dfs(self.root, maker)


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
    tree.root.name = f"{dstdir.resolve()}/"
    tree.generate(dryrun=False)
    result = []
    for path in sorted(dstdir.rglob("*")):
        rpath = path.relative_to(dstdir)
        result.append(f"{rpath}/" if path.is_dir() else f"{rpath}")
    return result


@click.group()
def main():
    pass


@main.command()
@click.argument("destdir", type=click.Path(path_type=Path))
@click.option("-g", "--generate", is_flag=True)
@click.argument("src", type=click.File("r"))
def create(destdir, src, generate):
    """regenerates a new directory tree from the `tree -aF` output

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
        trees.dfs(tree.root, lambda n: print(f" {n=}"))
        breakpoint()
        pass


if __name__ == "__main__":
    main()