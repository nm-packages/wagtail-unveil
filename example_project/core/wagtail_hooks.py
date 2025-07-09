from example_project.core.views import example_model_viewset
from wagtail import hooks

@hooks.register("register_admin_viewset")
def register_example_model_viewset():
    return example_model_viewset
