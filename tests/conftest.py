import io
import functools
from pathlib import Path
from unittest import mock

import pytest

@pytest.fixture(scope="function")
def help_wrapper():
    def _helper(fn):
        @functools.wraps(fn)
        def _fn(*args, **kwargs):
            class AbortHelp(Exception):
                pass

            try:
                buf = io.StringIO()
                name = getattr(fn, "__name__", fn.__class__.__name__)

                def callme(self, parser, namespace, values, option_string=None):
                    old_prog = parser.prog
                    internal = {
                        "_jb_pytest_runner.py",
                        "py.test",
                        "pytest",
                    }
                    if parser.prog in internal:
                        parser.prog = name
                    parser.print_help(buf)
                    parser.prog = old_prog
                    raise AbortHelp
                with mock.patch("argparse._HelpAction.__call__", new=callme):
                    fn(*args, **kwargs)
                    raise RuntimeError(f"{name} didn't call --help")
            except AbortHelp:
                return (
                    buf
                    .getvalue()
                    # py 3.7 -> 3.8 change
                    .replace("optional arguments:", "options:")
                )
        return _fn
    return _helper


@pytest.fixture(scope="function")
def test_tree():
    files = """
        package2/modF.py
        package2/__init__.py
        package2/subpackageD/modH.py
        package2/subpackageD/tests/test_modD.py
        package2/subpackageC/modG.py
        tests/test_modG.py
        tests/test_modD.py
        tests/package1/subpackageB/test_modC.py
        tests/package1/test_modA.py
        tests/subpackageC/test_modG.py
        src/package1/subpackageA/modC.py
        src/package1/subpackageA/__init__.py
        src/package1/__init__.py
        src/package1/modB.py
        src/package1/modA.py
        src/package1/subpackageB/tests/test_modD.py
        src/package1/subpackageB/__init__.py
        src/package1/subpackageB/modE.py
        src/package1/subpackageB/modD.py
"""

    def create(root):
        for path in [ f for f in files.split("\n") if f.strip()]:
            dst = Path(root) / path.strip()
            dst.parent.mkdir(exist_ok=True, parents=True)
            dst.write_text("")
    return create


if __name__ == "__main__":
    import sys
    test_tree.__wrapped__()(sys.argv[1])
