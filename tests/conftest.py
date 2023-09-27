import io
import functools
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
                def callme(self, parser, namespace, values, option_string=None):
                    old_prog = parser.prog
                    internal = {
                        "_jb_pytest_runner.py",
                        "py.test",
                    }
                    if parser.prog in internal:
                        parser.prog = fn.__name__
                    parser.print_help(buf)
                    parser.prog = old_prog
                    raise AbortHelp
                with mock.patch("argparse._HelpAction.__call__", new=callme):
                    fn(*args, **kwargs)
                    raise RuntimeError(f"{fn.__name__} didn't call --help")
            except AbortHelp:
                return (
                    buf
                    .getvalue()
                    # py 3.7 -> 3.8 change
                    .replace("optional arguments:", "options:")
                )
        return _fn
    return _helper