PACKAGE=pytest_tdd


help:
	@echo "make tests"

build:
	rm -rf dist && python -m build .

.PHONY: tests
tests:
	PYTHONPATH=src py.test -vvs tests


.PHONY: coverage
coverage:
	PYTHONPATH=src py.test -vvs \
       --cov=$(PACKAGE) \
       --cov-report=html:build/coverage \
       --html=build/junit/junit.html --self-contained-html
