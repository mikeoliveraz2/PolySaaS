"""
Sniffer Stream Actions Service
-------------------------------
For every PassThroughEndpoint that has captured traffic (TrafficLog entries),
creates an Instruction + MQOutput for each unique POST path discovered.

Pub/Sub Flow (GCP — primary broker):
  1. PolySniffer captures POST traffic → TrafficLog row.
  2. This service (or signal) creates:
     - an Instruction (POST, path, executescript=EndpointDataExtractorService)
     - an MQOutput (provider=google_pubsub, topic="{trigger}-{path_slug}")
  3. On a live passthrough POST, DoseRequestController matches the Instruction
     (substring match on requestpath) and runs EndpointDataExtractorService.
  4. EndpointDataExtractorService._publish_to_pubsub reads the active MQConfig
     with provider=google_pubsub and publishes the POST body to the topic.
  5. Any number of subscribers on that Pub/Sub topic receive the message
     for parallel processing.

Topic naming convention:  {trigger_path}-{post_path_slug}
  e.g. endpoint trigger "odoo", POST path "/web/dataset/call_kw"
       → topic "odoo-web-dataset-call_kw"
"""
import re
import logging
from django.db import transaction
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _slugify_path(path: str) -> str:
    """Convert a URL path to a safe topic-name segment, e.g. /web/login → web-login"""
    slug = path.strip("/").replace("/", "-").replace("_", "_")
    slug = re.sub(r"[^a-zA-Z0-9\-_]", "", slug)
    return slug.lower() or "root"


def _topic_name(trigger: str, path: str) -> str:
    """Build topic name as {trigger}-{path_slug}, max 255 chars."""
    trigger_slug = re.sub(r"[^a-zA-Z0-9\-_]", "", trigger.strip("/").replace("/", "-"))
    path_slug = _slugify_path(path)
    return f"{trigger_slug}-{path_slug}"[:255]


def _set_schema(tenant):
    """Point the DB search_path at the tenant schema so TrafficLog is visible."""
    import re as _re
    from django.db import connection
    schema = tenant.schema_name if tenant and tenant.schema_name else "public"
    if not _re.match(r"^[a-zA-Z0-9_]+$", schema):
        raise ValueError(f"Invalid schema name: {schema!r}")
    with connection.cursor() as cur:
        cur.execute(f"SET search_path TO {schema}, public;")


def _resolve_pubsub_defaults(tenant):
    """
    Look up the tenant's active GCP Pub/Sub MQConfig to populate MQOutput
    defaults (project_id, credentials). Returns a dict or empty dict if none.
    """
    from dose.models.mq_config import MQConfig
    cfg = MQConfig.objects.filter(
        tenant=tenant,
        provider="google_pubsub",
        is_active=True,
    ).first()
    if not cfg:
        cfg = MQConfig.objects.filter(
            provider="google_pubsub",
            is_active=True,
        ).first()
    if cfg:
        return {
            "pubsub_project_id": cfg.pubsub_project_id or "",
            "pubsub_credentials_json": cfg.pubsub_credentials_json or "",
        }
    return {}


