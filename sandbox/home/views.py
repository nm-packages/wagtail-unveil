from django.http import HttpResponseServerError


def intentional_frontend_error(_request):
    """Sandbox-only endpoint that reliably returns a 500 for report testing."""
    return HttpResponseServerError("Intentional frontend error")
