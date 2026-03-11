# Conventions

## Code Style & Patterns

- **Strings:** Double quotes everywhere (enforced by ruff)
- **Imports:** Group in order: stdlib, third-party (Django, Wagtail), local — separated by blank lines
- **Class naming:** CamelCase for classes, snake_case for functions/variables/modules
- **Views:** Use Wagtail ViewSets (`wagtail.admin.viewsets`) for admin pages — no legacy `ModelAdmin`
- **Admin integration:** Use `register_admin_viewset` hook, Wagtail 7.0 patterns only
- **Models:** Use `BigAutoField` as default auto field, descriptive `class Meta` with `verbose_name`/`verbose_name_plural`
- **URLs:** Use `path()` not `re_path()`, use `app_name` namespacing

## Testing Conventions

- **Root-level `tests/` package** split by feature area (not inside the distributable package)
- **Base class:** `django.test.TestCase` (or `wagtail.test.utils.WagtailTestUtils` mixin when testing admin views)
- **Test naming:** `test_<what_it_does>` — descriptive, not just `test_1`, `test_2`
- **Test class naming:** `Test<Feature>` (e.g., `TestURLDiscovery`, `TestAdminViews`)
- **Use Django test client** for view tests, not external HTTP libraries
- **Factories/fixtures:** Use Django's `setUp()` method, not pytest fixtures
- **tox:** Use `make tox` (or `uv run tox`) to run tests across all Python/Django/Wagtail versions; matrix defined in `tox.ini`

## Project Structure

- **Package (`wagtail_unveil/`):** All reusable code — must not import from `sandbox`
- **Sandbox (`sandbox/`):** Development/testing site — can import from `wagtail_unveil`
- **No new top-level apps** unless explicitly discussed
- **Templates:** Package templates go in `wagtail_unveil/templates/wagtail_unveil/`
- **Static files:** Package statics go in `wagtail_unveil/static/wagtail_unveil/`
- **Keep files focused:** One concern per module (don't stuff everything into models.py)

## Documentation

- **Pre-commit hooks** are configured in `.pre-commit-config.yaml` — run `make pre-commit` to check all files, or `uv run pre-commit install` to enable automatic checks on each commit
- **After each piece of work**, run lint and coverage checks (see the workflow in root AGENTS.md), then update the relevant AGENTS.md files and README.md to reflect new features, files, or changes
- **Docs sync checklist:** if `Makefile` targets or command behavior changes, update command docs in `AGENTS.md` and `docs/contributing/development.md`, then run `make docs-check`
- **README.md** is user-facing documentation — document features, usage, and configuration
- **AGENTS.md files** are the canonical agent context files — document key files, structure, and conventions
