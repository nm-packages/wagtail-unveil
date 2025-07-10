from django.db import models
from wagtail.snippets.models import register_snippet


@register_snippet
class ExampleSnippetModel(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Example Snippet"
        verbose_name_plural = "Example Snippets"

    def __str__(self):
        return self.title


class ExampleSnippetViewSetModel(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Example Snippet ViewSet"
        verbose_name_plural = "Example Snippet ViewSets"

    def __str__(self):
        return self.title
