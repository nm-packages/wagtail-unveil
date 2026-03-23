import logging
from collections.abc import Callable
from dataclasses import dataclass

from wagtail import hooks

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdminInstanceResolverContext:
    """Context passed to admin instance resolver extensions."""

    namespace: str
    name: str
    callback: object
    route: str
    current_instance: object | None = None


AdminInstanceMatcher = Callable[[AdminInstanceResolverContext], bool]
AdminInstanceResolverFunc = Callable[[AdminInstanceResolverContext], object | None]


@dataclass(frozen=True)
class AdminInstanceResolver:
    """Describe a hookable strategy for resolving admin URL parameters."""

    label: str
    matches: AdminInstanceMatcher
    resolver: AdminInstanceResolverFunc
    override: bool = False


def _describe_hook_fn(hook_fn):
    """Return a readable dotted path for a registered hook function."""
    hook_name = getattr(hook_fn, "__qualname__", getattr(hook_fn, "__name__", repr(hook_fn)))
    hook_module = getattr(hook_fn, "__module__", "")
    return f"{hook_module}.{hook_name}" if hook_module else hook_name


def _validate_admin_instance_resolver(resolver, hook_name):
    """Ensure a hook-provided admin resolver exposes callable entry points."""
    if not callable(resolver.matches):
        raise TypeError(
            f"{hook_name} registered AdminInstanceResolver '{resolver.label}' with a non-callable matches function."
        )
    if not callable(resolver.resolver):
        raise TypeError(
            f"{hook_name} registered AdminInstanceResolver '{resolver.label}' with a non-callable resolver."
        )


def _coerce_admin_instance_resolvers(result, hook_name):
    """Normalize hook results into a flat list of admin instance resolvers."""
    if result is None:
        return []
    if isinstance(result, AdminInstanceResolver):
        _validate_admin_instance_resolver(result, hook_name)
        return [result]
    if isinstance(result, (list, tuple)):
        resolvers = []
        for resolver in result:
            if not isinstance(resolver, AdminInstanceResolver):
                raise TypeError(f"{hook_name} must return AdminInstanceResolver instances.")
            _validate_admin_instance_resolver(resolver, hook_name)
            resolvers.append(resolver)
        return resolvers
    raise TypeError(f"{hook_name} must return an AdminInstanceResolver, a list/tuple of them, or None.")


def get_registered_admin_instance_resolvers():
    """Return admin instance resolvers registered through Wagtail hooks.

    Hook name:
    - ``register_unveil_admin_instance_resolvers``

    Hook functions may return a single ``AdminInstanceResolver``, a list/tuple
    of them, or ``None``. Broken hook contributions are logged and skipped so
    other registered resolvers can still participate in discovery.
    """
    resolvers = []
    hook_name = "register_unveil_admin_instance_resolvers"
    for hook_fn in hooks.get_hooks(hook_name):
        hook_label = _describe_hook_fn(hook_fn)
        try:
            result = hook_fn()
        except Exception:
            logger.warning(
                "Skipping %s hook %s because it raised an exception.",
                hook_name,
                hook_label,
                exc_info=True,
            )
            continue

        try:
            resolvers.extend(_coerce_admin_instance_resolvers(result, hook_name))
        except Exception:
            logger.warning(
                "Skipping %s hook %s because it returned invalid admin instance resolvers.",
                hook_name,
                hook_label,
                exc_info=True,
            )
    return resolvers
