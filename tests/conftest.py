from __future__ import annotations
import dataclasses as dc
from pathlib import Path

import pytest

@pytest.fixture(scope="function")
def mktree(tmp_path):
    def create(txt, mode=None, subpath=""):
        mode = mode or ("tree" if "─ " in txt else "txt" )
        if mode == "tree":
            from pytest_tdd import tree
            tree.write(tmp_path / subpath, tree.parse(txt))
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


@pytest.fixture(scope="function")
def resolver(request):
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

    yield Resolver(
        Path(__file__).parent / "data",
        request.module.__name__)


@pytest.fixture(scope="session")
def pretty(create_pretty_printer: PrettyPrinterFactory) -> PrettyPrinter:
    from pytest_print import Formatter
    from contextlib import contextmanager
    formatter = Formatter(indentation="  ", head=" ", space=" ", icon="⏩", timer_fmt="[{elapsed:.20f}]")

    printer = create_pretty_printer(formatter=formatter)

    @contextmanager
    def message(msg):
        printer(msg)
        yield
   
    return message
