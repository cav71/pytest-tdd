import logging
from pathlib import Path
from qualitor import api, cli


log = logging.getLogger(__name__)


def parse_args(args=None):
    parser = cli.ArgumentParser(doc=__doc__)

    parser.add_argument("source", type=Path, help="source to run tests for")
    parser.add_argument("-t", "--test-dir", default=Path.cwd() / "tests", type=Path, help="root of tests")
    
    options = parser.parse_args(args)
    logging.basicConfig(level=logging.INFO)

    return options.__dict__


def find_test(source:Path, test_dir:Path):
    candidates = [
        test_dir / f"test_{source.name}"
    ]
    found = [ c for c in candidates if c.exists() ]
    return found[0]


def main(source:Path, test_dir:Path):
    log.info("source file: %s", source)

    tfile = find_test(source, test_dir)
    log.info("found test in: %s", tfile)

    from pytest import main
    main(["-vvs", tfile])


if __name__ == "__main__":
    main(**parse_args())
