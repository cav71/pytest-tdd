import argparse

import pytest
from pytest_tdd import cli


def test_merge_kwargs():
    def fn(x, y=2):
        pass
    options = argparse.Namespace(x=1, z=3)

    # missing y
    pytest.raises(cli.InternalCliError, cli.merge_kwargs, fn, options)

    options.y = 99
    assert cli.merge_kwargs(fn, options) == { "x": 1, "y": 99}


@pytest.fixture(scope="function")
def single_command_cli():
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument("-f", type=float)
        parser.add_argument("value", type=float)
        parser.add_argument("--abort")
        parser.add_argument("--except", dest="except_")

    def process_options(options: argparse.Namespace, error: cli.ErrorFn):
        options.value *= options.f

    @cli.driver(add_arguments, process_options, reraise=True)
    def hello(options):
        """an hello world example

        With an extensive help message and multiline
         text with indentation
            and complex shape
        """
        if options.except_:
            raise cli.AbortExecutionError(f"aborted with {options.except_=}")
        if options.abort:
            options.error(f"aborted with {options.abort=}")
        return options.value
    return hello


@pytest.fixture(scope="function")
def multi_command_cli():

    # common arguments to all commands
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument("-f", type=float)
        parser.add_argument("value", type=float)
        parser.add_argument("--abort")
        parser.add_argument("--except", dest="except_")

    def process_options(options: argparse.Namespace, error: cli.ErrorFn):
        options.value *= options.f

    return
    group = cli.MulticommandDriver(add_arguments, process_options)


    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument("--hello-x")

    def process_options(options: argparse.Namespace, error: cli.ErrorFn):
        pass

    @group.command(add_arguments, process_options)
    def hello(options):
        pass


    @group.command()
    def world(options):
        pass


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
    @cli.driver()
    def hello(options):
        "this is a docstring"
        pass

    assert hello.__doc__ == "this is a docstring"


def test_single_command_cli_help(help_wrapper, single_command_cli):
    assert help_wrapper(single_command_cli)(["--help"]) == """\
usage: hello [-h] [-n] [-v] [-f F] [--abort ABORT] [--except EXCEPT_] value

an hello world example

positional arguments:
  value

options:
  -h, --help        show this help message and exit
  -n, --dry-run
  -v, --verbose
  -f F
  --abort ABORT
  --except EXCEPT_

With an extensive help message and multiline
 text with indentation
    and complex shape
"""

def test_single_command_cli_calls(single_command_cli):

    assert single_command_cli(["12", "-f", "4"]) == 48

    # test internal handled exceptions
    pytest.raises(cli.AbortExecutionError,
                  single_command_cli, ["12", "-f", "4", "--except", "bye!"])
    pytest.raises(cli.AbortExecutionError,
                  single_command_cli, ["12", "-f", "4", "--abort", "bye!"])

    # a non internal exception
    pytest.raises(TypeError,
                  single_command_cli, ["12",])


def test_multi_command_cli_help(help_wrapper, multi_command_cli):
    pass
