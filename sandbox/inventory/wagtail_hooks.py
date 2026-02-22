from wagtail import hooks

from sandbox.inventory.viewsets import InventoryViewSetGroup, ProductChooserViewSet


@hooks.register("register_admin_viewset")
def register_inventory_viewset_group():
    return InventoryViewSetGroup()


@hooks.register("register_admin_viewset")
def register_product_chooser_viewset():
    return ProductChooserViewSet("product_chooser")
