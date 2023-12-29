from __future__ import annotations

import contextlib
from typing import Any, IO, Generator
from pathlib import Path


def indent(txt: str, pre: str = " " * 2) -> str:
    """
    Indent text.

    Args:
        txt (str): The text to be indented.
        pre (str, optional): The string used as the indentation prefix.

    Returns:
        str: The indented text.

    """

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
    """
    Args:
        paths: A string, a Path object, a list of strings or Path objects, or None.

    Returns:
        A list of Path objects.

    Notes:
        - If `paths` is None, an empty list is returned.
        - If `paths` is a single string or Path object,
          it is converted to a Path object and returned as a list.
        - If `paths` is a list of strings or Path objects,
          each element is converted to a Path object and returned
          as a list of Path objects.

    Examples:
        >>> list_of_paths(None)
        []

        >>> list_of_paths('file.txt')
        [Path('file.txt')]

        >>> list_of_paths(['/path1/file1.txt', '/path2/file2.txt'])
        [Path('/path1/file1.txt'), Path('/path2/file2.txt')]
    """
    if not paths:
        return []
    return [Path(s) for s in ([paths] if isinstance(paths, (str, Path)) else paths)]


def lstrip(txt: str, ending: str | list[str]) -> str:
    """
    Args:
        txt: A string that needs to be stripped.
        ending: Either a string or a list of strings
                that represent the possible endings to strip from
                the beginning of the txt string.

    Returns:
        A new string with the specified endings stripped
        from the beginning if found, or the original string if none of
        the specified endings match.

    Example:
        >>> lstrip("Hello World", "Hello")
        ' World'
        >>> lstrip("Hello World", "Hi")
        'Hello World'
        >>> lstrip("Hello World", ["Hello", "Hi"])
        ' World'
    """
    endings = ending if isinstance(ending, list) else [ending]
    for left in endings:
        txt = txt[len(left) :] if txt.startswith(left) else txt
    return txt


def rstrip(txt: str, starting: str | list[str]) -> str:
    """
    Args:
        txt (str): The input text to be stripped.
        starting (str | list[str]): A string or a list of strings
        representing the characters or sequences of characters to
        be removed from the right end of the text.

    Returns:
        str: The text with the specified characters or sequences
        of characters removed from the right end.

    Raises:
        None

    Example usage:
        >>> rstrip('Hello World!', '!')
        'Hello World'
        >>> rstrip('Python is great', ['is', 'at'])
        'Python is gre'
    """
    startings = starting if isinstance(starting, list) else [starting]
    for right in startings:
        txt = txt[: -len(right)] if txt.endswith(right) else txt
    return txt


def strip(txt: str, sub: str | list[str]) -> str:
    """
    Args:
        txt: A string value representing the input text to be stripped.
        sub: A string or a list of strings to be removed from the input text.

    Returns:
        A string value representing the input text after applying the strip operation.

    """
    return lstrip(rstrip(txt, sub), sub)


def loadmod(path: Path, name: str | None = None) -> Any:
    """
    Loads a module from path.

    Args:
        path: The path to the module file that needs to be loaded.
        name: The name of the module. If not provided,
              the name will be determined using the file name of the path.

    Returns:
        The loaded module object.

    """
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
def mkdir(path: Path | None = None, keep: bool = False) -> Generator[Path, None, None]:
    from tempfile import mkdtemp
    from shutil import rmtree
    from os import makedirs

    tmpdir = path or mkdtemp()
    try:
        makedirs(tmpdir, exist_ok=True)
        yield Path(tmpdir).absolute()
        if path:
            return
        if not keep:
            rmtree(tmpdir, ignore_errors=True)
    except Exception as exc:
        raise RuntimeError("left temp dir untouched in %s", tmpdir) from exc
