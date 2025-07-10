
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register
from example_project.core.models import ExampleWagtailModeladminModel
from example_project.core.views import example_model_viewset
from wagtail import hooks

@hooks.register("register_admin_viewset")
def register_example_model_viewset():
    return example_model_viewset



class ExampleWagtailModeladminModelAdmin(ModelAdmin):
    model = ExampleWagtailModeladminModel
    base_url_path = "example-models" # This can be omitted or set Unveil should handle it
    menu_label = "Ex. Model Admin"
    menu_icon = "code"
    menu_order = 900


modeladmin_register(ExampleWagtailModeladminModelAdmin)