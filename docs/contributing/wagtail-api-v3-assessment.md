# Wagtail API v3 and URL discovery

This assessment uses Wagtail 8.0 and the sandbox's `/api/v3/` mount. It answers whether v3 can simplify `wagtail-unveil`'s frontend and admin URL discovery and GET testing. The [discovery architecture](discovery-architecture.md) remains the reference for current behavior.

## Conclusion

Wagtail API v3 can improve discovery **of v3 API operations**. Its OpenAPI schema declares paths, methods, required path and query parameters, and authentication. It cannot replace the resolver walk, page lookup, or admin instance resolution that serve the package's wider purpose. Using the schema as the general discovery source would add a second discovery system while omitting project URLs, page routes, routable subpages, and Wagtail admin views.

The useful next change is a narrow frontend fix: classify v3 operations by method, required parameters, and authentication, and select representative IDs for GET detail operations where safe. Keep Django's resolver as the inventory for the rest of the site. Do not use v3 write operations as substitutes for testing admin views: they have different URLs and behavior, and writes can change content.

## Evidence from the sandbox

With Wagtail 8.0 and the existing sandbox database, `/api/v3/openapi.json` returned OpenAPI 3.1 with **35 paths**. `get_frontend_urls()` emitted **56 v3 rows**, of which **17** were marked testable. The row count differs because Django Ninja registers separate callbacks for several operations on one path.

| Current row | Current result | What v3 declares or returns |
| --- | --- | --- |
| `/api/v3/pages/` with `create_page` | Testable | `create_page` is POST. The report's GET receives the page list's 200 response. |
| `/api/v3/pages/find/` with `find_page` | Testable | GET needs a useful `id` or `html_path`; a bare GET returned 404. |
| `/api/v3/schema/` with `list_schemas` | Testable | GET requires a v3 bearer token; the report's session-based GET returned 401. |
| `/api/v3/` with `api-root` | Testable | The mounted root has no GET operation; a GET returned 404. |
| `/api/v3/pages/<page_id>/` with `detail_page` | Untestable, unresolved parameter | The sandbox has a public page with ID 3, and v3 exposes a GET detail operation. |
| `/api/v3/snippets/<type>/<pk>/` | Untestable, unresolved parameters | The path needs a model type and instance ID; snippet reads also require a v3 bearer token. |

The callback metadata used by the v2-specific helpers in `frontend_resolution.py` (`cls` and `actions`) is absent on the v3 Django Ninja callbacks. The current v2 `find` recognition and detail ID resolution therefore do not apply to v3. The frontend report currently sends a credentialed **GET** for every testable row; it does not send a v3 API bearer token.

The admin discovery pipeline yielded **338 rows** in the same run. V3's OpenAPI paths all live under `/api/v3/`; they do not describe `/admin/` viewsets, chooser URLs, settings edit routes, or third-party admin packages. V3's CMS actions overlap with some admin tasks, but exercising an API action would test a different endpoint and may mutate content.

These counts describe the sandbox at the time of investigation, not a fixed package contract. Reproduce them by inspecting the mounted `/api/v3/openapi.json` and the output of `get_frontend_urls()` and `get_admin_urls()` in `sandbox.settings`.

## Dynamic tests with Django `TestCase`

The reports' Test buttons make GET requests and display the status codes. A Django `TestCase` can make the same in-process requests through `self.client` without going through `wagtail-unveil`'s report or JSON views. The test should call `get_admin_urls()` and `get_frontend_urls()` **after the test database is ready**, so its cases follow the routes and objects available there. A fixed list of sandbox URLs would miss project-specific admin viewsets and frontend routes.

In the current sandbox database, discovery marked **268 of 338 admin rows (79%)** and **55 of 131 frontend rows (42%)** as testable. The latter 55 rows correspond to **50 distinct request paths** because several v3 operation rows share a path. These are candidate counts for a dynamic GET sweep, not the number of successful or meaningfully checked endpoints. `TestCase` starts with an isolated test database, so its counts depend on the fixtures it creates; the sandbox's sample data is not automatically present.

A useful dynamic test would:

