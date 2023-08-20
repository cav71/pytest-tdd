help:
	@echo "make tests"

build:
	rm -rf dist && python -m build .

.PHONY: tests
tests:
	PYTHONPATH=src py.test -vvs tests
