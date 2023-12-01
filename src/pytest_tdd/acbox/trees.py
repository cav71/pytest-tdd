from __future__ import annotations

import collections
import dataclasses as dc
from typing import Callable, Iterable


@dc.dataclass
class Node:
    _: dc.KW_ONLY
    children: list[Node | None] = dc.field(default_factory=list)
    parent: Node | None = None

    @property
    def left(self):
        return self.children[0] if self.children else None

    @left.setter
    def left(self, node: Node):
        if len(self.children) == 0:
            self.children.append(node)
        else:
            self.children[0] = node

    @property
    def right(self):
        return self.children[1] if len(self.children) > 1 else None

    @right.setter
    def right(self, node: Node):
        if len(self.children) == 0:
            self.children.append(None)
        if len(self.children) == 1:
            self.children.append(node)
        else:
            self.children[1] = node


N = Node


def append(
    root: Node,
    dest: list | tuple,
    indexer: str,
    make_node: Callable[
        [
            Node,
            Iterable,
        ],
        Node,
    ],
):
    """appends a new node
    Eg.
        def make_node(parent: None, key: Iterable):
            node = Node(name=key[-1])
            node.parent = parent
            return node
        append(root, ["a", "b", "c", ], "name", make_node)
    """
    cur = root
    level = 0
    n = len(dest)
    while level < n:
        for child in cur.children:
            if getattr(child, indexer) == dest[level]:
                cur = child  # type: ignore
                break
        else:
            node = make_node(cur, dest[: level + 1])
            cur.children.append(node)
            cur = cur.children[-1]  # type: ignore

        level += 1


def dfs(root: Node, fn: Callable[[Node], None]) -> None:
    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        fn(node)
        for child in node.children:
            queue.appendleft(child)  # type: ignore