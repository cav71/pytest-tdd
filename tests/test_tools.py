from pytest_tdd import tools


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

    found = tools.indent(txt[1:], "..")
    assert f"\n{found}" == expected

    found = tools.indent(txt[1:-1], "..")
    assert f"\n{found}" == expected


def test_list_of_paths():
    from pathlib import Path

    assert tools.list_of_paths([]) == []
    assert tools.list_of_paths("hello") == [Path("hello")]
    assert tools.list_of_paths(["hello", Path("world")]) == [
        Path("hello"),
        Path("world"),
    ]


def test_strisp():
    assert tools.lstrip("/a/b/c/d/e", "/a/b") == "/c/d/e"
    assert tools.rstrip("/a/b/c/d/e", "/d/e") == "/a/b/c"
    assert tools.strip("/a/b/c/d/e", [ "/a/b", "/d/e"]) == "/c"


def test_loadmod():
    mod = tools.loadmod(__file__)
    assert "test_loadmod" in dir(mod)
    assert mod.__name__ == "test_tools.py"

    mod = tools.loadmod(__file__, "xyz")
    assert "test_loadmod" in dir(mod)
    assert mod.__name__ == "xyz"
