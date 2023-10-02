from pathlib import Path

from pytest_tdd import __main__ as mod


def test_help(help_wrapper):
    Path(__file__).parent.parent

    assert (help_wrapper(mod.main)(["--help"]) == """\
usage: main [-h] [-n] [-v] [-t TESTS_DIR] [-s SOURCES_DIR] source

given a python module execute related tests.

positional arguments:
  source                source to run tests for

options:
  -h, --help            show this help message and exit
  -n, --dry-run
  -v, --verbose
  -t TESTS_DIR, --tests-dir TESTS_DIR
                        root of tests (default: tests)
  -s SOURCES_DIR, --sources-dir SOURCES_DIR
                        root of sources (default: src)

Example:
    $> pytest-tdd \\
         --src src --tests tests \\
         src/mylibrary/mysubdir/hello.py
    or (the default)
    $> pytest-tdd src/mylibrary/mysubdir/hello.py

    This will look up (and run if found) the following tests:
    - tests/mylibrary/subdir/test_hello.py
    - tests/test_hello.py
""")


