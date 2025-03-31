.PHONY: lint
lint:
	 poetry run mypy \
		--check-untyped-defs \
		src/minimux

.PHONY: format
format:
	poetry run isort \
		--tc \
		--profile=black \
		src/minimux
	poetry run black \
		src/minimux
