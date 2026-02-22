from django.db import models
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
