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

## Refactoring While Changing Code

- **Refactor nearby touched code:** When a feature, bug fix, or review-driven change touches an area that has obvious local duplication, unnecessary indirection, or newly exposed complexity, simplify it in the same patch when the refactor is behavior-preserving and low risk.
- **Prefer simpler extensions to layered helpers:** When extending existing logic, prefer the clearest implementation that fits the current need rather than adding tiny one-use helpers, parallel branches, or extra abstraction layers that make the touched flow harder to follow.
- **Do not widen scope for speculative cleanup:** Keep opportunistic refactors local to the code already being changed. Do not turn a scoped fix into broader cleanup, module reshuffling, or unrelated architectural work unless that larger change is required for correctness, testability, or clarity of the touched behavior.
- **Remove duplication introduced by the current change:** If the new work creates obvious repeated setup, repeated branching, or repeated parsing/resolution logic, clean that duplication up before finalizing the patch when doing so does not materially increase risk.
- **Call out deferred refactors:** If a useful refactor is noticed but intentionally left out to preserve scope, mention that explicitly in the final handoff or PR discussion instead of silently leaving the opportunity undocumented.

Good fit examples:

- extracting repeated test setup into a small helper when several new tests need the same manifest or page fixture arrangement
- combining or refactoring tests when new coverage introduces obvious duplicated setup, assertions, or scenario scaffolding without making the resulting test intent harder to read
- collapsing a tiny one-use helper or branch added during the change when it adds indirection without improving readability
- simplifying touched parsing, discovery, or resolution logic when the new requirement reveals duplicated or over-factored control flow

Not a good fit examples:

- reorganizing multiple modules during a narrow bug fix when the existing file layout is not blocking the change
- renaming broad internal APIs or moving symbols across subsystems purely for taste while implementing a scoped behavior change
- turning a local readability cleanup into a wider refactor that changes unrelated code paths or expands test surface without a concrete need

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
- **Changelog:** every pull request must add or update a concise note under `CHANGELOG.md` -> `## Unreleased`, and that changelog change must ship in the same PR as the related work
- **Docs maintenance:** update `README.md`, relevant `AGENTS.md` files, and canonical contributor docs when behavior, structure, or doc ownership changes
- **Docs sync checklist:** if `Makefile` targets or command behavior changes, update command docs in `docs/contributing/development.md` in the same PR; keep `AGENTS.md` doc-routing references accurate if the canonical sources change
- **README.md** is user-facing documentation — document features, usage, and configuration
- **AGENTS.md files** are the canonical agent context files — document repo orientation, key files, and agent workflow rather than full contributor command catalogs
