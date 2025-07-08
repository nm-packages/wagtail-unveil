from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from example_project.for_snippets.models import ExampleSnippetViewSetModel


class ExampleSnippetViewSetModelViewSet(SnippetViewSet):
    model = ExampleSnippetViewSetModel

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
    ]

# Instead of using @register_snippet as a decorator on the model class,
# register the snippet using register_snippet as a function and pass in
# the custom SnippetViewSet subclass.
register_snippet(ExampleSnippetViewSetModelViewSet)