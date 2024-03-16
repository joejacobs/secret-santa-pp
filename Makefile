lint-check:
	poetry run ruff check

lint-fix:
	poetry run ruff check --fix

format:
	poetry run ruff format

test:
	poetry run pytest --cov=secret_santa_pp
