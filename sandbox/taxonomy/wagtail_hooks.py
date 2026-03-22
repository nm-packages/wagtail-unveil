import re

from django.apps import apps
from wagtail import hooks
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from sandbox.taxonomy.models import Banner, Colour, Person
from wagtail_unveil.discovery.extensions import AdminInstanceResolver

MODELADMIN_URL_NAME_RE = re.compile(r"^(?P<app_label>\w+)_(?P<model_name>\w+)_modeladmin_\w+$")


def _get_modeladmin_model(url_name):
    """Return the modeladmin model class encoded in a URL name, if any."""
    match = MODELADMIN_URL_NAME_RE.match(url_name)
    if not match:
        return None

    try:
        return apps.get_model(match.group("app_label"), match.group("model_name"))
    except LookupError:
        return None


def _get_modeladmin_instance(context):
    """Return a representative instance for a modeladmin route."""
    model = _get_modeladmin_model(context.name)
    if model is None:
        return None

    queryset = model.objects.all()
    if hasattr(model, "depth"):
        queryset = queryset.exclude(depth=1)
    return queryset.first()


@register_snippet
class BannerSnippetViewSet(SnippetViewSet):
    model = Banner
    menu_icon = "pick"
    icon = "pick"
    menu_label = "Banners"
    menu_name = "banners"
    add_to_admin_menu = True
    list_display = ("title",)


@register_snippet
class ColourSnippetViewSet(SnippetViewSet):
    model = Colour
    menu_icon = "view"
    icon = "view"
    menu_label = "Colours"
    menu_name = "colours"
    add_to_admin_menu = True


@modeladmin_register
class PersonModelAdmin(ModelAdmin):
    model = Person
    menu_icon = "user"
    menu_label = "People"
    list_display = ("name", "email", "job_title")
    search_fields = ("name", "email", "job_title")


@hooks.register("register_unveil_admin_instance_resolvers")
def register_modeladmin_unveil_extension():
    """Example project-level hook that resolves wagtail-modeladmin detail routes."""
    return AdminInstanceResolver(
        label="extension:wagtail-modeladmin",
        predicate=lambda context: _get_modeladmin_model(context.name) is not None,
        resolver=_get_modeladmin_instance,
    )
