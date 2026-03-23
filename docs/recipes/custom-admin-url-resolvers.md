# Add Custom Admin URL Resolvers

Use this recipe when `wagtail-unveil` can discover admin routes from a third-party Wagtail package or project-specific admin integration, but some parameterised routes still show `URL requires parameters` because `wagtail-unveil` cannot infer a representative object on its own.

`wagtail-unveil` exposes a public hook for this kind of project-level customization. This guide focuses on the general pattern for adding a custom admin URL resolver. It uses `wagtail-modeladmin` as a worked example, but the same structure can be adapted for other packages that expose admin URLs and need a concrete instance before those URLs can be tested.

## When To Use This

Add this hook when all of the following are true:

- your project includes a package or custom admin integration that exposes parameterised admin routes
- `wagtail-unveil` can see those routes in the backend report or backend API
- some of those routes are still untestable because they need a concrete object ID
- the route callback metadata does not already give `wagtail-unveil` enough information to pick the right instance

If the routes are already showing a populated `resolved_route` and `is_testable: true`, you do not need this customization.

## Public Extension Points

This recipe uses only the public integration surface:

- Wagtail hook: `register_unveil_admin_instance_resolvers`
- resolver type: `wagtail_unveil.discovery.extensions.AdminInstanceResolver`

Add the hook to a `wagtail_hooks.py` file inside one of your installed apps. If your project already has a suitable app-level `wagtail_hooks.py`, add the resolver there. Otherwise, create one in an installed app that loads alongside the admin package or integration you are extending.

## General Pattern

Each custom resolver has two responsibilities:

- `matches` decides whether the resolver should handle the current admin URL
- `resolver` returns the object that should be used to reverse that URL

The default `override=False` is usually correct for package-specific resolvers. Use `override=True` only when `wagtail-unveil` is already selecting an instance from callback metadata, but that earlier choice is the wrong model for the route you need to reverse.

If you need to support more than one package-specific pattern, your hook can return a list or tuple of `AdminInstanceResolver` objects instead of just one.

## Worked Example: `wagtail-modeladmin`

The example below matches `wagtail-modeladmin` route names, infers the model from the route name, and returns a representative instance for `wagtail-unveil` to use when reversing the URL.

The sandbox/example project in this repository already includes this hook, which is why its `wagtail-modeladmin` edit, delete, and history routes are already testable with a populated `resolved_route`.

```python
import re
from django.apps import apps
from wagtail import hooks

from wagtail_unveil.discovery.extensions import AdminInstanceResolver


MODELADMIN_URL_NAME_RE = re.compile(r"^(?P<app_label>\w+)_(?P<model_name>\w+)_modeladmin_\w+$")


def _get_modeladmin_model(url_name):
    match = MODELADMIN_URL_NAME_RE.match(url_name)
    if not match:
        return None

    try:
        return apps.get_model(match.group("app_label"), match.group("model_name"))
    except LookupError:
        return None


def _get_modeladmin_instance(context):
    model = _get_modeladmin_model(context.name)
    if model is None:
        return None

    queryset = model.objects.all()
    if hasattr(model, "depth"):
        queryset = queryset.exclude(depth=1)
    return queryset.first()


@hooks.register("register_unveil_admin_instance_resolvers")
def register_modeladmin_unveil_extension():
    return AdminInstanceResolver(
        label="extension:wagtail-modeladmin",
        matches=lambda context: _get_modeladmin_model(context.name) is not None,
        resolver=_get_modeladmin_instance,
    )
```

## Verify The Result

Before adding the hook, affected third-party admin routes may remain visible but untestable. After adding the hook and restarting your development server:

1. Open the backend URLs report at `/unveil/report/backend-urls/`.
2. Find the affected routes for the package or admin integration you are extending.
3. Confirm that the parameterised routes you targeted now show a concrete `resolved_route` and are marked testable.

You can also inspect the backend API response at `/unveil/api/v1/backend-urls/` and look for:

- `resolved_route` populated for the affected routes
- `is_testable` set to `true`
- the original `route` still preserved as the canonical discovered pattern

If you are following the `wagtail-modeladmin` example above, the routes to check are typically edit, delete, and history.

## Troubleshooting

### The route is still marked `URL requires parameters` after adding the hook

The resolver probably is not matching the route name you expect, or it is returning `None`. Check the route names in the backend report or API output and make sure your `matches` function matches those names.

### The resolver matches, but no route becomes testable

Your resolver may not be finding an instance. Create at least one suitable object for the package or admin integration you are targeting and try again.

### When should I use `override=True`?

Use `override=True` only when `wagtail-unveil` is already finding an instance from callback metadata, but that instance is the wrong type for the route you are trying to reverse. In that case, your custom resolver can replace the earlier choice instead of acting as a fallback.

You do not need it for the `wagtail-modeladmin` example above.

## Related

- [Recipes](index.md) — Back to recipe list
- [Backend URLs Report](../features/backend-urls-report.md) — See how resolved admin URLs are presented
- [Discovery Architecture](../contributing/discovery-architecture.md) — Contributor-focused internals for the resolution pipeline
