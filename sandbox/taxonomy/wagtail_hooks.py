from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register

from sandbox.taxonomy.models import Colour, Person


@register_snippet
class ColourSnippetViewSet(SnippetViewSet):
    model = Colour
    icon = "snippet"
    menu_label = "Colours"
    menu_name = "colours"
    add_to_admin_menu = True


@modeladmin_register
class PersonModelAdmin(ModelAdmin):
    model = Person
    icon = "user"
    menu_label = "People"
    list_display = ("name", "email", "job_title")
    search_fields = ("name", "email", "job_title")
