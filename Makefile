.PHONY: setup check sample test lint

setup:
	./scripts/setup.sh

check:
	./scripts/run.sh check

sample:
	./scripts/run.sh sample --software "BOM" --candidate "BOM Helper Service"

test:
	./scripts/test.sh

lint:
	.venv/bin/ruff check src tests
	.venv/bin/mypy src
