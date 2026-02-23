import io

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image as PILImage
from wagtail.contrib.forms.models import FormSubmission
from wagtail.contrib.redirects.models import Redirect
from wagtail.contrib.search_promotions.models import Query, SearchPromotion
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.models import Collection, Page, Site

from sandbox.core.models import BrandingSettings, ListingPage, SocialMediaSettings, StandardPage
from sandbox.forms.models import FormField, FormPage
from sandbox.home.models import HomePage
from sandbox.inventory.models import Product, Supplier
from sandbox.taxonomy.models import Person

# Prefix used to identify sample data created by this command
SAMPLE_PREFIX = "[Sample]"


def make_image_file(colour, size=(200, 200), format="PNG"):
    """Create an in-memory image file with a solid colour."""
    img = PILImage.new("RGB", size, colour)
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f"sample_{colour}.png")


class Command(BaseCommand):
    help = "Create sample data in the sandbox for development and testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove all sample data before recreating it.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self._clear_sample_data()

        self._create_images()
        self._create_documents()
        self._create_redirects()
        self._create_search_promotions()
        self._create_editor_user()
        self._create_child_pages()
        self._create_core_pages()
        self._create_collections()
        self._create_people()
        self._create_suppliers()
        self._create_products()
        self._create_form_pages()
        self._create_settings()

    def _clear_sample_data(self):
        """Remove all sample data created by this command."""
        # Images
        deleted = Image.objects.filter(title__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write(f"Deleted {deleted[0]} image(s)")

        # Documents
        deleted = Document.objects.filter(title__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write(f"Deleted {deleted[0]} document(s)")

        # Redirects
        deleted = Redirect.objects.filter(
            old_path__startswith="/sample-old-page-"
        ).delete()
        self.stdout.write(f"Deleted {deleted[0]} redirect(s)")

        # Search promotions
        deleted = SearchPromotion.objects.filter(
            description__startswith=SAMPLE_PREFIX
        ).delete()
        self.stdout.write(f"Deleted {deleted[0]} search promotion(s)")

        # Editor user
        deleted = User.objects.filter(username="editor").delete()
        self.stdout.write(f"Deleted {deleted[0]} user(s)")

        # Collections
        sample_collections = Collection.objects.filter(name__startswith=SAMPLE_PREFIX)
        count = sample_collections.count()
        for collection in sample_collections:
            collection.delete()
        self.stdout.write(f"Deleted {count} collection(s)")

        # Products (before suppliers due to FK)
        deleted = Product.objects.filter(name__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write(f"Deleted {deleted[0]} product(s)")

        # Suppliers
        deleted = Supplier.objects.filter(name__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write(f"Deleted {deleted[0]} supplier(s)")

        # People
        deleted = Person.objects.filter(name__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write(f"Deleted {deleted[0]} person(s)")

        # Form submissions (before pages, due to FK)
        deleted = FormSubmission.objects.filter(
            page__title__startswith=SAMPLE_PREFIX
        ).delete()
        self.stdout.write(f"Deleted {deleted[0]} form submission(s)")

        # Settings
        default_site = Site.objects.filter(is_default_site=True).first()
        if default_site:
            deleted = SocialMediaSettings.objects.filter(
                site=default_site,
                facebook__startswith="https://facebook.com/sample",
            ).delete()
            self.stdout.write(f"Deleted {deleted[0]} social media setting(s)")
        deleted = BrandingSettings.objects.filter(
            site_name__startswith=SAMPLE_PREFIX
        ).delete()
        self.stdout.write(f"Deleted {deleted[0]} branding setting(s)")

        # Child pages (includes form pages)
        Page.objects.filter(title__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write("Deleted sample pages")

    def _create_images(self):
        """Create sample images using Pillow."""
        colours = [
            ("red", (255, 0, 0)),
            ("green", (0, 255, 0)),
            ("blue", (0, 0, 255)),
        ]
        for name, rgb in colours:
            title = f"{SAMPLE_PREFIX} {name.title()} Image"
            if Image.objects.filter(title=title).exists():
                self.stdout.write(f"Skipped image: {title} (already exists)")
                continue
            image_file = make_image_file(rgb)
            Image.objects.create(title=title, file=image_file)
            self.stdout.write(f"Created image: {title}")

    def _create_documents(self):
        """Create sample text documents."""
        documents = [
            ("Report", "This is a sample report document."),
            ("Notes", "This is a sample notes document."),
            ("Guide", "This is a sample guide document."),
        ]
        for name, content in documents:
            title = f"{SAMPLE_PREFIX} {name}"
            if Document.objects.filter(title=title).exists():
                self.stdout.write(f"Skipped document: {title} (already exists)")
                continue
            file = ContentFile(content.encode("utf-8"), name=f"sample_{name.lower()}.txt")
            Document.objects.create(title=title, file=file)
            self.stdout.write(f"Created document: {title}")

    def _create_redirects(self):
        """Create sample redirects."""
        for i in range(1, 4):
            old_path = f"/sample-old-page-{i}/"
            if Redirect.objects.filter(old_path=old_path).exists():
                self.stdout.write(f"Skipped redirect: {old_path} (already exists)")
                continue
            Redirect.objects.create(old_path=old_path, redirect_link="/")
            self.stdout.write(f"Created redirect: {old_path} -> /")

    def _create_search_promotions(self):
        """Create sample promoted search results."""
        home_page = HomePage.objects.first()
        if not home_page:
            self.stdout.write("Skipped search promotions: no HomePage found")
            return

        queries = ["example", "test"]
        for query_string in queries:
            description = f"{SAMPLE_PREFIX} Promoted result for '{query_string}'"
            if SearchPromotion.objects.filter(description=description).exists():
                self.stdout.write(
                    f"Skipped search promotion: {query_string} (already exists)"
                )
                continue
            query = Query.get(query_string)
            SearchPromotion.objects.create(
                query=query,
                page=home_page,
                description=description,
            )
            self.stdout.write(f"Created search promotion: {query_string} -> HomePage")

    def _create_editor_user(self):
        """Create a non-superuser editor with the Editors group."""
        if User.objects.filter(username="editor").exists():
            self.stdout.write("Skipped user: editor (already exists)")
            return

        user = User.objects.create_user(
            username="editor",
            email="editor@example.com",
            password="editor123",
        )
        editors_group, _ = Group.objects.get_or_create(name="Editors")
        user.groups.add(editors_group)
        self.stdout.write("Created user: editor (password: editor123)")

    def _create_child_pages(self):
        """Create sample child pages under HomePage."""
        home_page = HomePage.objects.first()
        if not home_page:
            self.stdout.write("Skipped child pages: no HomePage found")
            return

        page_titles = [
            f"{SAMPLE_PREFIX} About Us",
            f"{SAMPLE_PREFIX} Contact",
        ]
        for title in page_titles:
            if Page.objects.filter(title=title).exists():
                self.stdout.write(f"Skipped page: {title} (already exists)")
                continue
            slug = title.replace(SAMPLE_PREFIX, "").strip().lower().replace(" ", "-")
            page = StandardPage(title=title, slug=f"sample-{slug}")
            home_page.add_child(instance=page)
            self.stdout.write(f"Created page: {title}")

    def _create_core_pages(self):
        """Create a ListingPage with StandardPage children under HomePage."""
        home_page = HomePage.objects.first()
        if not home_page:
            self.stdout.write("Skipped core pages: no HomePage found")
            return

        listing_title = f"{SAMPLE_PREFIX} Blog"
        if Page.objects.filter(title=listing_title).exists():
            self.stdout.write(f"Skipped page: {listing_title} (already exists)")
            return

        listing_page = ListingPage(
            title=listing_title,
            slug="sample-blog",
            intro="<p>A sample blog listing page.</p>",
        )
        home_page.add_child(instance=listing_page)
        self.stdout.write(f"Created page: {listing_title}")

        for post_title in ["First Post", "Second Post", "Third Post"]:
            title = f"{SAMPLE_PREFIX} {post_title}"
            slug = f"sample-{post_title.lower().replace(' ', '-')}"
            page = StandardPage(
                title=title,
                slug=slug,
                body=f"<p>Content for {post_title}.</p>",
            )
            listing_page.add_child(instance=page)
            self.stdout.write(f"Created page: {title}")

    def _create_collections(self):
        """Create sample collections under the root collection."""
        root_collection = Collection.objects.first()
        collection_names = [
            f"{SAMPLE_PREFIX} Photos",
            f"{SAMPLE_PREFIX} Downloads",
        ]
        for name in collection_names:
            if Collection.objects.filter(name=name).exists():
                self.stdout.write(f"Skipped collection: {name} (already exists)")
                continue
            root_collection.add_child(name=name)
            self.stdout.write(f"Created collection: {name}")

    def _create_people(self):
        """Create sample Person instances for ModelAdmin listing."""
        people = [
            ("Alice Johnson", "alice@example.com", "Developer"),
            ("Bob Smith", "bob@example.com", "Designer"),
            ("Carol Williams", "carol@example.com", "Editor"),
        ]
        for name, email, job_title in people:
            full_name = f"{SAMPLE_PREFIX} {name}"
            if Person.objects.filter(name=full_name).exists():
                self.stdout.write(f"Skipped person: {full_name} (already exists)")
                continue
            Person.objects.create(name=full_name, email=email, job_title=job_title)
            self.stdout.write(f"Created person: {full_name}")

    def _create_suppliers(self):
        """Create sample Supplier instances for ModelViewSet listing."""
        suppliers = [
            ("Acme Corp", "sales@acme.example.com", "https://acme.example.com"),
            ("Widget Co", "info@widgetco.example.com", "https://widgetco.example.com"),
        ]
        for name, email, website in suppliers:
            full_name = f"{SAMPLE_PREFIX} {name}"
            if Supplier.objects.filter(name=full_name).exists():
                self.stdout.write(f"Skipped supplier: {full_name} (already exists)")
                continue
            Supplier.objects.create(name=full_name, email=email, website=website)
            self.stdout.write(f"Created supplier: {full_name}")

    def _create_products(self):
        """Create sample Product instances for ModelViewSet listing."""
        supplier = Supplier.objects.filter(name__startswith=SAMPLE_PREFIX).first()
        if not supplier:
            self.stdout.write("Skipped products: no sample supplier found")
            return

        products = [
            ("Gadget Alpha", "GAD-001", "A versatile gadget.", "29.99"),
            ("Gadget Beta", "GAD-002", "An improved gadget.", "49.99"),
            ("Widget Standard", "WID-001", "A standard widget.", "9.99"),
        ]
        for name, sku, description, price in products:
            full_name = f"{SAMPLE_PREFIX} {name}"
            full_sku = f"{SAMPLE_PREFIX}-{sku}"
            if Product.objects.filter(name=full_name).exists():
                self.stdout.write(f"Skipped product: {full_name} (already exists)")
                continue
            Product.objects.create(
                name=full_name,
                sku=full_sku,
                description=description,
                price=price,
                supplier=supplier,
            )
            self.stdout.write(f"Created product: {full_name}")

    def _create_form_pages(self):
        """Create a sample form page with form fields under HomePage."""
        home_page = HomePage.objects.first()
        if not home_page:
            self.stdout.write("Skipped form pages: no HomePage found")
            return

        title = f"{SAMPLE_PREFIX} Contact Form"
        if Page.objects.filter(title=title).exists():
            self.stdout.write(f"Skipped page: {title} (already exists)")
            return

        form_page = FormPage(
            title=title,
            slug="sample-contact-form",
            intro="<p>Fill in the form below to get in touch.</p>",
            thank_you_text="<p>Thank you for your message. We will be in touch shortly.</p>",
        )
        home_page.add_child(instance=form_page)

        fields = [
            ("name", "singleline", "Your name"),
            ("email", "email", "Your email address"),
            ("message", "multiline", "Your message"),
        ]
        for sort_order, (clean_name, field_type, label) in enumerate(fields):
            FormField.objects.create(
                page=form_page,
                sort_order=sort_order,
                label=label,
                field_type=field_type,
                clean_name=clean_name,
            )

        self.stdout.write(f"Created page: {title} (with {len(fields)} form fields)")

        self._create_form_submissions(form_page)

    def _create_form_submissions(self, form_page):
        """Create sample form submissions for the given form page."""
        submissions = [
            {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "message": "Hello, I have a question about your services.",
            },
            {
                "name": "Bob Smith",
                "email": "bob@example.com",
                "message": "I would like to request a demo.",
            },
            {
                "name": "Carol Williams",
                "email": "carol@example.com",
                "message": "Great website! Keep up the good work.",
            },
        ]
        for form_data in submissions:
            FormSubmission.objects.create(
                page=form_page,
                form_data=form_data,
            )
        self.stdout.write(
            f"Created {len(submissions)} form submission(s) for {form_page.title}"
        )

    def _create_settings(self):
        """Create sample site and generic settings."""
        default_site = Site.objects.filter(is_default_site=True).first()
        if not default_site:
            self.stdout.write("Skipped settings: no default site found")
            return

        # Site-specific social media settings
        _, created = SocialMediaSettings.objects.get_or_create(
            site=default_site,
            defaults={
                "facebook": "https://facebook.com/sample-site",
                "twitter": "https://twitter.com/sample-site",
                "instagram": "https://instagram.com/sample-site",
            },
        )
        if created:
            self.stdout.write("Created social media settings")
        else:
            self.stdout.write("Skipped social media settings (already exists)")

        # Generic branding settings
        if BrandingSettings.objects.exists():
            self.stdout.write("Skipped branding settings (already exists)")
        else:
            BrandingSettings.objects.create(
                site_name=f"{SAMPLE_PREFIX} My Wagtail Site",
                tagline=f"{SAMPLE_PREFIX} A sample tagline for the site",
            )
            self.stdout.write("Created branding settings")
