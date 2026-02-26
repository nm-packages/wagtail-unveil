from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Site

from wagtail_unveil.urls import (
    AdminURL,
    _clean_regex_route,
    get_admin_urls,
)


class TestGetAdminUrls(TestCase):
    def setUp(self):
        self.urls = get_admin_urls()

    def test_returns_urls(self):
        self.assertGreater(len(self.urls), 0)

    def test_all_urls_start_with_admin(self):
        for url in self.urls:
            self.assertTrue(url.route.startswith("admin/"), url.route)

    def test_url_has_expected_fields(self):
        url = self.urls[0]
        self.assertIsInstance(url, AdminURL)
        self.assertIsInstance(url.route, str)
        self.assertIsInstance(url.name, str)
        self.assertIsInstance(url.namespace, str)
        self.assertIsInstance(url.has_parameters, bool)
        self.assertIsInstance(url.view_name, str)

    def test_known_url_present(self):
        names = {url.name for url in self.urls}
        self.assertIn("wagtailadmin_home", names)

    def test_has_parameters_detection(self):
        parameterized = [url for url in self.urls if url.has_parameters]
        static = [url for url in self.urls if not url.has_parameters]
        self.assertGreater(len(parameterized), 0)
        self.assertGreater(len(static), 0)
        for url in static:
            self.assertNotIn("<", url.route)

    def test_is_testable_false_for_non_snippet_parameterized(self):
        for url in self.urls:
            if url.has_parameters and not url.resolved_route:
                self.assertFalse(url.is_testable, url.route)
                self.assertIn(url.skip_reason, ("URL requires parameters", "POST-only view"))

    def test_regex_routes_are_cleaned_and_testable(self):
        """Regex anchors are stripped so non-parameterised regex routes are testable."""
        modeladmin_index = [url for url in self.urls if url.name == "taxonomy_person_modeladmin_index"]
        self.assertEqual(len(modeladmin_index), 1)
        self.assertNotIn("^", modeladmin_index[0].route)
        self.assertTrue(modeladmin_index[0].is_testable, modeladmin_index[0].route)

    def test_is_testable_false_for_logout(self):
        logout = [url for url in self.urls if url.name == "wagtailadmin_logout"]
        self.assertEqual(len(logout), 1)
        self.assertFalse(logout[0].is_testable)
        self.assertEqual(logout[0].skip_reason, "POST-only view")

    def test_is_testable_false_for_error_test(self):
        error = [url for url in self.urls if url.name == "wagtailadmin_error_test"]
        self.assertEqual(len(error), 1)
        self.assertFalse(error[0].is_testable)
        self.assertEqual(error[0].skip_reason, "Intentional error endpoint")

    def test_is_testable_true_for_home(self):
        home = [url for url in self.urls if url.name == "wagtailadmin_home"]
        self.assertEqual(len(home), 1)
        self.assertTrue(home[0].is_testable)
        self.assertEqual(home[0].skip_reason, "")


class TestShowAdminUrlsCommand(TestCase):
    def _call(self, *args):
        out = StringIO()
        call_command("show_admin_urls", *args, stdout=out)
        return out.getvalue()

    def test_command_runs(self):
        output = self._call()
        self.assertIn("Total:", output)

    def test_output_contains_urls(self):
        output = self._call()
        self.assertIn("wagtailadmin_home", output)

    def test_static_filter(self):
        output = self._call("--static")
        for line in output.splitlines():
            if line.startswith("admin/"):
                self.assertNotIn("<", line)

    def test_parameterized_filter(self):
        output = self._call("--parameterized")
        for line in output.splitlines():
            if line.startswith("admin/"):
                self.assertTrue("<" in line or "(" in line, line)


class TestCleanRegexRoute(TestCase):
    """Test the _clean_regex_route() helper."""

    def test_strips_caret(self):
        self.assertEqual(_clean_regex_route("^foo/bar/"), "foo/bar/")

    def test_strips_dollar(self):
        self.assertEqual(_clean_regex_route("foo/bar/$"), "foo/bar/")

    def test_strips_both_anchors(self):
        self.assertEqual(_clean_regex_route("^foo/bar/$"), "foo/bar/")

    def test_converts_named_group(self):
        self.assertEqual(
            _clean_regex_route("^edit/(?P<instance_pk>[-\\w]+)/$"),
            "edit/<instance_pk>/",
        )

    def test_passthrough_normal_route(self):
        self.assertEqual(_clean_regex_route("admin/home/"), "admin/home/")

    def test_multiple_named_groups(self):
        self.assertEqual(
            _clean_regex_route("^a/(?P<pk>[0-9]+)/b/(?P<slug>[-\\w]+)/$"),
            "a/<pk>/b/<slug>/",
        )


