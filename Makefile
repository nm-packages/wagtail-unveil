UV = uv
RUN = $(UV) run --env-file .env
MANAGE = $(RUN) django-admin

.PHONY: help setup env install migrate superuser sample-data runserver run test test-js build-js tox lint lint-fix lint-js lint-js-fix makemigrations pre-commit coverage coverage-html clean

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  setup           Full dev setup: env, install, migrate, sample-data"
	@echo "  superuser       Create a superuser"
	@echo "  runserver       Start the sandbox dev server (alias: run)"
	@echo "  test            Run package tests"
	@echo "  test-js         Run JavaScript report tests"
	@echo "  build-js        Build report JavaScript bundle assets"
	@echo "  tox             Run tests across all Python/Django/Wagtail versions"
	@echo "  lint            Run ruff check"
	@echo "  lint-fix        Run ruff check --fix"
	@echo "  lint-js         Run Biome JavaScript checks"
	@echo "  lint-js-fix     Run Biome JavaScript checks with --write"
	@echo "  pre-commit      Run pre-commit hooks on all files"
	@echo "  makemigrations  Create package migrations"
	@echo "  sample-data     Create sample data"
	@echo "  coverage        Run tests with coverage and show terminal report"
	@echo "  coverage-html   Generate HTML coverage report and open it"
	@echo "  clean           Remove db.sqlite3, .env, and media"

setup: env install migrate sample-data

env:
	cp -n .env.example .env || true

install:
	$(UV) sync

migrate:
	$(MANAGE) migrate

superuser:
	$(MANAGE) createsuperuser

sample-data:
	$(MANAGE) create_sample_data

runserver:
	$(MANAGE) runserver

run: runserver

test:
	$(MANAGE) test tests

test-js:
	npm run test:js

build-js:
	npm run build:js

tox:
	$(UV) run tox

lint:
	$(UV) run ruff check .

lint-fix:
	$(UV) run ruff check --fix .

lint-js:
	npm run lint:js

lint-js-fix:
	npm run lint:js:fix

pre-commit:
	$(UV) run pre-commit run --all-files

makemigrations:
	$(MANAGE) makemigrations wagtail_unveil

coverage:
	$(RUN) coverage run -m django test tests
	$(RUN) coverage report

coverage-html: coverage
	$(RUN) coverage html
	open htmlcov/index.html

clean:
	rm -f db.sqlite3 .env
	rm -rf media
