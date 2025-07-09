
from wagtail_modeladmin.options import ModelAdmin, modeladmin_register
from example_project.core.models import ExampleWagtailModeladminModel
from example_project.core.views import example_model_viewset
from wagtail import hooks

@hooks.register("register_admin_viewset")
def register_example_model_viewset():
    return example_model_viewset



class ExampleWagtailModeladminModelAdmin(ModelAdmin):
    model = ExampleWagtailModeladminModel
    # base_url_path = "examplemodeladmin"  # customise the URL from default to admin/bookadmin
    menu_label = "Ex. Model Admin"  # ditch this to use verbose_name_plural from model
    # menu_icon = "pilcrow"  # change as required
    # menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    # add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
    # exclude_from_explorer = (
    #     False  # or True to exclude pages of this type from Wagtail's explorer view
    # )
    # add_to_admin_menu = True  # or False to exclude your model from the menu
    # list_display = ("title")


# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(ExampleWagtailModeladminModelAdmin)