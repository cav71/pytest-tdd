from __future__ import annotations
from pathlib import Path


def indent(txt: str, pre: str = " " * 2) -> str:
    "simple text indentation"

    from textwrap import dedent

    txt = dedent(txt)
    if txt.endswith("\n"):
        last_eol = "\n"
        txt = txt[:-1]
    else:
        last_eol = ""

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
        txt = txt[len(right) :] if txt.endswith(right) else txt
    return txt


def strip(txt: str, sub: str | list[str]) -> str:
    return lstrip(rstrip(txt, sub), sub)


def loadmod(path: Path) -> Any:
    from importlib.util import module_from_spec, spec_from_file_location

    module = None
    spec = spec_from_file_location(Path(path).name, Path(path))
    if spec:
        module = module_from_spec(spec)
    if module and spec and spec.loader:
        spec.loader.exec_module(module)
    return module
