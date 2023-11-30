# tree -aF layouts/my-project

from __future__ import annotations
import os
import sys
from typing import Literal
from pathlib import Path
import argparse
import dataclasses as dc

from acbox.structures import trees


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

    @staticmethod
    def append(root, iterable):
        cur = root
        index = 0
        while index < len(iterable):
            for child in cur.children:
                if child.name == iterable[index]:
                    cur = child
                    break
            else:
                node = Node(
                    name=iterable[index],
                    kind="dir" if iterable[index].endswith("/") else "file",
                )
                node.parent = cur
                cur.children.append(node)
                cur = cur.children[-1]
            index += 1


#     @staticmethod
#     def dfs(tree: Tree | Node, fn: Callable[Node]) -> None:
#         cur = getattr(tree, "root", tree)
#         queue = collections.deque([cur])
#         while queue:
#             node = queue.popleft()
#             fn(node)
#             for child in node.children:
#                 queue.appendleft(child)


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
        return line[:1] not in SEP

    result = []
    plevel = None
    data = []
    for line in txt.split("\n"):
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
        # tree.append(tree.root, key)
        def make_node(parent: None, key: Iterable):
            return Node(name=key[-1], kind="dir" if key[-1].endswith("/") else "file")

        trees.append(tree.root, key, "name", make_node)
    return tree


def main():
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
