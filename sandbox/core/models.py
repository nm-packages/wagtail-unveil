from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    BaseSiteSetting,
    register_setting,
)
from wagtail.fields import RichTextField
from wagtail.models import Page


class ListingPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["core.StandardPage"]

    class Meta:
        verbose_name = "Listing Page"


class StandardPage(Page):
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    parent_page_types = ["home.HomePage", "core.ListingPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Standard Page"


@register_setting
class SocialMediaSettings(BaseSiteSetting):
    facebook = models.URLField(blank=True, help_text="Facebook page URL")
    twitter = models.URLField(blank=True, help_text="Twitter profile URL")
    instagram = models.URLField(blank=True, help_text="Instagram profile URL")

    panels = [
        FieldPanel("facebook"),
        FieldPanel("twitter"),
        FieldPanel("instagram"),
    ]

    class Meta:
        verbose_name = "Social Media Settings"


@register_setting
class BrandingSettings(BaseGenericSetting):
    site_name = models.CharField(max_length=255, blank=True, help_text="Site name")
    tagline = models.CharField(max_length=255, blank=True, help_text="Site tagline")

    panels = [
        FieldPanel("site_name"),
        FieldPanel("tagline"),
    ]

    class Meta:
        verbose_name = "Branding Settings"
