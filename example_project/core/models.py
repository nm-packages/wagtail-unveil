from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel


class BasePage(Page):
    """
    Base class for all pages in the example project.
    This can be extended by other page models to include common fields or methods.
    """

    class Meta:
        abstract = True

    banner_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Optional banner image for the page.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("banner_image"),
    ]


class ExamplePageModelBasic(BasePage):
    """A basic example page model"""

    body = RichTextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel("body"),
    ]


class ExamplePageModelStandard(BasePage):
    """A standard example page model"""

    intro = models.TextField(blank=True)
    body = RichTextField(blank=True)

    content_panels = BasePage.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
    ]


class ExampleModelViewSetModel(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class ExampleWagtailModeladminModel(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
    ]

    def __str__(self):
        return self.title
