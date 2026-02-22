from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from sandbox.taxonomy.models import Colour


@register_snippet
class ColourSnippetViewSet(SnippetViewSet):
    model = Colour
    icon = "snippet"
    menu_label = "Colours"
    menu_name = "colours"
    add_to_admin_menu = True
