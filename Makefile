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

.PHONY: formatcheck
formatcheck:
	poetry run isort \
		--tc \
		--profile black \
		--check-only \
		src/minimux
	poetry run black \
		--check \
		src/minimux

.PHONY: test
test:
	poetry run pytest \
		tests
