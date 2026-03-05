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
from sandbox.events.models import EventIndexPage, EventPage
from sandbox.forms.models import FormField, FormPage
from sandbox.home.models import HomePage
from sandbox.inventory.models import Product, Supplier
from sandbox.taxonomy.models import Banner, Category, Colour, Person

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
        self._create_multisite_fixture()
        self._create_core_pages()
        self._create_collections()
        self._create_people()
        self._create_categories()
        self._create_colours()
        self._create_banners()
        self._assign_banners_to_home()
        self._create_suppliers()
        self._create_products()
        self._create_form_pages()
        self._create_event_pages()
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
        deleted = Redirect.objects.filter(old_path__startswith="/sample-old-page-").delete()
        self.stdout.write(f"Deleted {deleted[0]} redirect(s)")

        # Search promotions
        deleted = SearchPromotion.objects.filter(description__startswith=SAMPLE_PREFIX).delete()
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

        # Categories
        deleted = Category.objects.filter(name__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write(f"Deleted {deleted[0]} category/categories")

        # Colours
        deleted = Colour.objects.filter(name__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write(f"Deleted {deleted[0]} colour(s)")

        # Banners (clear FK assignment before deleting)
        home_page = HomePage.objects.first()
        if home_page and home_page.banner and home_page.banner.title.startswith(SAMPLE_PREFIX):
            home_page.banner = None
            home_page.save_revision().publish()
        deleted = Banner.objects.filter(title__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write(f"Deleted {deleted[0]} banner(s)")

        # Form submissions (before pages, due to FK)
        deleted = FormSubmission.objects.filter(page__title__startswith=SAMPLE_PREFIX).delete()
        self.stdout.write(f"Deleted {deleted[0]} form submission(s)")

        # Settings
        default_site = Site.objects.filter(is_default_site=True).first()
        if default_site:
            deleted = SocialMediaSettings.objects.filter(
                site=default_site,
                facebook__startswith="https://facebook.com/sample",
            ).delete()
            self.stdout.write(f"Deleted {deleted[0]} social media setting(s)")

        deleted = Site.objects.filter(hostname="sub.localhost", is_default_site=False).delete()
        self.stdout.write(f"Deleted {deleted[0]} multisite fixture site(s)")

        deleted = BrandingSettings.objects.filter(site_name__startswith=SAMPLE_PREFIX).delete()
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
                self.stdout.write(f"Skipped search promotion: {query_string} (already exists)")
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

        pages = [
            (
                f"{SAMPLE_PREFIX} About Us",
                "<p>Welcome to our About Us page. We are a team of developers "
                "building great things with Wagtail.</p>"
                "<p>Our mission is to make content management simple and enjoyable.</p>",
            ),
            (
                f"{SAMPLE_PREFIX} Contact",
                "<p>Get in touch with us using the details below.</p>"
                "<p>Email: hello@example.com</p>"
                "<p>Phone: +44 1234 567890</p>",
            ),
        ]
        for title, body in pages:
            if Page.objects.filter(title=title).exists():
                self.stdout.write(f"Skipped page: {title} (already exists)")
                continue
            slug = title.replace(SAMPLE_PREFIX, "").strip().lower().replace(" ", "-")
            page = StandardPage(title=title, slug=f"sample-{slug}", body=body)
            home_page.add_child(instance=page)
            self.stdout.write(f"Created page: {title}")

    def _create_multisite_fixture(self):
        """Create a non-default site with its own homepage and child page."""
        root_page = Page.get_first_root_node()
        if not root_page:
            self.stdout.write("Skipped multisite fixture: no root page found")
            return

        subsite_title = f"{SAMPLE_PREFIX} Subsite Home"
        subsite_slug = "sample-subsite-home"
        sub_home = HomePage.objects.filter(title=subsite_title, slug=subsite_slug).first()
        if sub_home:
            self.stdout.write(f"Skipped page: {subsite_title} (already exists)")
        else:
            sub_home = HomePage(
                title=subsite_title,
                slug=subsite_slug,
            )
            root_page.add_child(instance=sub_home)
            self.stdout.write(f"Created page: {subsite_title}")

        subsite_page_title = f"{SAMPLE_PREFIX} Subsite About"
        if Page.objects.filter(title=subsite_page_title).exists():
            self.stdout.write(f"Skipped page: {subsite_page_title} (already exists)")
        else:
            sub_page = StandardPage(
                title=subsite_page_title,
                slug="sample-subsite-about",
                body="<p>Sample content served from the subdomain fixture site.</p>",
            )
            sub_home.add_child(instance=sub_page)
            self.stdout.write(f"Created page: {subsite_page_title}")

        site, created = Site.objects.update_or_create(
            hostname="sub.localhost",
            port=8000,
            defaults={
                "site_name": f"{SAMPLE_PREFIX} Subsite",
                "root_page": sub_home,
                "is_default_site": False,
            },
        )
        if created:
            self.stdout.write(f"Created site: {site.hostname}")
        else:
            self.stdout.write(f"Updated site: {site.hostname}")

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

    def _create_categories(self):
        """Create sample Category snippet instances."""
        categories = ["News", "Events", "Blog"]
        for name in categories:
            full_name = f"{SAMPLE_PREFIX} {name}"
            if Category.objects.filter(name=full_name).exists():
                self.stdout.write(f"Skipped category: {full_name} (already exists)")
                continue
            Category.objects.create(name=full_name)
            self.stdout.write(f"Created category: {full_name}")

    def _create_colours(self):
        """Create sample Colour instances."""
        colours = ["Red", "Green", "Blue"]
        for name in colours:
            full_name = f"{SAMPLE_PREFIX} {name}"
            if Colour.objects.filter(name=full_name).exists():
                self.stdout.write(f"Skipped colour: {full_name} (already exists)")
                continue
            Colour.objects.create(name=full_name)
            self.stdout.write(f"Created colour: {full_name}")

    def _create_banners(self):
        """Create sample Banner snippet instances (previewable)."""
        banners = [
            (
                "Welcome",
                "<p>Welcome to our website. Discover what we have to offer.</p>",
                "https://example.com/about",
                "Find out more",
            ),
            (
                "Special Offer",
                "<p>Don't miss our limited-time offers. Available this month only.</p>",
                "https://example.com/offers",
                "View offers",
            ),
        ]
        for title, body, url, cta_text in banners:
            full_title = f"{SAMPLE_PREFIX} {title}"
            if Banner.objects.filter(title=full_title).exists():
                self.stdout.write(f"Skipped banner: {full_title} (already exists)")
                continue
            Banner.objects.create(
                title=full_title,
                body=body,
                call_to_action_url=url,
                call_to_action_text=cta_text,
            )
            self.stdout.write(f"Created banner: {full_title}")

    def _assign_banners_to_home(self):
        """Assign the first sample banner to the HomePage."""
        home_page = HomePage.objects.first()
        if not home_page:
            self.stdout.write("Skipped banner assignment: no HomePage found")
            return

        banner = Banner.objects.filter(title__startswith=SAMPLE_PREFIX).first()
        if not banner:
            self.stdout.write("Skipped banner assignment: no sample banners found")
            return

        if home_page.banner == banner:
            self.stdout.write(f"Skipped banner assignment: already set to '{banner}'")
            return

        home_page.banner = banner
        home_page.save_revision().publish()
        self.stdout.write(f"Assigned banner '{banner}' to HomePage")

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
        self.stdout.write(f"Created {len(submissions)} form submission(s) for {form_page.title}")

    def _create_event_pages(self):
        """Create a sample EventIndexPage with child EventPages under HomePage."""
        home_page = HomePage.objects.first()
        if not home_page:
            self.stdout.write("Skipped event pages: no HomePage found")
            return

        title = f"{SAMPLE_PREFIX} Events"
        if Page.objects.filter(title=title).exists():
            self.stdout.write(f"Skipped page: {title} (already exists)")
            return

        index_page = EventIndexPage(
            title=title,
            slug="sample-events",
            intro="<p>A sample events index page with routable sub-URLs.</p>",
        )
        home_page.add_child(instance=index_page)
        self.stdout.write(f"Created page: {title}")

        from datetime import date

        events = [
            ("Spring Conference", date(2025, 4, 15), "Convention Centre"),
            ("Summer Workshop", date(2025, 7, 20), "Community Hall"),
            ("Autumn Meetup", date(2024, 10, 5), "Library"),
            ("Winter Gala", date(2024, 12, 12), "Grand Hotel"),
        ]
        for event_title, event_date, location in events:
            full_title = f"{SAMPLE_PREFIX} {event_title}"
            slug = f"sample-{event_title.lower().replace(' ', '-')}"
            event = EventPage(
                title=full_title,
                slug=slug,
                event_date=event_date,
                location=location,
                body=f"<p>Details for {event_title}.</p>",
            )
            index_page.add_child(instance=event)
            self.stdout.write(f"Created page: {full_title}")

    def _create_settings(self):
        """Create sample site and generic settings."""
        default_site = Site.objects.filter(is_default_site=True).first()
        if not default_site:
            self.stdout.write("Skipped settings: no default site found")
            return

        # Site-specific social media settings
        _, created = SocialMediaSettings.objects.update_or_create(
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
            self.stdout.write("Updated social media settings")

        # Generic branding settings
        existing = BrandingSettings.objects.first()
        if existing:
            existing.site_name = f"{SAMPLE_PREFIX} My Wagtail Site"
            existing.tagline = f"{SAMPLE_PREFIX} A sample tagline for the site"
            existing.save()
            self.stdout.write("Updated branding settings")
        else:
            BrandingSettings.objects.create(
                site_name=f"{SAMPLE_PREFIX} My Wagtail Site",
                tagline=f"{SAMPLE_PREFIX} A sample tagline for the site",
            )
            self.stdout.write("Created branding settings")
