from pytest_tdd import misc


def test_get_doc():
    from ast import parse
    txt = """
'''Hello world
multi lined
  comment
'''
def init():
    pass
"""
    assert misc.get_doc(parse(txt)) == """\
Hello world
multi lined
  comment
""".rstrip()

    assert misc.get_doc(parse(txt), pre="..") == """\
..Hello world
..multi lined
..  comment
"""


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
    assert misc.strip("/a/b/c/d/e", [ "/a/b", "/d/e"]) == "/c"


def test_loadmod():
    mod = misc.loadmod(__file__)
    assert "test_loadmod" in dir(mod)
    assert mod.__name__ == "test_misc.py"

    mod = misc.loadmod(__file__, "xyz")
    assert "test_loadmod" in dir(mod)
    assert mod.__name__ == "xyz"

