from django.conf import settings


def get_pages_per_type():
    """Return `WAGTAIL_UNVEIL_PAGES_PER_TYPE` as a non-negative integer.

    Accepted inputs:
    - missing / None -> 1
    - int >= 0 -> unchanged
    - numeric string (e.g. "3", "0") -> coerced to int

    Invalid, unusable, or negative values fall back to 1.
    Use 0 explicitly for no limit.
    """
    raw_value = getattr(settings, "WAGTAIL_UNVEIL_PAGES_PER_TYPE", 1)

    if raw_value is None:
        return 1

    if isinstance(raw_value, int):
        return raw_value if raw_value >= 0 else 1

    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if not stripped:
            return 1
        try:
            parsed = int(stripped)
        except ValueError:
            return 1
        return parsed if parsed >= 0 else 1

    return 1
