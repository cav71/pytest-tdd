help:
	@echo "make build"

build:
	rm -rf dist && python -m build -n .
