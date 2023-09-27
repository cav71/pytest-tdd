from __future__ import annotations

import argparse
import functools
import logging
import sys
from typing import Any, Callable, Protocol

from . import misc


class ErrorFn(Protocol):
    def __call__(self, message: str, explain: str | None, hint: str | None) -> None:
        ...


class AbortExecutionError(Exception):
    @staticmethod
    def _strip(txt):
        txt = txt or ""
        txt = txt[1:] if txt.startswith("\n") else txt
        txt = misc.indent(txt, pre="")
        return txt[:-1] if txt.endswith("\n") else txt

    def __init__(
        self,
        message: str,
        explain: str | None = None,
        hint: str | None = None,
        usage: str | None = None,
    ):
        self.message = message.strip()
        self.explain = explain
        self.hint = hint
        self.usage = usage

    def __str__(self):
        out = []
        if self.usage:
            out.extend(self.usage.strip().split("\n"))
        if self.message:
            out.extend(self._strip(self.message).split("\n"))
        if self.explain:
            out.append("reason:")
            out.extend(misc.indent(self.explain).split("\n"))
        if self.hint:
            out.append("hint:")
            out.extend(misc.indent(self.hint).split("\n"))
        return "\n".join((line.strip() if not line.strip() else line) for line in out)


def _indent(txt: str, pre: str = " " * 2) -> str:
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


def merge_kwargs(
    fn: Callable[[Any], Any], options: argparse.Namespace
) -> dict[str, Any]:
    from inspect import signature

    fn_kwargs = set(signature(fn).parameters)
    if fn_kwargs == {"options"}:
        return {"options": options}
    op_kwargs = set(options.__dict__)
    if missing := (fn_kwargs - op_kwargs):
        raise RuntimeError("missing arguments", missing)
    return {k: getattr(options, k) for k in op_kwargs & fn_kwargs}


def _add_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    """parses args from the command line

    Args:
        args: command line arguments or None to pull from sys.argv
        doc: text to use in cli description
    """
    parser.add_argument("-n", "--dry-run", dest="dryrun", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")


def _process_options(
    options: argparse.Namespace, errorfn: ErrorFn
) -> argparse.Namespace | None:
    logging.basicConfig(
        format="%(levelname)s:%(name)s:(dry-run) %(message)s"
        if options.dryrun
        else "%(levelname)s:%(name)s:%(message)s",
        level=logging.DEBUG if options.verbose else logging.INFO,
    )

    for d in [
        "verbose",
    ]:
        delattr(options, d)
    return options


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        class ParserFormatter(
            argparse.ArgumentDefaultsHelpFormatter,
            argparse.RawDescriptionHelpFormatter,
        ):
            pass

        description, epilog = "", ""
        if "doc" in kwargs:
            description, _, epilog = (kwargs.pop("doc") or "").partition("\n")
            epilog = _indent(epilog, pre="")
        description = kwargs.get("descriptions") or description
        epilog = kwargs.get("epilog") or epilog
        formatter_class = (
            kwargs.pop("formatter_class")
            if "formatter_class" in kwargs
            else ParserFormatter
        )

        super().__init__(
            formatter_class=formatter_class,
            description=description,
            epilog=epilog,
            **kwargs,
        )


def driver(
    add_arguments: Callable[[argparse.ArgumentParser], None] | None = None,
    process_options: Callable[[argparse.Namespace, ErrorFn], argparse.Namespace | None]
    | None = None,
    doc: str | None = None,
    match_call: bool = True,
    reraise: bool = False,
    **parser_kwargs,
):
    """decorator for cli scripts

    :argument add_arguments: callable (with parser ArgumentParser argument)
                        to add arguments
    :argument process_options: callable (with options Namespace and ErrorFn function)
                        to process options
    :argument reraise: reraise the internal exception instead exiting

    Example:
        def add_arguments(parser: argparse.ArgumentParser):
            parser.add_argument("-x")

        def process_options(options: argparse.Namespace, error: ErrorFn):
            pass

        @cli.driver(add_arguments, process_options)
        def main(options):
            pass

        if __name__ == "__main__":
            main()
    """

    @functools.wraps(driver)
    def _fn(main: Callable[[argparse.Namespace | Any], Any]):
        @functools.wraps(main)
        def _fn1(args: None | list[str] = None) -> Any:
            try:
                parser = ArgumentParser(doc=doc or main.__doc__, **parser_kwargs)
                _add_arguments(parser)
                if add_arguments:
                    add_arguments(parser)

                options = parser.parse_args(args=args)

                def error(
                    message: str,
                    explain: str = "",
                    hint: str = "",
                    usage: str | None = None,
                ):
                    raise AbortExecutionError(message, explain, hint, usage)

                errorfn: ErrorFn = functools.partial(error, usage=parser.format_usage())
                options.error = errorfn

                options = _process_options(options, errorfn) or options
                if process_options:
                    options = process_options(options, errorfn) or options

                kwargs = merge_kwargs(main, options)
                return main(**kwargs) if match_call else main(options)  # type: ignore
            except AbortExecutionError as err:
                if reraise:
                    raise err
                print(str(err), file=sys.stderr)  # noqa: T201
                raise SystemExit(2) from None
            except Exception:
                raise

        return _fn1

    return _fn


# class group:
#     def __init__(
#         self,
#         add_arguments: Callable[[argparse.ArgumentParser], None] | None = None,
#         process_options: Callable[
#             [argparse.Namespace, ErrorFn], argparse.Namespace | None
#         ]
#         | None = None,
#         **kwargs,
#     ):
#         self._add_arguments = add_arguments
#         self._process_options = process_options
#         self._postprocess : dict[str, Callable[
#             [argparse.Namespace, ErrorFn], argparse.Namespace | None
#         ]
#         | None ] = {}
#         self.parser = ArgumentParser(**kwargs)
#         self.subparsers = self.parser.add_subparsers()
#
#     def command(
#         self,
#         fn,
#         add_arguments: Callable[[argparse.ArgumentParser], None] | None = None,
#         process_options: Callable[
#             [argparse.Namespace, ErrorFn], argparse.Namespace | None
#         ]
#         | None = None,
#         name: str | None = None,
#     ):
#         name = name or fn.__name__
#         parser = self.subparsers.add_parser(name)
#         if self._add_arguments:
#             self._add_arguments(parser)
#         add_arguments(parser)
#         self._postprocess[name] = process_options
#
