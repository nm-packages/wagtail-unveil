from wagtail.admin.viewsets.model import ModelViewSet
from example_project.core.models import ExampleModelViewSetModel

class ExampleModelViewSet(ModelViewSet):
    model = ExampleModelViewSetModel
    form_fields = ('title', 'description')
    add_to_admin_menu = True
    icon = 'doc-full-inverse'
    menu_label = 'Ex. Model ViewSet'
    menu_icon = 'view'
    menu_order = 900


example_model_viewset = ExampleModelViewSet()