from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.models import PreviewableMixin
from wagtail.snippets.models import register_snippet


@register_snippet
class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"


class Person(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    job_title = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "person"
        verbose_name_plural = "people"


class Colour(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "colour"
        verbose_name_plural = "colours"


class Banner(PreviewableMixin, models.Model):
    title = models.CharField(max_length=255)
    body = RichTextField(blank=True)
    call_to_action_url = models.URLField(blank=True)
    call_to_action_text = models.CharField(max_length=100, blank=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("body"),
        FieldPanel("call_to_action_url"),
        FieldPanel("call_to_action_text"),
    ]

    def __str__(self):
        return self.title

    def get_preview_template(self, request, mode_name):
        return "taxonomy/previews/banner.html"

    class Meta:
        verbose_name = "banner"
        verbose_name_plural = "banners"
