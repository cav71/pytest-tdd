
# pytest-tdd

### Description
`pytest-tdd` is a cli tool to discover and run tests related to a module.

In a project with a standard layout:
```
my-project/
├── src/
│   └── my_package/
│       └── module1.py
└── tests/
    └── test_module1.py
```

This command will run `test_module1.py` using `pytest`:
```bash

$> pytest-tdd -v src/my_package/module1.py

module1.py run 1 tests with 0 failures and 0 errors, covered 115 lines out of 167 (68.86%, missing=52 lines)
```

> **NOTE 1** You can pass a `-t|--threshold 70` to mark a failure if the overage is less than 70%.

> **NOTE 2** You can use the `-t|--tests-dir` to point to a different **tests** directory and `-s|--sources-dir` to point to a different **src** directory.

### pre-commit integration
pytest-tdd can be integrate as part of a commit,

[//]: # (edited using https://jbt.github.io/markdown-editor)
