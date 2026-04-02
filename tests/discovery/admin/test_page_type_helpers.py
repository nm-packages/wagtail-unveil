from django.test import TestCase
from wagtail.models import Page

from wagtail_unveil.discovery.backend_resolution import (
    get_add_subpage_parent_page_instances_by_type,
    get_page_instances_by_type,
)


class TestPageTypeHelperQueries(TestCase):
    def test_get_page_instances_by_type_returns_one_page_per_type(self):
        instances = get_page_instances_by_type()

        self.assertGreater(len(instances), 0)
        self.assertEqual(len({page.pk for page in instances}), len(instances))
        self.assertEqual(
            {
                f"{page.specific_class._meta.app_label}.{page.specific_class._meta.object_name}"
                for page in instances
            },
            {
                f"{page.specific_class._meta.app_label}.{page.specific_class._meta.object_name}"
                for page in Page.objects.exclude(depth=1).select_related("content_type")
            },
        )

    def test_get_add_subpage_parent_page_instances_by_type_returns_compatible_parents(self):
        instances = get_add_subpage_parent_page_instances_by_type()

        self.assertGreater(len(instances), 0)
        self.assertEqual(len({page.pk for page in instances}), len(instances))
        for page in instances:
            with self.subTest(page_id=page.pk):
                self.assertTrue(
                    any(model.can_create_at(page) for model in type(page).creatable_subpage_models()),
                )
