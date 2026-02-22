from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.viewsets.model import ModelViewSet, ModelViewSetGroup

from sandbox.inventory.models import Product, Supplier


class SupplierViewSet(ModelViewSet):
    model = Supplier
    icon = "site"
    add_to_admin_menu = False
    form_fields = ["name", "email", "website"]
    list_display = ["name", "email", "website"]
    search_fields = ["name", "email"]


class ProductViewSet(ModelViewSet):
    model = Product
    icon = "doc-full-inverse"
    add_to_admin_menu = False
    inspect_view_enabled = True
    copy_view_enabled = True
    form_fields = ["name", "sku", "description", "price", "supplier", "is_active"]
    list_display = ["name", "sku", "price", "supplier", "is_active"]
    list_filter = ["is_active", "supplier"]
    search_fields = ["name", "sku"]
    list_export = ["name", "sku", "price", "supplier", "is_active"]


class InventoryViewSetGroup(ModelViewSetGroup):
    menu_label = "Inventory"
    menu_icon = "clipboard-list"
    items = (ProductViewSet, SupplierViewSet)


class ProductChooserViewSet(ChooserViewSet):
    model = Product
    icon = "doc-full-inverse"
    choose_one_text = "Choose a product"
    choose_another_text = "Choose another product"
