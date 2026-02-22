from django.conf import settings


def get_pages_per_type():
    """Return the max number of page instances to test per page type.

    Values: 0 or None = all (no limit), positive int = limit per type.
    Default: 0 (all pages).
    """
    return getattr(settings, "WAGTAIL_UNVEIL_PAGES_PER_TYPE", 0)
