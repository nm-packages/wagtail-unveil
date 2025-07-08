from django.core.management.base import BaseCommand
from example_project.for_snippets.models import ExampleSnippetModel, ExampleSnippetViewSetModel
from example_project.core.models import ExamplePageModelBasic, ExamplePageModelStandard
from wagtail.models import Page
from wagtail.images.models import Image
from wagtail.documents.models import Document
from PIL import Image as PILImage, ImageDraw, ImageFont
from django.core.files.base import ContentFile
import io


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

        # Create example images
        # create or update 5 example images
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green  
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
        ]
        
        for i, color in enumerate(colors):
            image_title = f"Example Image {i + 1}"
            
            # Check if image already exists
            if not Image.objects.filter(title=image_title).exists():
                # Create a colored image using PIL
                img = PILImage.new('RGB', (800, 600), color)
                
                # Add some text to make it more interesting
                draw = ImageDraw.Draw(img)
                text = f"Image {i + 1}"
                
                # Calculate text position (center)
                try:
                    font = ImageFont.load_default()
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except Exception:
                    # Fallback if textbbox is not available
                    text_width = len(text) * 10
                    text_height = 20
                
                x = (800 - text_width) // 2
                y = (600 - text_height) // 2
                
                # Use contrasting color for text
                text_color = (255, 255, 255) if sum(color) < 400 else (0, 0, 0)
                draw.text((x, y), text, fill=text_color, font=font)
                
                # Save image to memory
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG', quality=95)
                img_io.seek(0)
                
                # Create Wagtail Image object
                image_file = ContentFile(img_io.read(), name=f'example_image_{i + 1}.jpg')
                wagtail_image = Image(title=image_title, file=image_file)
                wagtail_image.save()
                
                self.stdout.write(f"Created image: {image_title}")
        
        self.stdout.write("Example images created successfully!")

        # Create example documents
        # create or update 5 example documents
        document_types = [
            ('txt', 'This is a sample text document with example content.\n\nIt contains multiple lines of text to demonstrate document creation.'),
            ('csv', 'Name,Age,City\nJohn Doe,30,New York\nJane Smith,25,Los Angeles\nBob Johnson,35,Chicago'),
            ('json', '{\n  "name": "Example JSON Document",\n  "type": "sample",\n  "data": {\n    "items": [1, 2, 3, 4, 5],\n    "active": true\n  }\n}'),
            ('xml', '<?xml version="1.0" encoding="UTF-8"?>\n<document>\n  <title>Example XML Document</title>\n  <content>\n    <item id="1">First item</item>\n    <item id="2">Second item</item>\n  </content>\n</document>'),
            ('md', '# Example Markdown Document\n\nThis is a **sample** markdown document.\n\n## Features\n\n- Bullet points\n- *Italic text*\n- `Code snippets`\n\n### Code Example\n\n```python\nprint("Hello, World!")\n```')
        ]
        
        for i, (ext, content) in enumerate(document_types):
            document_title = f"Example Document {i + 1}"
            
            # Check if document already exists
            if not Document.objects.filter(title=document_title).exists():
                # Create document content
                doc_content = content.encode('utf-8')
                
                # Create Wagtail Document object
                doc_file = ContentFile(doc_content, name=f'example_document_{i + 1}.{ext}')
                wagtail_document = Document(title=document_title, file=doc_file)
                wagtail_document.save()
                
                self.stdout.write(f"Created document: {document_title} (.{ext})")
        
        self.stdout.write("Example documents created successfully!")

        # Here you would implement the logic to create example content
        # For demonstration purposes, we will just print a message
        self.stdout.write("Example content generated successfully!")