# DO NOT MODIFY: Critical system file. Ask before making changes.

from dose.models import Instruction
from dose.api.methods.dosebase import DoseBase
from dose.services.atomic_services_registry import ATOMIC_SERVICE_REGISTRY, init_atomic_services_registry
from django.contrib import messages
import urllib.parse
import validators
import requests
from urllib.parse import parse_qs, urlsplit
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)
logger.info("Now Logging in doserequestcontroller")

def safe_log_str(obj):
    """
    Convert object to string safely for logging, replacing Unicode characters
    that can't be encoded to cp1252 (Windows console encoding).
    """
    try:
        s = str(obj)
        # Try to encode to ASCII - if it fails, replace non-ASCII with escape sequences
        try:
            s.encode('ascii')
            return s
        except UnicodeEncodeError:
            # Replace non-ASCII characters with ASCII-safe representation
            return s.encode('ascii', 'backslashreplace').decode('ascii')
    except Exception as e:
        return f"<Error encoding object: {type(obj).__name__}>"

from dose.middleware.debug import DebugStackMiddleware   # ← ADD THIS

class DoseRequestController(DebugStackMiddleware, MiddlewareMixin):  # ← FIRST!

    async_mode = False

    def __init__(self, get_response):
        print("********** DoseRequestController initialized **********")
        self.get_response = get_response


    def __call__(self, request):
        print("[DEBUG] ENTERED DoseRequestController __call__ for path:", getattr(request, 'path', None))
        logger.info(f"[DEBUG] request.user: {getattr(request, 'user', None)} (is_authenticated: {getattr(getattr(request, 'user', None), 'is_authenticated', False)})")
        logger.info(f"[DEBUG] request.tenant: {getattr(request, 'tenant', None)}")

        # Ensure request.tenant is set from session if not already present
        if not hasattr(request, 'tenant') or request.tenant is None:
            tenant_id = request.session.get('tenant_id')
            if tenant_id:
                try:
                    from django.db import connection
                    from dose.models.tenant import Tenant
                    with connection.cursor() as cursor:
                        cursor.execute('SET search_path TO public')
                        all_tenants = list(Tenant.objects.all())
                        logger.info(f"[DEBUG] All tenants visible to controller (public schema): {all_tenants}")
                        request.tenant = Tenant.objects.get(id=tenant_id)
                        logger.info(f"[DEBUG] Set request.tenant from session: {request.tenant}")
                except Exception as e:
                    logger.warning(f"[DEBUG] Could not set request.tenant from session tenant_id={tenant_id}: {e}")
            else:
                logger.warning("[DEBUG] No tenant_id in session; request.tenant remains None.")
        # Exclude public subscription page, load-balancer health, DoseMessage, and i18n paths
        if (
            request.path == '/subscribe/'
            or request.path == '/health/'
            or request.path == '/health/ready/'
            or 'dosemessages' in request.path
            or request.path.startswith('/jis18n')
        ):
            return self.get_response(request)
        # Optionally process the request before passing to view
        logger.info("DoseRequestController __call__")
        request_get_params = request.GET
        logger.info("request_get_params= %s", safe_log_str(request_get_params))
        request_post_params = request.POST
        logger.info("request_post_params= %s", safe_log_str(request_post_params))
        request_scheme = request.scheme
        logger.info("request_scheme= %s", request_scheme)
        request_headers = request.headers
        logger.info("request_headers= %s", safe_log_str(request_headers))
        requestmethod = request.method
        logger.info('requestmethod= %s', requestmethod)
        requestpath = request.path
        logger.info('requestpath= %s', requestpath)
        print()
        print('>>>>>>>>>>>>>>>>>>>>>>>> requestpath= %s', requestpath)
        print()
        # Initialize atomic services registry
        init_atomic_services_registry()
        logger.info("ATOMIC_SERVICE_REGISTRY keys: %s", list(ATOMIC_SERVICE_REGISTRY.keys()))

        # Import Parameter model
        try:
            from parameters.models import Parameter
        except ImportError:
            Parameter = None

        # Improved instruction matching logic: match if instruction.requestpath is a substring of the request path
        normalized_request_path = request.path.rstrip('/').lower()

        # Set search_path to tenant schema (and public) before querying Instruction
        from django.db import connection
        tenant_schema = None
        if hasattr(request, 'tenant') and getattr(request.tenant, 'schema_name', None):
            tenant_schema = request.tenant.schema_name
        if tenant_schema:
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {tenant_schema},public;")
                cursor.execute("SHOW search_path;")
                search_path = cursor.fetchone()[0]
            print(f"[DEBUG] PostgreSQL search_path SET to: {search_path}")
        else:
            with connection.cursor() as cursor:
                cursor.execute("SHOW search_path;")
                search_path = cursor.fetchone()[0]
            print(f"[DEBUG] PostgreSQL search_path (no tenant): {search_path}")

        instructions = Instruction.objects.filter(requestmethod=requestmethod, direction='REQ')
        print(f"[DEBUG] All instructions for method={requestmethod}, direction=REQ:")
        for instr in instructions:
            print(f"  - Instruction id={getattr(instr, 'id', None)}, requestpath='{instr.requestpath}', normalized='{instr.requestpath.rstrip('/').lower()}'")
        print(f"[DEBUG] Normalized request path: '{normalized_request_path}'")
        matched_instructions = [
            instr for instr in instructions
            if instr.requestpath.rstrip('/').lower() in normalized_request_path
        ]
        print(f"[DEBUG] matched_instructions for path '{normalized_request_path}' and method '{requestmethod}': {len(matched_instructions)}")
        logger.info("matched_instructions.count()= %s", len(matched_instructions))
        if len(matched_instructions) == 0:
            return self.get_response(request)

        # Example urllist handling (if present in instruction)
        for instruction_row in matched_instructions:
            urllist = getattr(instruction_row, 'urllist', None)
            if urllist:
                for serviceUrl in (urllist or '').split(', '):
                    if not serviceUrl.strip():
                        continue
                    logger.info("serviceUrl= %s", serviceUrl)
                    if not validators.url(serviceUrl):
                        messages.add_message(request, messages.ERROR, serviceUrl + ' IS INVALID')
                        return self.get_response(request)
                    if len(serviceUrl) > 10:
                        mybody = {
                            'Cookie': 'cookieStr',
                            'otherStuff': 'as25',
                            'moreStuff': 'as35',
                            'description': 'Some will prepend this 555 some will replace this and some will append this.',
                            'datetimestamp': '2022-09-01T00:00:00Z'
                        }
                        logger.info('mybody = %s', mybody)
                        # Example request, headers can be customized
                        getdata = requests.get(serviceUrl, json=mybody)
                        logger.info("response getdata = %s", getdata.headers)
                        messages.add_message(request, messages.INFO, serviceUrl + ' Executed!')

        # Continue normal request processing
        # Execute atomic service if executescript is set and matches a registered service
        from dose.models import CallBackData
        for instruction_row in matched_instructions:
            executescript_name = getattr(instruction_row, 'executescript', None)
            atomic_result = None
            # Attach parameters to request before atomic service execution
            if Parameter is not None:
                # Only use executescript_name as the parameter key (no eventKey or matchingKey from instruction)
                matching_key = executescript_name
                if matching_key:
                    params_qs = Parameter.objects.filter(matchingKey=matching_key).order_by('sequence')
                    request.atomic_parameters = list(params_qs)
                    logger.info(f"[PARAM-ATTACH] Attached {len(request.atomic_parameters)} parameters for key '{matching_key}' to request.")
                else:
                    request.atomic_parameters = []
                    logger.info("[PARAM-ATTACH] No matchingKey found; attached empty parameter list to request.")
            else:
                request.atomic_parameters = []
                logger.warning("[PARAM-ATTACH] Parameter model not available; attached empty parameter list to request.")

            if executescript_name:
                cls = ATOMIC_SERVICE_REGISTRY.get(executescript_name)
                print(f"[DEBUG] DoseRequestController: executescript_name={executescript_name}, cls={cls}")
                if cls and hasattr(cls, 'execute_and_save'):
                    print(f"[DEBUG] DoseRequestController: Executing atomic service {executescript_name}")
                    # Save the request and instruction to the RequestLog model before executing the atomic service
                    try:
                        from dose.models.request_log import RequestLog
                        RequestLog.objects.create(
                            user=getattr(request, 'user', None),
                            tenant=getattr(request, 'tenant', None),
                            path=getattr(request, 'path', ''),
                            method=getattr(request, 'method', ''),
                            body={
                                'instruction': str(instruction_row),
                                'request_data': {
                                    'GET': dict(request.GET),
                                    'POST': dict(request.POST),
                                    'headers': dict(request.headers),
                                }
                            }
                        )
                        logger.info('[RequestLog] Saved request and instruction to RequestLog.')
                    except Exception as e:
                        logger.warning(f'[RequestLog] Failed to save request log: {e}')
                    # Execute the atomic service and capture the result
                    atomic_result = cls.execute_and_save(request, instruction_row)
            # Save atomic service result to CallBackData if flag is set
            if hasattr(instruction_row, 'save_callbackdata') and instruction_row.save_callbackdata:
                print("[DEBUG] CALLBACKDATA BLOCK REACHED for instruction:", instruction_row)
                print("[DEBUG] atomic_result:", atomic_result)
                print("[DEBUG] tenant:", getattr(request, 'tenant', None))
                logger.info(f"[DEBUG] Entering callbackdata save block for instruction: {instruction_row}, atomic_result: {atomic_result}, tenant: {getattr(request, 'tenant', None)}")
                import json
                logger.info(f"[CALLBACKDATA-DEBUG] atomic_result before save: {repr(atomic_result)}")
                logger.info(f"[CALLBACKDATA-DEBUG] request.atomic_parameters before save: {repr(getattr(request, 'atomic_parameters', None))}")
                # Set default description if missing or null
                description = getattr(instruction_row, 'description', None)
                if not description or description.strip().lower() == 'null':
                    if atomic_result:
                        description = 'AtomicService1 was successful'
                    else:
                        description = 'AtomicService1 was not successful'
                # ...existing code for saving CallBackData, use description variable...
                if not atomic_result:
                    atomic_result = "Request processed, no atomic service result."
                # Try to serialize atomic_result to JSON if possible
                try:
                    callbackdata_json = json.dumps(atomic_result) if not isinstance(atomic_result, str) else atomic_result
                except Exception:
                    callbackdata_json = str(atomic_result)
                logger.info("[CALLBACKDATA] About to save callbackdata: %s", callbackdata_json)
                # Save parameters as JSON (from request.atomic_parameters)
                try:
                    import datetime
                    from django.db.models import Model
                    params_json = []
                    if hasattr(request, 'atomic_parameters') and request.atomic_parameters:
                        # Convert model instances to dicts, handle datetime and model serialization
                        for param in request.atomic_parameters:
                            param_dict = {}
                            for field in param._meta.fields:
                                value = getattr(param, field.name)
                                if isinstance(value, datetime.datetime):
                                    value = value.isoformat()
                                elif isinstance(value, Model):
                                    # For User or any model instance, use str(value) or value.id
                                    value = str(value)
                                param_dict[field.name] = value
                            params_json.append(param_dict)
                    import json as _json
                    params_json_str = _json.dumps(params_json)
                    logger.info("[CALLBACKDATA] About to save parameters_json: %s", params_json_str)
                    cb = CallBackData.objects.create(
                        matchingEventKey=getattr(instruction_row, 'eventKey', None),
                        description=description,
                        callbackdata=callbackdata_json,
                        parameters_json=params_json_str,
                        tenant=getattr(request, 'tenant', None)
                    )
                    logger.info("[CALLBACKDATA] Saved CallBackData id %s for instruction id %s", cb.id, instruction_row.id)
                except Exception as e:
                    logger.error("[CALLBACKDATA] Failed to save CallBackData: %s", str(e))
        response = self.get_response(request)
        return response
