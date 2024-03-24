clean:
	rm -rf .ruff_cache .pytest_cache

format:
	poetry run ruff check --select I --fix
	poetry run ruff format

lint: ruff-check pyright

lint-fix: ruff-fix

lint-test: lint test

pyright:
	poetry run pyright

ruff-check:
	poetry run ruff check

ruff-fix:
	poetry run ruff check --fix

test:
	poetry run pytest
