"""
Django management command to generate example content for the Wagtail Unveil package.
This command will only create content if it does not already exist so running it multiple times will not create duplicates.

Usage:
    python manage.py generate_content

Generated content includes:
- Images (5 programmatically generated colored images with text overlays)
- Documents (5 files of different types: txt, csv, json, xml, md)
- Snippets (5 registered snippets using the decorator+ 5 ViewSet snippets)
- Pages (5 basic pages + 5 standard pages with banner images)
- Form pages (5 form pages with sample submissions)
- Search promotions (5 search queries with page/external link promotions)
- Collections (5 collections)

Requirements:
- PIL (Pillow) for image generation
"""

from django.core.management.base import BaseCommand
from example_project.for_snippets.models import ExampleSnippetModel, ExampleSnippetViewSetModel
from example_project.core.models import ExamplePageModelBasic, ExamplePageModelStandard
from example_project.for_forms.models import ExampleFormPage
from wagtail.contrib.forms.models import FormSubmission
from wagtail.contrib.search_promotions.models import SearchPromotion, Query
from wagtail.models import Page, Collection
from wagtail.images.models import Image
from wagtail.documents.models import Document
from PIL import Image as PILImage, ImageDraw, ImageFont
from django.core.files.base import ContentFile
import io


class Command(BaseCommand):
    help = "Generate example content for the Wagtail Unveil package"

    def handle(self, *args, **options):
        """
        Orchestrates the creation of all example content types in a logical order:
        """
        self.stdout.write("Generating example content...")

        # Create media content first (needed by pages)
        self.generate_example_images()
        self.stdout.write("Example images created successfully!")

        self.generate_example_documents()
        self.stdout.write("Example documents created successfully!")

        # Create snippets
        self.generate_example_snippets()
        self.stdout.write("Example snippets created successfully!")

        # Create page content that references media
        self.generate_example_pages()
        self.stdout.write("Example pages created successfully!")

        # Create form pages with sample submissions
        self.generate_example_form_pages()
        self.stdout.write("Example form pages created successfully!")

        # Create search-promotions
        self.generate_example_search_promotions()
        self.stdout.write("Example search promotions created successfully!")

        # Create collections
        self.generate_example_collections()
        self.stdout.write("Example collections created successfully!")

        self.stdout.write("Example content generated successfully!")

    def generate_example_images(self):
        """
        Creates 5 programmatically generated example images using PIL.
        """
        # Define a palette of 5 distinct colors
        colors = [
            (255, 182, 193),    # Light Pink - warm, inviting
            (144, 238, 144),    # Light Green - fresh, natural
            (173, 216, 230),    # Light Blue - calm, professional
            (255, 255, 224),    # Light Yellow - bright, cheerful
            (221, 160, 221),    # Plum - elegant, sophisticated
        ]
        
        for i, color in enumerate(colors):
            image_title = f"Example Image {i + 1}"
            
            if not Image.objects.filter(title=image_title).exists():
                # Create a solid color background image with centered text
                img = PILImage.new('RGB', (800, 600), color)
                draw = ImageDraw.Draw(img)
                text = f"Image {i + 1}"
                # Calculate text positioning for center alignment
                font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                # Center the text on the image
                x = (800 - text_width) // 2
                y = (600 - text_height) // 2
                # Choose text color for good contrast against background
                # Dark text on light backgrounds, light text on dark backgrounds
                text_color = (255, 255, 255) if sum(color) < 400 else (0, 0, 0)
                draw.text((x, y), text, fill=text_color, font=font)
                
                # Convert PIL image to BytesIO
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG', quality=95)
                img_io.seek(0)
                
                # Create and save the image object
                image_file = ContentFile(img_io.read(), name=f'example_image_{i + 1}.jpg')
                wagtail_image = Image(title=image_title, file=image_file)
                wagtail_image.save()
                
                self.stdout.write(f"Created image: {image_title}")

    def generate_example_documents(self):
        """
        Creates 5 example documents, different file types
        """
        # Example document types and their content
        document_types = [
            ('txt', 'This is a sample text document with example content.\n\nIt contains multiple lines of text to demonstrate document creation.'),
            ('csv', 'Name,Age,City\nJohn Doe,30,New York\nJane Smith,25,Los Angeles\nBob Johnson,35,Chicago'),
            ('json', '{\n  "name": "Example JSON Document",\n  "type": "sample",\n  "data": {\n    "items": [1, 2, 3, 4, 5],\n    "active": true\n  }\n}'),
            ('xml', '<?xml version="1.0" encoding="UTF-8"?>\n<document>\n  <title>Example XML Document</title>\n  <content>\n    <item id="1">First item</item>\n    <item id="2">Second item</item>\n  </content>\n</document>'),
            ('md', '# Example Markdown Document\n\nThis is a **sample** markdown document.\n\n## Features\n\n- Bullet points\n- *Italic text*\n- `Code snippets`\n\n### Code Example\n\n```python\nprint("Hello, World!")\n```')
        ]
        
        for i, (ext, content) in enumerate(document_types):
            document_title = f"Example Document {i + 1}"
            
            if not Document.objects.filter(title=document_title).exists():
                # Encode content as bytes for file creation
                doc_content = content.encode('utf-8')
                
                # Create the document file with appropriate extension
                doc_file = ContentFile(doc_content, name=f'example_document_{i + 1}.{ext}')
                wagtail_document = Document(title=document_title, file=doc_file)
                wagtail_document.save()
                
                self.stdout.write(f"Created document: {document_title} (.{ext})")

    def generate_example_snippets(self):
        """
        Creates example snippet instances for both snippet model types.
        """
        # Create both types of snippet registration
        for i in range(5):
            # @register_snippet decorator
            ExampleSnippetModel.objects.update_or_create(
                title=f"Example Snippet {i + 1}",
                defaults={
                    "description": f"This is an example snippet description for snippet {i + 1}."
                }
            )
            
            # registered via SnippetViewSet
            ExampleSnippetViewSetModel.objects.update_or_create(
                title=f"Example ViewSet Snippet {i + 1}",
                defaults={
                    "description": f"This is an example ViewSet snippet description for snippet {i + 1}."
                }
            )

    def generate_example_pages(self):
        """
        Creates example page instances of two different page types.
        """
        # Get a random selection of available images
        example_images = Image.objects.all().order_by('?')[:5]

        if not example_images.exists():
            self.stdout.write("No images found to associate with example pages. Please create some images first.")
            return
        
        root_page = Page.objects.get(id=3) # ID 3 should be OK here as it's created by the initial migration

        for i in range(5):
            # Create basic page type
            if not ExamplePageModelBasic.objects.filter(title=f"Example Basic Page {i + 1}").exists():
                root_page.add_child(
                    instance=ExamplePageModelBasic(
                        title=f"Example Basic Page {i + 1}",
                        slug=f"example-basic-page-{i + 1}",
                        body=f"This is the body content for example basic page {i + 1}.",
                        banner_image=example_images[i % 5]  # Cycle through available images
                    )
                )
            
            # Create standard page type
            if not ExamplePageModelStandard.objects.filter(title=f"Example Standard Page {i + 1}").exists():
                root_page.add_child(
                    instance=ExamplePageModelStandard(
                        title=f"Example Standard Page {i + 1}",
                        slug=f"example-standard-page-{i + 1}",
                        intro=f"This is the intro for example standard page {i + 1}.",
                        body=f"This is the body content for example standard page {i + 1}.",
                        banner_image=example_images[i % 5]  # Cycle through available images
                    )
                )

    def generate_example_form_pages(self):
        """
        Creates example form pages with form fields and sample submissions.
        """
        # Get the root page for adding form pages to the site structure
        root_page = Page.objects.get(id=3) # ID 3 should be OK here as it's created by the initial migration

        for i in range(5):
            if not ExampleFormPage.objects.filter(title=f"Example Form Page {i + 1}").exists():
                # Create form page instance with intro and thank you content
                form_page = ExampleFormPage(
                    title=f"Example Form Page {i + 1}",
                    slug=f"example-form-page-{i + 1}",
                    intro=f"This is the intro for example form page {i + 1}.",
                    thank_you_text=f"Thank you for submitting the form on example form page {i + 1}."
                )
                
                # Add a form field for collecting a users name
                form_page.form_fields.create(
                    field_type='singleline',  # Single line text input field
                    label='Name',             # Field label shown to users
                    required=True             # Makes the field mandatory
                )

                root_page.add_child(instance=form_page)
                form_page.save_revision().publish()

                # Create sample form submissions
                for j in range(5):
                    FormSubmission.objects.create(
                        page=form_page,
                        form_data={'name': f'Example User {j + 1}'}  # JSON field format for form data
                    )

    def generate_example_search_promotions(self):
        """
        Creates example search promotions
        """
        for i in range(5):
            # Create or retrieve the search query, they are unique
            query, _ = Query.objects.get_or_create(
                query_string=f"example query {i + 1}",
            )
            
            # Only create search promotion if none exists for this query yet
            if not SearchPromotion.objects.filter(query=query).exists():
                # Try to promote an existing page first (preferred approach)
                promoted_page = ExamplePageModelBasic.objects.order_by('?').first()
                
                # Create page-based promotion (internal content)
                SearchPromotion.objects.create(
                    query=query,
                    page=promoted_page,
                    description=f"This is an example search promotion description for promotion {i + 1}.",
                )
            
                # and an external link promotion
                external_link_url = f"https://example.com/promotion-{i + 1}"
                SearchPromotion.objects.create(
                    query=query,
                    external_link_url=external_link_url,
                    external_link_text=f"Example External Link {i + 1}",
                    description=f"This is an example search promotion with an external link for promotion {i + 1}.",
                )

    def generate_example_collections(self):
        """
        Creates example collections
        """
        # Get the root collection
        root_collection = Collection.get_first_root_node()
        
        # Create 5 example collections as children of root
        for i in range(5):
            collection_name = f"Example Collection {i + 1}"
            
            # Check if collection already exists as a child of root
            # This maintains idempotency and prevents duplicate creation
            existing_collection = root_collection.get_children().filter(name=collection_name).first()
            
            if not existing_collection:
                # Create new collection and add to tree structure
                new_collection = Collection(name=collection_name)
                root_collection.add_child(instance=new_collection)
                self.stdout.write(f"Created collection: {collection_name}")
