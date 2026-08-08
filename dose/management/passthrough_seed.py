"""Compatibility guard for the retired passthrough endpoint cloning API."""


def seed_passthrough_endpoints(tenant, *, log=None) -> int:
    """Do not clone endpoint rows; each tenant provisioner owns its exact record."""
    if log:
        log(
            "Passthrough endpoint seeding is disabled; tenant app provisioners "
            "must create their own endpoint rows."
        )
    return 0
