from __future__ import annotations

from pytest_tdd import misc


def test_indent():
    txt = """
    This is a simply
       indented text
      with some special
         formatting
"""
    expected = """
..This is a simply
..   indented text
..  with some special
..     formatting
"""

    found = misc.indent(txt[1:], "..")
    assert f"\n{found}" == expected

    found = misc.indent(txt[1:-1], "..")
    assert f"\n{found}" == expected


def test_list_of_paths():
    from pathlib import Path

    assert misc.list_of_paths([]) == []
    assert misc.list_of_paths("hello") == [Path("hello")]
    assert misc.list_of_paths(["hello", Path("world")]) == [
        Path("hello"),
        Path("world"),
    ]


def test_strisp():
    assert misc.lstrip("/a/b/c/d/e", "/a/b") == "/c/d/e"
    assert misc.rstrip("/a/b/c/d/e", "/d/e") == "/a/b/c"
    assert misc.strip("/a/b/c/d/e", ["/a/b", "/d/e"]) == "/c"


def test_loadmod():
    mod = misc.loadmod(__file__)
    assert "test_loadmod" in dir(mod)
    assert mod.__name__ == "test_misc.py"

    mod = misc.loadmod(__file__, "xyz")
    assert "test_loadmod" in dir(mod)
    assert mod.__name__ == "xyz"


def test_get_doc():
    txt = """
'''Hello world
multi lined
  comment
'''
def init():
    pass
"""
    assert misc.get_doc(txt) == """\
Hello world
multi lined
  comment
""".rstrip()

    assert misc.get_doc(txt, pre="..") == """\
..Hello world
..multi lined
..  comment
"""


def test_mkdir(tmp_path):
    # fake a dest dir
    with misc.mkdir(tmp_path / "testdir") as tdir:
        assert tdir.exists()
    assert tdir.exists()
    tdir.rmdir()

    with misc.mkdir() as tdir:
        assert tdir.exists()
    assert not tdir.exists()


def test_mkdir_failure(tmp_path):
    try:
        with misc.mkdir(tmp_path / "testdir") as tdir:
            assert tdir.exists()
            raise RuntimeError("failure")
    except Exception as e:
        assert e.args[1] == tdir
        assert tdir.exists()
        tdir.rmdir()
    assert not tdir.exists()