def create_stream_actions_for_endpoint(endpoint, tenant, dry_run=False):
    """
    For a single PassThroughEndpoint, find all unique POST paths in TrafficLog
    and create (or update) one Instruction + one MQOutput per path.

    Returns a list of result dicts describing what was created/skipped.
    """
    from dose.polysniffer.models import TrafficLog
    from dose.models.instruction import Instruction
    from dose.models.mq_output import MQOutput

    _set_schema(tenant)

    trigger = (endpoint.trigger_path or "").strip("/") or str(endpoint.id)

    try:
        logs = list(
            TrafficLog.objects.filter(
                endpoint_name__icontains=trigger,
                method="POST",
            ).values_list("path", flat=True).distinct()
        )

        if not logs:
            parsed = urlparse(endpoint.endpoint_url)
            domain_fragment = parsed.netloc.split(":")[0]
            logs = list(
                TrafficLog.objects.filter(
                    url__icontains=domain_fragment,
                    method="POST",
                ).values_list("path", flat=True).distinct()
            )
    except Exception as e:
        logger.warning(f"TrafficLog query failed for {trigger}: {e}")
        return [{"endpoint": trigger, "status": "no_posts_found", "note": str(e)}]

    logs = list(dict.fromkeys(logs))

    results = []

    if not logs:
        return [{"endpoint": endpoint.trigger_path, "status": "no_posts_found"}]

    pubsub_defaults = _resolve_pubsub_defaults(tenant)

    for raw_path in logs:
        path = raw_path.strip() or "/"
        topic = _topic_name(trigger, path)
        instruction_path = f"/{trigger}/{path.strip('/')}" if not path.startswith(f"/{trigger}") else path

        if dry_run:
            results.append({
                "endpoint": trigger,
                "path": path,
                "topic": topic,
                "instruction_path": instruction_path,
                "status": "dry_run",
            })
            continue

        with transaction.atomic():
            instruction, instr_created = Instruction.objects.get_or_create(
                tenant=tenant,
                requestpath=instruction_path,
                requestmethod="POST",
                defaults={
                    "eventKey": topic,
                    "description": f"Auto-generated from sniffer: {endpoint.get_menu_title()} POST {path}",
                    "direction": "REQ",
                    "executescript": "EndpointDataExtractorService",
                    "appusername": "sniffer",
                    "urllist": endpoint.endpoint_url,
                    "save_callbackdata": True,
                },
            )

            mq_output, mq_created = MQOutput.objects.get_or_create(
                tenant=tenant,
                name=f"sniffer-{topic}"[:200],
                defaults={
                    "provider": "google_pubsub",
                    "is_active": True,
                    "instruction_path": instruction_path,
                    "pubsub_project_id": pubsub_defaults.get("pubsub_project_id", ""),
                    "pubsub_topic": topic,
                    "pubsub_credentials_json": pubsub_defaults.get("pubsub_credentials_json", ""),
                    "message_format": "json",
                    "include_request_metadata": True,
                    "include_response_data": False,
                    "description": (
                        f"Auto-generated: publish {endpoint.get_menu_title()} "
                        f"POST {path} as JSON to Pub/Sub topic '{topic}'"
                    ),
                },
            )

        results.append({
            "endpoint": trigger,
            "path": path,
            "topic": topic,
            "instruction_path": instruction_path,
            "instruction_id": instruction.pk,
            "instruction_created": instr_created,
            "mq_output_id": mq_output.pk,
            "mq_output_created": mq_created,
            "status": "created" if (instr_created or mq_created) else "already_exists",
        })

    return results


def create_stream_actions_for_all_sniffed(tenant, dry_run=False):
    """
    Iterate over all PassThroughEndpoints that have TrafficLog data and
    call create_stream_actions_for_endpoint for each.

    Returns aggregated list of results.
    """
    from dose.models.pass_through_endpoint import PassThroughEndpoint
    from dose.polysniffer.models import TrafficLog

    _set_schema(tenant)

    try:
        sniffed_triggers = list(
            TrafficLog.objects.filter(method="POST")
            .values_list("endpoint_name", flat=True)
            .distinct()
        )
    except Exception as e:
        logger.warning(f"TrafficLog scan failed: {e}")
        sniffed_triggers = []

    endpoints = PassThroughEndpoint.objects.all()
    sniffed_lower = [(sn or "").lower() for sn in sniffed_triggers]
    matched = []
    for ep in endpoints:
        trigger = (ep.trigger_path or "").strip("/")
        if any(trigger and trigger.lower() in sn for sn in sniffed_lower):
            matched.append(ep)
        elif ep.endpoint_url:
            domain = urlparse(ep.endpoint_url).netloc.split(":")[0]
            if any(domain and domain.lower() in sn for sn in sniffed_lower):
                matched.append(ep)

    all_results = []
    for ep in matched:
        results = create_stream_actions_for_endpoint(ep, tenant, dry_run=dry_run)
        all_results.extend(results)

    if not all_results:
        all_results.append({"status": "no_sniffed_endpoints_found"})

    return all_results
