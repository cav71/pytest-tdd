from pathlib import Path


def generate_fs_tree(destdir: Path, txt: str):
    from pytest_tdd.tree import parse

    tree = parse(txt)
    tree.root.name = str(destdir.expanduser().resolve()) + "/"  # type: ignore
    tree.generate(dryrun=False)  # type: ignore
