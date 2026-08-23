from .slack import SlackEndpointActionAdapter


_ADAPTERS = (SlackEndpointActionAdapter,)


def adapter_for_endpoint(endpoint):
    """Resolve provider behavior without putting app names in shared UI code."""
    for adapter_class in _ADAPTERS:
        if adapter_class.matches_endpoint(endpoint):
            return adapter_class()
    return None
