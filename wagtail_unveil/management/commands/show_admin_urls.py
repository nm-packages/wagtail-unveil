from django.core.management.base import BaseCommand

from wagtail_unveil.urls import get_admin_urls


class Command(BaseCommand):
    help = "List all discovered Wagtail admin URLs."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--parameterized",
            action="store_true",
            help="Only show URLs that contain parameters.",
        )
        group.add_argument(
            "--static",
            action="store_true",
            help="Only show URLs without parameters.",
        )

    def handle(self, *args, **options):
        urls = get_admin_urls()

        if options["parameterized"]:
            urls = [u for u in urls if u.has_parameters]
        elif options["static"]:
            urls = [u for u in urls if not u.has_parameters]

        if not urls:
            self.stdout.write("No URLs found.")
            return

        route_width = max(len(u.route) for u in urls)
        name_width = max(len(u.name) for u in urls)
        view_width = max(len(u.view_name) for u in urls)

        header = (
            f"{'ROUTE':<{route_width}}  "
            f"{'NAME':<{name_width}}  "
            f"{'VIEW':<{view_width}}"
        )
        separator = "-" * len(header)

        self.stdout.write(separator)
        self.stdout.write(header)
        self.stdout.write(separator)

        for u in urls:
            self.stdout.write(
                f"{u.route:<{route_width}}  "
                f"{u.name:<{name_width}}  "
                f"{u.view_name:<{view_width}}"
            )

        self.stdout.write(separator)
        self.stdout.write(f"\nTotal: {len(urls)} URLs")
