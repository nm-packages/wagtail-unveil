# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**wagtail-unveil** is a reusable Wagtail package that discovers all URLs (hardcoded and generated) in a Wagtail site — both frontend and backend (Wagtail admin) URLs. It provides admin listing pages where developers can inspect and test URLs, primarily to verify they return 200 OK rather than error codes. The package is intended for distribution via PyPI.

## Repository Structure

- `wagtail_unveil/` — The reusable package (installable from PyPI)
- `sandbox/` — An example Wagtail site with the package installed, used for development and testing
- `manage.py` — Uses `sandbox.settings.dev` by default

## Development Commands

```bash
# Install dependencies (uses uv)
uv sync

# Run the sandbox dev server
uv run python manage.py runserver

# Run migrations
uv run python manage.py migrate

# Create migrations for the package
uv run python manage.py makemigrations wagtail_unveil

# Run all tests
uv run python manage.py test

# Run tests for the package only
uv run python manage.py test wagtail_unveil

# Lint
uv run ruff check .

# Lint and fix
uv run ruff check --fix .
```

## Conventions

See [CONVENTIONS.md](CONVENTIONS.md) for all coding conventions. Follow these strictly.

## Tech Stack

- Python 3.11+, Wagtail 7.0, Django 5.2
- `uv` for dependency management (pyproject.toml + uv.lock)
- SQLite for local development
- Django test runner for tests, ruff for linting
