from .base import * # noqa: F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-8yw(eft92qp%nyy%9l%f93k7^ah4)dt=pm-%w5jhw#xrjc2=vi"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Additional optional for development/testing
# The apps below may not be installed by in a Wagtail project.

INSTALLED_APPS += ["wagtail_unveil"] # noqa: F405

# Uncomment to Enable Wagtail Model Admin
INSTALLED_APPS += ["wagtail_modeladmin"]

# Uncomment to Enable Wagtail Locales
# It's extected to see errors in the Unviel report view if this is disabled.
INSTALLED_APPS += ["wagtail.locales"]

# Uncomment to Enable Internationalization
# It's extected to see errors in the Unviel report view if this is disabled.
USE_I18N = True
WAGTAIL_I18N_ENABLED = True
USE_L10N = True
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES = [
    ('en', "English"),
    ('fr', "French"),
    ('es', "Spanish"),
]

# Uncomment if you want to test search promotions
# It's extected to see errors in the Unviel report view if this is not installed.
INSTALLED_APPS += ["wagtail.contrib.search_promotions"]

# Adding this will adjust the max instances for all output
# WAGTAIL_UNVEIL_MAX_INSTANCES = 1 # 0 is all instances

# Uncomment to use the provided username and password for urls checks
WAGTAIL_UNVEIL_CHECK_USERNAME = "test" # Default is None
WAGTAIL_UNVEIL_CHECK_PASSWORD = "test" # Default is None

try:
    from .local import * # noqa: F403
except ImportError:
    pass
