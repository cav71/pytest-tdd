from pytest_tdd import tree as ptree


def test_generate(tmp_path):
    found = ptree.generate(tmp_path, """
my-project/
├── src/
│   └── my_package/
│       └── module1.py
└── tests/
    └── test_module1.py

""")
    assert set(found) == {
"src/",
"src/my_package/",
"src/my_package/module1.py",
"src/tests/",
"src/tests/test_module1.py",
}
