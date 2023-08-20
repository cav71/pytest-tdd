import argparse
import contextlib
from unittest import mock

import pytest
from pytest_tdd import cli


def test_exception():
    obj = cli.AbortExecutionError(
        message="this is a short one-liner",
        explain="""
          It looks the repository doesn't have any branch,
          you should:
            git checkout --orphan <branch-name>
          """,
        hint="create a git branch",
    )
    assert (
        str(obj)
        == """\
this is a short one-liner
reason:

  It looks the repository doesn't have any branch,
  you should:
    git checkout --orphan <branch-name>

hint:
  create a git branch
"""
    )


def test_docstring():
    @cli.cli()
    def hello(options):
        "this is a docstring"
        pass

    assert hello.__doc__ == "this is a docstring"


def test_cli_call_help():

    class JumpOut(Exception):
        pass

    def add_argument(parser: argparse.ArgumentParser):
        parser.add_argument("-f", type=float)
        parser.add_argument("value", type=float)

    def process_options(options: argparse.Namespace, error: cli.ErrorFn):
        options.value *= options.f
    
    @cli.cli(add_argument, process_options)
    def hello(options):
        return options.value

    with contextlib.ExitStack() as stack:

        def xxx(self, parser, namespace, values, option_string=None):
            found = (
                parser.format_help()
                .strip()
                .replace(" py.test ", " pytest ")
                .replace("optional arguments:", "options:")
            )
            assert (
                found
                == """
usage: pytest [-h] [-n] [-v] [-f F] value

positional arguments:
  value

options:
  -h, --help     show this help message and exit
  -n, --dry-run
  -v, --verbose
  -f F
""".strip()
            )
            raise JumpOut("get out")

        stack.enter_context(mock.patch("argparse._HelpAction.__call__", new=xxx))
        pytest.raises(JumpOut, hello, ["--help",])
        assert hello(["-f", "2", "123"]) == 246
