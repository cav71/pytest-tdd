from __future__ import annotations
import dataclasses as dc
from pathlib import Path
from typing import Callable, Generator, TYPE_CHECKING

import pytest


if TYPE_CHECKING:
    from _pytest.fixtures import SubRequest
    from pytest_print import PrettyPrinterFactory, PrettyPrinter


@pytest.fixture(scope="function")
def mktree(tmp_path: Path) -> Callable[[str, str|None, str], Path]:
    def create(txt: str, mode: str | None =None, subpath: str="") -> Path:
        mode = mode or ("tree" if "─ " in txt else "txt" )
        if mode == "tree":
            from pytest_tdd import tree
            if root := tree.parse(txt):
                tree.write(tmp_path / subpath, root)
        else:
            for path in [f for f in txt.split("\n") if f.strip()]:
                dst = Path(tmp_path) / subpath / path.strip()
                if path.strip().startswith("#"):
                    continue
                elif path.strip().endswith("/"):
                    dst.mkdir(exist_ok=True, parents=True)
                else:
                    dst.parent.mkdir(exist_ok=True, parents=True)
                    dst.write_text("")
        return tmp_path / subpath
    return create


@dc.dataclass
class Resolver:
    root: Path
    name: str

    def resolve(self, path: Path|str) -> Path:
        candidates = [
            self.root / self.name / path,
            self.root / path,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"cannot find {path}", candidates)


@pytest.fixture(scope="function")
def resolver(request: SubRequest) -> Generator[Resolver]:
    yield Resolver(
        Path(__file__).parent / "data",
        request.module.__name__)


@pytest.fixture(scope="session")
def pretty(create_pretty_printer: PrettyPrinterFactory) -> Callable[[str], _GeneratorContextManager[None, None, None]]:
    from pytest_print import Formatter
    from contextlib import contextmanager
    formatter = Formatter(indentation="  ", head=" ", space=" ", icon="⏩", timer_fmt="[{elapsed:.20f}]")

    printer = create_pretty_printer(formatter=formatter)

    @contextmanager
    def message(msg: str) -> Generator[None, None, None]:
        printer(msg)
        yield

    return message
