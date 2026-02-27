import os

from django.conf import settings


def get_pages_per_type():
    """Return `WAGTAIL_UNVEIL_PAGES_PER_TYPE` as a non-negative integer.

    Accepted inputs:
    - missing / None -> 1
    - int >= 0 -> unchanged
    - numeric string (e.g. "3", "0") -> coerced to int

    Invalid, unusable, or negative values fall back to 1.
    Use 0 explicitly for no limit.

    Env var WAGTAIL_UNVEIL_PAGES_PER_TYPE is checked first; Django setting is the fallback.
    """
    raw_value = os.environ.get("WAGTAIL_UNVEIL_PAGES_PER_TYPE") or getattr(settings, "WAGTAIL_UNVEIL_PAGES_PER_TYPE", 1)

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


def get_skip_url_prefixes():
    """Return WAGTAIL_UNVEIL_SKIP_URL_PREFIXES as a list of normalised prefix strings.

    Accepted inputs:
    - missing / None -> []
    - list of strings -> each string stripped of a leading slash

    Invalid types and non-string items are silently dropped.

    Env var WAGTAIL_UNVEIL_SKIP_URL_PREFIXES is checked first (comma-separated string);
    Django setting is the fallback.
    """
    env_value = os.environ.get("WAGTAIL_UNVEIL_SKIP_URL_PREFIXES")
    if env_value is not None:
        if not env_value.strip():
            return []
        return [item.strip().lstrip("/") for item in env_value.split(",") if item.strip()]
    raw = getattr(settings, "WAGTAIL_UNVEIL_SKIP_URL_PREFIXES", [])
    if not isinstance(raw, (list, tuple)):
        return []
    result = []
    for item in raw:
        if isinstance(item, str):
            result.append(item.lstrip("/"))
    return result


def get_api_key():
    """Return WAGTAIL_UNVEIL_API_KEY as a non-empty string, or '' if absent/invalid.

    Accepted inputs:
    - environment variable WAGTAIL_UNVEIL_API_KEY (checked first)
    - Django setting WAGTAIL_UNVEIL_API_KEY (fallback)

    Invalid, non-string, or empty values return ''.
    """
    value = os.environ.get("WAGTAIL_UNVEIL_API_KEY") or getattr(settings, "WAGTAIL_UNVEIL_API_KEY", "")
    if not isinstance(value, str):
        return ""
    return value.strip()
