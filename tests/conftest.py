from pathlib import Path

import pytest

@pytest.fixture(scope="function")
def mktree(tmp_path):
    def create(txt, subpath=""):
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
        for path in [f for f in files.split("\n") if f.strip()]:
            dst = Path(root) / path.strip()
            dst.parent.mkdir(exist_ok=True, parents=True)
            dst.write_text("")
    return create


if __name__ == "__main__":
    import sys
    test_tree.__wrapped__()(sys.argv[1])
