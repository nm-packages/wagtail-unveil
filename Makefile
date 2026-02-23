UV = uv
RUN = $(UV) run --env-file .env
MANAGE = $(RUN) django-admin

.PHONY: help setup env install migrate superuser sample-data runserver run test lint lint-fix makemigrations clean

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  setup           Full dev setup: env, install, migrate, sample-data"
	@echo "  superuser       Create a superuser"
	@echo "  runserver       Start the sandbox dev server (alias: run)"
	@echo "  test            Run package tests"
	@echo "  lint            Run ruff check"
	@echo "  lint-fix        Run ruff check --fix"
	@echo "  makemigrations  Create package migrations"
	@echo "  sample-data     Create sample data"
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

lint:
	$(UV) run ruff check .

lint-fix:
	$(UV) run ruff check --fix .

makemigrations:
	$(MANAGE) makemigrations wagtail_unveil

clean:
	rm -f db.sqlite3 .env
	rm -rf media
