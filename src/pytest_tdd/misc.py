from __future__ import annotations

import contextlib
from typing import Any, IO, Generator
from pathlib import Path


def indent(txt: str, pre: str = " " * 2) -> str:
    "simple text indentation"

    from textwrap import dedent

    txt = dedent(txt)
    if txt.endswith("\n"):
        last_eol = "\n"
        txt = txt[:-1]
    else:
        last_eol = "\n"

    result = pre + txt.replace("\n", "\n" + pre) + last_eol
    return result if result.strip() else result.strip()


def list_of_paths(paths: str | Path | list[str | Path] | None) -> list[Path]:
    if not paths:
        return []
    return [Path(s) for s in ([paths] if isinstance(paths, (str, Path)) else paths)]


def lstrip(txt: str, ending: str | list[str]) -> str:
    endings = ending if isinstance(ending, list) else [ending]
    for left in endings:
        txt = txt[len(left) :] if txt.startswith(left) else txt
    return txt


def rstrip(txt: str, starting: str | list[str]) -> str:
    startings = starting if isinstance(starting, list) else [starting]
    for right in startings:
        txt = txt[: -len(right)] if txt.endswith(right) else txt
    return txt


def strip(txt: str, sub: str | list[str]) -> str:
    return lstrip(rstrip(txt, sub), sub)


def loadmod(path: Path, name: str | None = None) -> Any:
    from importlib.util import module_from_spec, spec_from_file_location

    module = None
    spec = spec_from_file_location(name or Path(path).name, Path(path))
    if spec:
        module = module_from_spec(spec)
    if module and spec and spec.loader:
        spec.loader.exec_module(module)
    return module


def get_doc(src: Path | IO, pre: str | None = None) -> str | None:
    from ast import parse, NodeVisitor, get_docstring

    class Visitor(NodeVisitor):
        def __init__(self):
            self.doc = None
            super().__init__()

        def visit_Module(self, node):
            assert self.doc is None, "module has two heads?"
            self.doc = get_docstring(node, clean=True)
            return super().generic_visit(node)

    root = parse(str(src.read_text() if hasattr(src, "read_text") else src))
    visitor = Visitor()
    visitor.visit(root)
    return (
        visitor.doc
        if visitor.doc is None
        else visitor.doc
        if pre is None
        else indent(visitor.doc, pre)
    )


@contextlib.contextmanager
def mkdir(path: Path | None = None) -> Generator[Path, None, None]:
    from tempfile import mkdtemp
    from shutil import rmtree
    from os import makedirs

    tmpdir = path or mkdtemp()
    try:
        makedirs(tmpdir, exist_ok=True)
        yield Path(tmpdir).absolute()
        if path:
            return
        rmtree(tmpdir, ignore_errors=True)
    except Exception as exc:
        raise RuntimeError("left temp dir untouched in %s", tmpdir) from exc
