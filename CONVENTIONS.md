# Conventions

## Code Style & Patterns

- **Strings:** Double quotes everywhere (enforced by ruff)
- **Imports:** Group in order: stdlib, third-party (Django, Wagtail), local — separated by blank lines
- **Module organization:** Prefer top-to-bottom ordering that follows a module's main public entrypoint or execution flow. Keep helpers close to the phase or responsibility that uses them, keep genuinely shared primitives near the top when reused across phases, keep the main public orchestrator/entrypoint after its supporting phases, and pair related public helpers with their diagnostics/accessors when that improves findability. Treat this as a default preference rather than a rigid rule for every simple file.
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
- **Canonical workflow docs:** use `docs/contributing/development.md` for contributor commands, validation loops, and CI-aligned day-to-day workflow; use `AGENTS.md` for agent-only repo workflow and context
- **After code changes in `wagtail_unveil/` or `tests/`**, run `make lint` and `make coverage`, then inspect coverage for touched files and add tests for newly introduced uncovered lines
- **Changelog:** for notable unreleased user-visible, contributor-visible, or maintainer-relevant work, add a concise note under `CHANGELOG.md` -> `## Unreleased` in the same PR
- **Docs maintenance:** update `README.md`, relevant `AGENTS.md` files, and canonical contributor docs when behavior, structure, or doc ownership changes
- **Docs sync checklist:** if `Makefile` targets or command behavior changes, update command docs in `docs/contributing/development.md` in the same PR; keep `AGENTS.md` doc-routing references accurate if the canonical sources change
- **README.md** is user-facing documentation — document features, usage, and configuration
- **AGENTS.md files** are the canonical agent context files — document repo orientation, key files, and agent workflow rather than full contributor command catalogs
