from dataclasses import dataclass

from wagtail import hooks


@dataclass(frozen=True)
class AdminInstanceResolverContext:
    """Context passed to admin instance resolver extensions."""

    namespace: str
    name: str
    callback: object
    route: str
    current_instance: object | None = None


@dataclass(frozen=True)
class AdminInstanceResolver:
    """Describe a hookable strategy for resolving admin URL parameters."""

    label: str
    predicate: object
    resolver: object
    override: bool = False


def _coerce_admin_instance_resolvers(result, hook_name):
    """Normalize hook results into a flat list of admin instance resolvers."""
    if result is None:
        return []
    if isinstance(result, AdminInstanceResolver):
        return [result]
    if isinstance(result, (list, tuple)):
        resolvers = []
        for resolver in result:
            if not isinstance(resolver, AdminInstanceResolver):
                raise TypeError(f"{hook_name} must return AdminInstanceResolver instances.")
            resolvers.append(resolver)
        return resolvers
    raise TypeError(f"{hook_name} must return an AdminInstanceResolver, a list/tuple of them, or None.")


def get_registered_admin_instance_resolvers():
    """Return admin instance resolvers registered through Wagtail hooks.

    Hook name:
    - ``register_unveil_admin_instance_resolvers``

    Hook functions may return a single ``AdminInstanceResolver``, a list/tuple
    of them, or ``None``.
    """
    resolvers = []
    hook_name = "register_unveil_admin_instance_resolvers"
    for hook_fn in hooks.get_hooks(hook_name):
        resolvers.extend(_coerce_admin_instance_resolvers(hook_fn(), hook_name))
    return resolvers