class TestParameterisedURLResolution(TestCase):
    """Test that parameterised admin URLs are resolved using real model instances."""

    def setUp(self):
        # Create instances for models that need them
        from wagtail.contrib.redirects.models import Redirect
        from wagtail.contrib.search_promotions.models import Query

        self.query = Query.objects.create(query_string="test search")
        self.redirect = Redirect.objects.create(
            old_path="/test-redirect",
            site=Site.objects.first(),
            redirect_link="/destination",
        )
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        self.document = Document.objects.create(
            title="Test document",
            file="test.pdf",
        )
        self.user = User.objects.create_user(username="testuser", password="password")
        self.group = Group.objects.create(name="Test group")

        from sandbox.taxonomy.models import Banner, Category, Colour

        self.category = Category.objects.create(name="Test category")
        self.colour = Colour.objects.create(name="Test colour")
        self.banner = Banner.objects.create(title="Test banner")

        self.urls = get_admin_urls()
        self.snippet_urls = [u for u in self.urls if u.namespace.startswith("wagtailsnippets_") and u.has_parameters]

    def test_snippet_edit_url_is_testable(self):
        edit_urls = [u for u in self.snippet_urls if u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_snippet_copy_url_is_testable(self):
        copy_urls = [u for u in self.snippet_urls if u.name == "copy"]
        self.assertGreater(len(copy_urls), 0)
        for url in copy_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_snippet_delete_url_is_testable(self):
        delete_urls = [u for u in self.snippet_urls if u.name == "delete"]
        self.assertGreater(len(delete_urls), 0)
        for url in delete_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_resolved_route_contains_pk(self):
        for url in self.snippet_urls:
            if url.resolved_route:
                self.assertNotIn("<", url.resolved_route)
                self.assertRegex(url.resolved_route, r"/\d+/")

    def test_redirect_edit_url_is_testable(self):
        edit_urls = [u for u in self.urls if "redirect" in u.namespace and u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_redirect_delete_url_is_testable(self):
        delete_urls = [u for u in self.urls if "redirect" in u.namespace and u.name == "delete"]
        self.assertGreater(len(delete_urls), 0)
        for url in delete_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_image_edit_url_is_testable(self):
        edit_urls = [u for u in self.urls if "wagtailimages" in u.namespace and u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_image_delete_url_is_testable(self):
        delete_urls = [u for u in self.urls if "wagtailimages" in u.namespace and u.name == "delete"]
        self.assertGreater(len(delete_urls), 0)
        for url in delete_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_image_url_generator_is_testable(self):
        url_gen_urls = [
            u
            for u in self.urls
            if "wagtailimages" in u.namespace and u.name in ("url_generator", "url_generator_output")
        ]
        self.assertGreater(len(url_gen_urls), 0)
        for url in url_gen_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_document_edit_url_is_testable(self):
        edit_urls = [u for u in self.urls if "wagtaildocs" in u.namespace and u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_user_edit_url_is_testable(self):
        edit_urls = [u for u in self.urls if "wagtailusers_users" in u.namespace and u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_resolved_route_has_no_angle_brackets(self):
        resolved = [u for u in self.urls if u.resolved_route]
        self.assertGreater(len(resolved), 0)
        for url in resolved:
            self.assertNotIn("<", url.resolved_route, url.route)

    def test_multi_param_urls_remain_untestable(self):
        multi_param = [u for u in self.urls if u.has_parameters and u.route.count("<") > 1 and not u.resolved_route]
        for url in multi_param:
            self.assertFalse(url.is_testable, url.route)
            self.assertEqual(url.skip_reason, "URL requires parameters")

    def test_searchpick_edit_url_is_testable(self):
        edit_urls = [u for u in self.urls if "searchpromotions" in u.namespace and u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_unresolvable_parameterised_urls_are_untestable(self):
        unresolvable = [u for u in self.urls if u.has_parameters and not u.resolved_route]
        self.assertGreater(len(unresolvable), 0)
        for url in unresolvable:
            self.assertFalse(url.is_testable, url.route)
            self.assertIn(url.skip_reason, ("URL requires parameters", "POST-only view"))


class TestModeladminURLDiscovery(TestCase):
    """Test that wagtail-modeladmin URLs are discovered and testable."""

    def setUp(self):
        from sandbox.taxonomy.models import Person

        Person.objects.create(name="Test Person", email="test@example.com")
        self.urls = get_admin_urls()
        self.modeladmin_urls = [u for u in self.urls if "modeladmin" in u.name]

    def test_modeladmin_urls_discovered(self):
        self.assertGreater(len(self.modeladmin_urls), 0)

    def test_index_is_testable(self):
        index = [u for u in self.modeladmin_urls if u.name.endswith("_index")]
        self.assertEqual(len(index), 1)
        self.assertTrue(index[0].is_testable)
        self.assertFalse(index[0].has_parameters)

    def test_create_is_testable(self):
        create = [u for u in self.modeladmin_urls if u.name.endswith("_create")]
        self.assertEqual(len(create), 1)
        self.assertTrue(create[0].is_testable)
        self.assertFalse(create[0].has_parameters)

    def test_edit_is_testable_with_resolved_route(self):
        edit = [u for u in self.modeladmin_urls if u.name.endswith("_edit")]
        self.assertEqual(len(edit), 1)
        self.assertTrue(edit[0].is_testable)
        self.assertTrue(edit[0].resolved_route)
        self.assertNotIn("<", edit[0].resolved_route)

    def test_delete_is_testable_with_resolved_route(self):
        delete = [u for u in self.modeladmin_urls if u.name.endswith("_delete")]
        self.assertEqual(len(delete), 1)
        self.assertTrue(delete[0].is_testable)
        self.assertTrue(delete[0].resolved_route)

    def test_history_is_testable_with_resolved_route(self):
        history = [u for u in self.modeladmin_urls if u.name.endswith("_history")]
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0].is_testable)
        self.assertTrue(history[0].resolved_route)

    def test_routes_have_no_regex_anchors(self):
        for url in self.modeladmin_urls:
            self.assertNotIn("^", url.route, url.route)
            self.assertNotIn("$", url.route, url.route)

    def test_empty_namespace(self):
        for url in self.modeladmin_urls:
            if url.name.startswith("taxonomy_person"):
                self.assertEqual(url.namespace, "")


class TestSettingsURLDiscovery(TestCase):
    """Test that Wagtail site and generic settings URLs are discovered and testable."""

    def setUp(self):
        from sandbox.core.models import BrandingSettings, SocialMediaSettings

        site = Site.objects.first()
        SocialMediaSettings.objects.get_or_create(
            site=site,
            defaults={
                "facebook": "https://facebook.com/test",
                "twitter": "https://twitter.com/test",
                "instagram": "https://instagram.com/test",
            },
        )
        if not BrandingSettings.objects.exists():
            BrandingSettings.objects.create(
                site_name="Test Site",
                tagline="Test tagline",
            )

        self.urls = get_admin_urls()
        self.settings_urls = [u for u in self.urls if u.namespace == "wagtailsettings"]

    def test_settings_urls_discovered(self):
        self.assertGreater(len(self.settings_urls), 0)

    def test_settings_urls_have_correct_namespace(self):
        for url in self.settings_urls:
            self.assertEqual(url.namespace, "wagtailsettings")

    def test_settings_edit_urls_present(self):
        edit_urls = [u for u in self.settings_urls if u.name == "edit"]
        self.assertGreater(len(edit_urls), 0)

    def test_settings_urls_are_parameterised(self):
        for url in self.settings_urls:
            self.assertTrue(url.has_parameters, url.route)

    def test_settings_routes_contain_settings_prefix(self):
        for url in self.settings_urls:
            self.assertTrue(url.route.startswith("admin/settings/"), url.route)

    def test_settings_redirect_url_is_testable(self):
        redirect_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" not in u.route]
        self.assertGreater(len(redirect_urls), 0)
        for url in redirect_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)

    def test_settings_edit_url_is_testable(self):
        edit_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" in u.route]
        self.assertGreater(len(edit_urls), 0)
        for url in edit_urls:
            self.assertTrue(url.is_testable, url.route)
            self.assertTrue(url.resolved_route, url.route)
            self.assertNotIn("<", url.resolved_route)

    def test_settings_resolved_route_contains_app_and_model(self):
        for url in self.settings_urls:
            if url.resolved_route:
                self.assertIn("/core/", url.resolved_route)

    def test_settings_edit_url_uses_site_pk(self):
        """For BaseSiteSetting edit URL, resolved_route should contain site pk, not settings row pk."""
        from sandbox.core.models import SocialMediaSettings

        # Get the site_id from the settings instance
        settings_instance = SocialMediaSettings.objects.first()
        self.assertIsNotNone(settings_instance)
        expected_site_pk = settings_instance.site_id

        # Find the edit URL for SocialMediaSettings
        edit_urls = [u for u in self.settings_urls if u.name == "edit" and "<int:pk>" in u.route and u.resolved_route]
        self.assertGreater(len(edit_urls), 0)

        # Assert the resolved_route contains the site pk (from settings.site_id), not settings row pk
        for url in edit_urls:
            self.assertIn(f"/{expected_site_pk}/", url.resolved_route)

    def test_settings_preview_url_is_non_testable(self):
        """preview_on_edit URL should be non-testable since sandbox settings don't implement PreviewableMixin."""
        preview_urls = [u for u in self.settings_urls if u.name == "preview_on_edit"]

        # If preview_on_edit URLs are discovered, they should all be non-testable
        for url in preview_urls:
            self.assertFalse(url.is_testable, url.route)
            self.assertTrue(url.skip_reason)
