from django.test import TestCase
from wagtail.models import Page, Site

from sandbox.core.models import StandardPage
from sandbox.home.models import HomePage
from wagtail_unveil.discovery.frontend import get_frontend_urls


class TestMultisiteFrontendUrls(TestCase):
    def setUp(self):
        root = Page.get_first_root_node()

        self.sub_home = HomePage(title="Subsite Home", slug="subsite-home")
        root.add_child(instance=self.sub_home)
        self.sub_home.save_revision().publish()

        self.sub_page = StandardPage(
            title="Subsite About",
            slug="subsite-about",
            body="<p>Subsite page body.</p>",
        )
        self.sub_home.add_child(instance=self.sub_page)
        self.sub_page.save_revision().publish()

        self.sub_site = Site.objects.create(
            hostname="sub.localhost",
            port=8000,
            site_name="Subsite",
            root_page=self.sub_home,
            is_default_site=False,
        )

        self.urls = get_frontend_urls()

    def test_non_default_site_page_is_discovered_but_marked_untestable(self):
        matches = [u for u in self.urls if u.source == "page" and u.page_title == "Subsite About"]
        self.assertEqual(len(matches), 1)
        match = matches[0]
        self.assertEqual(match.url, "/subsite-about/")
        self.assertFalse(match.is_testable)
        self.assertEqual(match.skip_reason, "Belongs to non-default site host: sub.localhost:8000")

    def test_default_site_page_entries_remain_testable(self):
        default_site_pages = [
            u
            for u in self.urls
            if u.source == "page" and u.page_title != "Subsite About" and not u.name and not u.skip_reason
        ]
        self.assertGreater(len(default_site_pages), 0)
