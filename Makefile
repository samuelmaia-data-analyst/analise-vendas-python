.PHONY: setup lint type linkcheck test test-cov quality run precommit release-check release-bump-patch changelog-check

setup:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check .

type:
	mypy src

linkcheck:
	python scripts/check_markdown_links.py

release-check:
	python scripts/check_version_sync.py

changelog-check:
	python scripts/check_changelog.py

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=term-missing --cov-fail-under=80

quality: lint type linkcheck release-check changelog-check test

run:
	streamlit run app.py

run-cli:
	sales-analytics growth --period M

build-artifacts:
	sales-analytics build-artifacts

release-bump-patch:
	python scripts/bump_version.py --part patch

precommit:
	pre-commit run --all-files
