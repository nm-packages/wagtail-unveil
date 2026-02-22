from django.core.management.base import BaseCommand

from wagtail_unveil.urls import get_frontend_urls


class Command(BaseCommand):
    help = "List all discovered frontend URLs (pages and resolver routes)."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--pages",
            action="store_true",
            help="Only show URLs from Wagtail pages.",
        )
        group.add_argument(
            "--resolver",
            action="store_true",
            help="Only show URLs from the Django URL resolver.",
        )

    def handle(self, *args, **options):
        urls = get_frontend_urls()

        if options["pages"]:
            urls = [u for u in urls if u.source == "page"]
        elif options["resolver"]:
            urls = [u for u in urls if u.source == "resolver"]

        if not urls:
            self.stdout.write("No URLs found.")
            return

        url_width = max(len(u.url) for u in urls)
        source_width = max(len(u.source) for u in urls)
        type_width = max(len(u.page_type) for u in urls) or 9
        title_width = max(len(u.page_title) for u in urls) or 5
        name_width = max(len(u.name) for u in urls) or 4

        header = (
            f"{'URL':<{url_width}}  "
            f"{'SOURCE':<{source_width}}  "
            f"{'PAGE TYPE':<{type_width}}  "
            f"{'TITLE':<{title_width}}  "
            f"{'NAME':<{name_width}}"
        )
        separator = "-" * len(header)

        self.stdout.write(separator)
        self.stdout.write(header)
        self.stdout.write(separator)

        for u in urls:
            self.stdout.write(
                f"{u.url:<{url_width}}  "
                f"{u.source:<{source_width}}  "
                f"{u.page_type:<{type_width}}  "
                f"{u.page_title:<{title_width}}  "
                f"{u.name:<{name_width}}"
            )

        self.stdout.write(separator)
        self.stdout.write(f"\nTotal: {len(urls)} URLs")