1. Use the host project's test database and create a superuser for admin GETs. Run discovery after any project-provided test fixtures are loaded; do not require the package to know the project's page and snippet models.
2. Iterate rows marked `is_testable`, using `resolved_route or route` for admin paths and `resolved_url or url` plus `query_params` for frontend paths. Use `subTest` with the route name and concrete path so failures identify the endpoint. Deduplicate identical requests while retaining the associated row names for diagnostics.
3. Use `self.client.force_login(superuser)` for admin requests and an anonymous client for public frontend requests. Set the request host to match the Wagtail `Site`; check protected routes separately with the credentials they actually require. A v3 bearer token is distinct from a superuser session.
4. Assert a route-specific expected result. A blanket `2xx` assertion would misclassify intended redirects, permission responses, and the sandbox's deliberate `/intentional-error/` route. It would also accept the `create_page` false positive described above if it only checked the GET status at that shared path. Test operation identity and expected status, not just whether some GET on the path returned 200.

This can replace the **request execution** part of the reports for CI checks and avoid maintaining a second list of endpoints. It does not remove the discovery and parameter-resolution code: those functions supply the dynamic cases. It also does not exercise the reports' JavaScript, browser cookies, or a deployed site. The report views remain useful for inspecting the current site's URLs interactively; a `TestCase` checks only the isolated test site's state. Django's [test client documentation](https://docs.djangoproject.com/en/5.2/topics/testing/tools/) describes its in-process requests and browser limitations.

### Wagtail 7 comparison from `main`

The same dynamic-test design works on `main`: its lockfile selects Wagtail **7.3.1**, and its discovery functions expose the same `is_testable`, `resolved_route`, and `resolved_url` fields. Its sandbox mounts API v2 and has no API v3 dependency. The test can discover cases at runtime on Wagtail 7 without an OpenAPI schema.

The table uses fresh, isolated test databases for both branches. “Sample data” means running the sandbox's `create_sample_data` command after the database migrations. Counts are **discovered rows / rows currently marked testable**, not code coverage or proven successful responses.

| Branch and fixtures | Admin rows / GET candidates | Frontend rows / GET candidates |
| --- | ---: | ---: |
| `main`, Wagtail 7.3.1, default test data | 280 / 163 (58%) | 65 / 27 (42%) |
| `main`, Wagtail 7.3.1, sample data | 328 / 278 (85%) | 75 / 38 (51%) |
| Investigation branch, Wagtail 8.0, sample data | 338 / 268 (79%) | 131 / 55 (42%) |

On Wagtail 7 with sample data, a direct GET pass over the **278 distinct admin targets**, using a superuser test client, returned **266 HTTP 200** and **12 HTTP 302**. The redirects led to other admin pages, such as page history or an add-page form. The **38 distinct frontend targets**, using an anonymous client, returned **20 HTTP 200**, **17 HTTP 302**, and **one HTTP 500**. Sixteen redirects led to Django admin login; the logout route redirected to the Django admin root. The 500 was the sandbox's deliberate `/intentional-error/` endpoint. A separate authenticated pass over the 18 Django admin paths marked testable returned 15 responses of 200, plus one login redirect, one 405 for logout, and one 403 for autocomplete without its required parameters.

These results show what a dynamic smoke test could request, while also showing why response expectations need to depend on authentication, method, parameters, and route purpose. For Wagtail 7, representative fixtures raised the admin candidate count from 163 to 278 by resolving more parameterized URLs. The remaining 50 admin and 37 frontend rows in the sample-data run would need more compatible objects, query inputs, method-specific requests, or explicit skip handling. A GET sweep measures route availability and response behavior; it does not measure Python line coverage or verify that an edit, chooser, form, or API operation works correctly.

### What an installable package can supply

The percentages above come from the sandbox URLconf; they are **not coverage promises for an arbitrary Wagtail site**. Even the “default test data” run still includes sandbox-specific URL patterns and model definitions. A fresh installed project may have a different home page model, custom required fields, private pages, optional Wagtail apps, and third-party admin views.

A package-provided smoke test can be dynamic without generating project content:

- Discover the installed project's routes and use a superuser created only in the isolated test database for admin GETs.
- Request concrete, GET-safe paths; report how many discovered rows were exercised and why other rows were skipped. Treat login redirects, expected errors, and duplicate operation names explicitly so a green result means the intended endpoint was reached.
- Let the project's own tests or an optional setup callback create representative pages, snippets, settings, and media **before** discovery when broader coverage is wanted.

The package cannot reliably create an instance of every unknown page or snippet model from field introspection alone. A page may require a compatible parent, non-null custom fields, related objects, StreamField content, or custom save behavior. Wagtail's [testing guide](https://docs.wagtail.org/en/stable/advanced_topics/testing.html) shows that pages are added through the tree and that project tests supply type-specific content. Generic fixture generation would introduce a large, fragile subsystem while still skipping many real routes.

The simplest delivery would be a short recipe that a consuming project places in its own test suite, calling the existing discovery functions. If several projects need the same runner, a small opt-in test helper in the distributable package could remove repeated request-loop code. Neither option requires a new URL report, a management command, or a second discovery source. The existing report UI serves a different use case: inspecting the current site and its current data interactively. Whether that UI remains part of the package is a product-scope decision; adopting `TestCase` alone does not make its live-site role disappear.

### Could API v3 populate objects for a smoke test?

It can populate **specific objects in a controlled test database**. V3 supports authenticated create operations for pages, media, redirects, sites, and API-enabled snippets. A consuming project could POST a known page type with a known parent and required fields, then run discovery. That is useful when the project deliberately wants to test its v3 write path as well as the resulting GET URLs.

It does not solve generic fixture creation for an installable package:

- The live reports already choose representative objects from the site's own database. Reading the same objects through v3 adds an HTTP and authentication dependency without creating additional URL coverage.
- A Django `TestCase` uses a separate test database. A v3 POST made through its client writes there, not to the live site. It still requires v3 to be installed and mounted, a bearer token with create permission, a valid parent or related objects, and input for the concrete model. A failed v3 create would prevent the later smoke request, mixing fixture setup failures with endpoint failures.
- Copying production content into a test database through v3 would be a migration workflow. V3's read and create schemas differ: only exposed and writable fields can be submitted, and snippets are present only when API-enabled. The API does not cover every Wagtail feature, including Site settings and workflow operations. Parent IDs, relations, files, permissions, and site hosts would need project-specific mapping. The package cannot infer a complete, valid copy from the API response.

For a runner outside the Wagtail process, v3's page list can provide IDs and `meta.html_url` values for API-visible pages. The installed package already has database access to those page objects and can discover more than the API exposes, so v3 reads offer little simplification in this repository.

For a reusable smoke test, use existing instances in a live or staging site for read-only checks, and let each project's tests supply fixtures when an isolated `TestCase` needs more objects. V3 writes can remain an optional project-specific setup technique. They should not be a required dependency or a way to create content on a live production site during a smoke run.

## Recommended implementation order

1. Make frontend route rows method aware, or merge callbacks that share a path into one GET-focused row. Ensure a POST, PATCH, PUT, or DELETE operation cannot be shown as a successful GET test merely because another operation uses its path. Apply this rule to other resolver-backed routes too, rather than adding a v3-only exception.
2. Recognize v3 `find` and other operations that need query input as requiring it. OpenAPI lists the individual `find` parameters as optional, so this case needs an explicit rule. Use a concrete, safe query only when the package has a known matching object; otherwise keep the row visible with a skip reason.
3. Resolve a small allowlist of public GET detail routes from existing representative objects, then check the result using the Django test client. Pages, images, documents, and redirects are candidates. Site, schema, and snippet reads require a separate decision about v3 bearer-token support; a superuser session alone does not provide it.
4. Evaluate OpenAPI as an optional **v3-only** source for method and parameter metadata after the row model and tests support it. Schema and docs routes can be disabled with `WAGTAILAPI_DOCS_ENABLED=False`, and v3 is still a preview, so runtime reliance on a public schema endpoint would be brittle. The mounted Django URL resolver must continue to supply route coverage.

The smallest useful first patch is item 1 plus tests that cover shared GET/POST paths and a POST-only path. Items 2 and 3 can then be measured by the number of newly testable GET URLs, rather than by schema coverage alone.

## Sources

- [Wagtail 8.0 release notes](https://docs.wagtail.org/en/stable/releases/8.0.html): v3 scope and preview status.
- [Wagtail API v3 overview](https://docs.wagtail.org/en/stable/advanced_topics/api/v3/index.html): mounted routes, OpenAPI, optional docs, and supported resources.
- [V3 API authentication](https://docs.wagtail.org/en/stable/advanced_topics/api/v3/authentication.html): bearer-token and anonymous-read behavior.
- [V3 API reference](https://docs.wagtail.org/en/stable/advanced_topics/api/v3/reference.html): operations, parameters, and methods.
- [V3 schema discovery](https://docs.wagtail.org/en/stable/advanced_topics/api/v3/schema.html): distinct read and create schemas and API field requirements.
