# Add URL Resolution for `wagtail-modeladmin`

Use this recipe when `wagtail-unveil` can discover `wagtail-modeladmin` admin routes, but leaves parameterised routes such as edit, delete, or history marked as `URL requires parameters`.

`wagtail-unveil` already exposes a public hook for this kind of project-level customization. This guide uses `wagtail-modeladmin` as the worked example, but the same pattern can be adapted for other third-party Wagtail packages that need a representative object before their admin URLs can be tested.

## When To Use This

Add this hook when all of the following are true:

- your project uses `wagtail-modeladmin`
- `wagtail-unveil` can see the `modeladmin` routes in the backend report or backend API
- parameterised `modeladmin` routes are still untestable because they need a concrete object ID

If the routes are already showing a populated `resolved_route` and `is_testable: true`, you do not need this customization.

## Public Extension Points

This recipe uses only the public integration surface:

- Wagtail hook: `register_unveil_admin_instance_resolvers`
- resolver type: `wagtail_unveil.discovery.extensions.AdminInstanceResolver`

Add the hook to a `wagtail_hooks.py` file inside one of your own installed apps. If your project already has a suitable app-level `wagtail_hooks.py`, add the resolver there. Otherwise, create one in an installed app that is loaded alongside your `wagtail-modeladmin` registration.

## Example

The example below matches `wagtail-modeladmin` route names, infers the model from the route name, and returns a representative instance for `wagtail-unveil` to use when reversing the URL.

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
        predicate=lambda context: _get_modeladmin_model(context.name) is not None,
        resolver=_get_modeladmin_instance,
    )
```

### Why This Shape Works

- `predicate` decides whether the resolver should handle the current admin URL
- `resolver` returns the object that should be used to reverse that URL
- the default `override=False` is correct for `wagtail-modeladmin`, because this is a fallback when `wagtail-unveil` does not already have a usable instance from callback metadata

If you need to support more than one package-specific pattern, your hook can return a list or tuple of `AdminInstanceResolver` objects instead of just one.

## Verify The Result

After adding the hook and restarting your development server:

1. Open the backend URLs report at `/unveil/report/backend-urls/`.
2. Find the `wagtail-modeladmin` routes for your model.
3. Confirm that parameterised routes such as edit, delete, and history now show a concrete `resolved_route` and are marked testable.

You can also inspect the backend API response at `/unveil/api/v1/backend-urls/` and look for:

- `resolved_route` populated for the affected `modeladmin` routes
- `is_testable` set to `true`
- the original `route` still preserved as the canonical discovered pattern

## Troubleshooting

### The route is still marked `URL requires parameters`

The resolver probably is not matching the route name you expect, or it is returning `None`. Check the route names in the backend report or API output and make sure your `predicate` matches those names.

### The resolver matches, but no route becomes testable

Your resolver may not be finding an instance. Create at least one object for the modeladmin model and try again.

### When should I use `override=True`?

You do not need it for `wagtail-modeladmin`.

Use `override=True` only when `wagtail-unveil` is already finding an instance from callback metadata, but that instance is the wrong type for the route you are trying to reverse. In that case, your custom resolver can replace the earlier choice instead of acting as a fallback.

## Related

- [Recipes](index.md) — Back to recipe list
- [Backend URLs Report](../features/backend-urls-report.md) — See how resolved admin URLs are presented
- [Discovery Architecture](../contributing/discovery-architecture.md) — Contributor-focused internals for the resolution pipeline
