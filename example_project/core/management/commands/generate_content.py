from django.core.management.base import BaseCommand
from example_project.for_snippets.models import ExampleSnippetModel, ExampleSnippetViewSetModel
from example_project.core.models import ExamplePageModelBasic, ExamplePageModelStandard
from wagtail.models import Page


class Command(BaseCommand):
    help = "Generate example content for the Wagtail Unveil package"

    def handle(self, *args, **options):
        self.stdout.write("Generating example content...")

        # Create example snippets
        # create or update 5 example snippets
        for i in range(5):
            ExampleSnippetModel.objects.update_or_create(
                title=f"Example Snippet {i + 1}",
                defaults={
                    "description": f"This is an example snippet description for snippet {i + 1}."
                }
            )
            ExampleSnippetViewSetModel.objects.update_or_create(
                title=f"Example ViewSet Snippet {i + 1}",
                defaults={
                    "description": f"This is an example ViewSet snippet description for snippet {i + 1}."
                }
            )
        self.stdout.write("Example snippets created successfully!")

        # Create example pages
        # create or update 5 example pages
        root_page = Page.objects.get(id=3)  # Assuming the root page ID is 3
        for i in range(5):
            if not ExamplePageModelBasic.objects.filter(title=f"Example Basic Page {i + 1}").exists():
                root_page.add_child(
                    instance=ExamplePageModelBasic(
                        title=f"Example Basic Page {i + 1}",
                        slug=f"example-basic-page-{i + 1}",
                        body=f"This is the body content for example basic page {i + 1}."
                    )
                )
            if not ExamplePageModelStandard.objects.filter(title=f"Example Standard Page {i + 1}").exists():
                root_page.add_child(
                    instance=ExamplePageModelStandard(
                        title=f"Example Standard Page {i + 1}",
                        slug=f"example-standard-page-{i + 1}",
                        intro=f"This is the intro for example standard page {i + 1}.",
                        body=f"This is the body content for example standard page {i + 1}."
                    )
                )
        self.stdout.write("Example pages created successfully!")

        # Here you would implement the logic to create example content
        # For demonstration purposes, we will just print a message
        self.stdout.write("Example content generated successfully!")