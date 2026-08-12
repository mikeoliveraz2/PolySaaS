from django.http import HttpResponse


def test_nextcloud_iframe(request):
    """Retired — Nextcloud must load as a top-level passthrough page, not an iframe."""
    return HttpResponse(
        "<p>Nextcloud iframe test is retired. Open "
        "<a href='/pt/admin/nextcloud/'>/pt/admin/nextcloud/</a> top-level.</p>",
        content_type="text/html; charset=utf-8",
    )
