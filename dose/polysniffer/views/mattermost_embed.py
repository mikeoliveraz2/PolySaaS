# dose/polysniffer/views/mattermost_embed.py
# Embed view: server-side handler (PolySniffer handlers package).

from django.contrib.admin.views.decorators import staff_member_required

from ..handlers.mattermost_handler import MattermostPassthroughHandler


@staff_member_required
def mattermost_embed_view(request, endpoint_id):
    """Clean embed view using the new handler architecture."""
    handler = MattermostPassthroughHandler(endpoint_id)
    return handler.embed(request)
