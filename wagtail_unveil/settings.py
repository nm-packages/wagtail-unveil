import os
from dataclasses import dataclass

from django.conf import settings

_UNSET = object()


@dataclass(frozen=True)
class SettingDiagnostic:
    """Describe a wagtail-unveil setting for the diagnostics page."""

    name: str
    source: str
    raw_value: object
    effective_value: object
    notes: str
    sensitive: bool = False

    @property
    def source_label(self):
        labels = {
            "env": "Environment variable",
            "django": "Django setting",
            "default": "Default",
        }
        return labels[self.source]

    @property
    def raw_display(self):
        return _format_setting_value(self.raw_value, sensitive=self.sensitive)

    @property
    def effective_display(self):
        return _format_setting_value(self.effective_value, sensitive=self.sensitive)


def _format_setting_value(value, *, sensitive=False):
    """Render a setting value consistently for diagnostics templates."""
    if value is _UNSET:
        return "Not set"
    if sensitive and isinstance(value, str):
        if not value:
            return "Empty string"
        stripped = value.strip()
        if not stripped:
            return "Whitespace only"
        return f"Configured ({len(stripped)} chars)"
    return repr(value)


def _get_configured_source_and_raw_value(name):
    """Return the highest-precedence configured source, even if the value is unusable."""
    if name in os.environ:
        return "env", os.environ.get(name)

    django_value = getattr(settings, name, _UNSET)
    if django_value is not _UNSET:
        return "django", django_value

    return "default", _UNSET


def _is_blank_string(value):
    """Return True when a value is a string containing only whitespace."""
    return isinstance(value, str) and not value.strip()


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


def inspect_pages_per_type_setting():
    """Describe the configured and effective page-per-type setting."""
    source, raw_value = _get_configured_source_and_raw_value("WAGTAIL_UNVEIL_PAGES_PER_TYPE")
    effective_value = get_pages_per_type()
    notes = []

    if source == "default":
        notes.append("Defaults to 1 when omitted.")
    elif source == "env" and _is_blank_string(raw_value):
        notes.append("Blank environment values are ignored.")
    elif raw_value != effective_value:
        notes.append("Effective value is normalized to a non-negative integer.")

    if effective_value == 0:
        notes.append("0 means no limit.")

    return SettingDiagnostic(
        name="WAGTAIL_UNVEIL_PAGES_PER_TYPE",
        source=source,
        raw_value=raw_value,
        effective_value=effective_value,
        notes=" ".join(notes) or "Value used as-is.",
    )


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


def inspect_skip_url_prefixes_setting():
    """Describe the configured and effective skip-prefix setting."""
    source, raw_value = _get_configured_source_and_raw_value("WAGTAIL_UNVEIL_SKIP_URL_PREFIXES")
    effective_value = get_skip_url_prefixes()
    notes = []

    if source == "default":
        notes.append("Defaults to an empty list when omitted.")
    elif source == "env":
        if _is_blank_string(raw_value):
            notes.append("Blank environment values clear all exclusions.")
        else:
            notes.append("Environment values use comma-separated prefixes.")
    if source != "default" and raw_value != effective_value:
        notes.append("Effective prefixes strip leading slashes and drop invalid entries.")

    return SettingDiagnostic(
        name="WAGTAIL_UNVEIL_SKIP_URL_PREFIXES",
        source=source,
        raw_value=raw_value,
        effective_value=effective_value,
        notes=" ".join(notes) or "Value used as-is.",
    )


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


def inspect_api_key_setting():
    """Describe the configured and effective API key setting."""
    source, raw_value = _get_configured_source_and_raw_value("WAGTAIL_UNVEIL_API_KEY")
    effective_value = get_api_key()
    notes = []

    if source == "default":
        notes.append("Bearer authentication is not configured.")
    elif source == "env" and raw_value == "":
        notes.append("Blank environment values are ignored.")
    elif not isinstance(raw_value, str):
        notes.append("Non-string values are ignored.")
    else:
        if raw_value != raw_value.strip():
            notes.append("Leading and trailing whitespace is stripped from the effective value.")
        if effective_value == "":
            notes.append("Blank values leave Bearer authentication unconfigured.")

    return SettingDiagnostic(
        name="WAGTAIL_UNVEIL_API_KEY",
        source=source,
        raw_value=raw_value,
        effective_value=effective_value,
        notes=" ".join(notes) or "Value used as-is.",
        sensitive=True,
    )


def get_setting_diagnostics():
    """Return diagnostics for all public wagtail-unveil settings."""
    return (
        inspect_api_key_setting(),
        inspect_pages_per_type_setting(),
        inspect_skip_url_prefixes_setting(),
    )
