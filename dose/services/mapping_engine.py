"""
Mapping Engine - Resolves field_mappings expressions and applies transformations.

Expression syntax:
    'literal_string'          -> returns the literal string
    now:iso                   -> current datetime in ISO format
    request.POST.fieldname    -> resolves from Django request POST data
    request.GET.fieldname     -> resolves from Django request GET data
    payload.fieldname         -> resolves from a dict payload (MQ message body)
    payload.nested.field      -> dot-notation for nested dicts

Pipe operators (chained left to right):
    |strip                    -> str.strip()
    |lower                    -> str.lower()
    |upper                    -> str.upper()
    |default:value            -> fallback if resolved value is None or empty
    |bool                     -> truthy check -> True/False
    |bool:yes:no              -> truthy -> 'yes', falsy -> 'no'
    |int                      -> cast to int
    |int:trueval:falseval     -> truthy -> int(trueval), falsy -> int(falseval)
    |prefix:PREFIX-           -> prepend string
    |suffix:-SUFFIX           -> append string
    |truncate:120             -> truncate string to max length
    |email                    -> validate email format, None if invalid
    |if:path.to.check         -> return value only if another field is truthy
    |coalesce:path.fallback   -> use value, or resolve fallback path if empty
"""
import logging
import datetime
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def apply_mapping(mapping_record, context: dict) -> dict:
    """
    Apply a Mapping's field_mappings to a context dict and return the result.

    Args:
        mapping_record: Mapping model instance (has .field_mappings and .transformations)
        context: dict with keys like 'request', 'payload', etc.

    Returns:
        dict of resolved {target_field: value}
    """
    field_mappings = mapping_record.field_mappings or {}
    debug = field_mappings.get('_debug', '') == 'true'
    result = {}

    if debug:
        context_keys = {k: type(v).__name__ for k, v in context.items()}
        logger.info(f"[MappingEngine:DEBUG] Mapping '{mapping_record.slug}' context keys: {context_keys}")

    for target_field, expression in field_mappings.items():
        if target_field == '_debug':
            continue
        try:
            value = resolve_expression(expression, context)
            result[target_field] = value
            if debug:
                logger.info(f"[MappingEngine:DEBUG]   {target_field} = {expression!r} -> {value!r}")
        except Exception as e:
            logger.warning(f"[MappingEngine] Error resolving '{target_field}': {expression} -> {e}")
            result[target_field] = None

    transformations = mapping_record.transformations or []
    for transform in transformations:
        try:
            apply_transformation(transform, result)
        except Exception as e:
            logger.warning(f"[MappingEngine] Error in transformation {transform}: {e}")

    return result


def resolve_expression(expression: str, context: dict) -> Any:
    """
    Resolve a single field expression against the context.
    Supports literals, paths, and pipe operators.
    """
    if not expression or not isinstance(expression, str):
        return expression

    expression = expression.strip()

    # Literal string: 'some value'
    if expression.startswith("'") and expression.endswith("'"):
        return expression[1:-1]

    # now:iso
    if expression == 'now:iso':
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Split on pipes, but not pipes inside quotes
    parts = _split_pipes(expression)
    path = parts[0].strip()
    pipes = [p.strip() for p in parts[1:]]

    # Literal as first segment: 'some string'|pipe|pipe
    if path.startswith("'") and path.endswith("'"):
        value = path[1:-1]
    else:
        value = _resolve_path(path, context)

    for pipe in pipes:
        value = _apply_pipe(pipe, value, context)

    return value


def _split_pipes(expression: str) -> list:
    """Split expression on | but respect quoted strings."""
    parts = []
    current = []
    in_quotes = False
    for char in expression:
        if char == "'" or char == '"':
            in_quotes = not in_quotes
            current.append(char)
        elif char == '|' and not in_quotes:
            parts.append(''.join(current))
            current = []
        else:
            current.append(char)
    parts.append(''.join(current))
    return parts


def _resolve_path(path: str, context: dict) -> Any:
    """
    Resolve a dotted path against the context.
    Supports: request.POST.field, request.GET.field, payload.field, payload.nested.field
    """
    segments = path.split('.')

    if not segments:
        return None

    root = segments[0]
    rest = segments[1:]

    obj = context.get(root)
    if obj is None:
        return None

    for segment in rest:
        if obj is None:
            return None

        # Django QueryDict (request.POST, request.GET)
        if hasattr(obj, 'get') and hasattr(obj, 'getlist'):
            obj = obj.get(segment)
        # Regular dict
        elif isinstance(obj, dict):
            obj = obj.get(segment)
        # Object attribute
        elif hasattr(obj, segment):
            obj = getattr(obj, segment)
        else:
            return None

    return obj


_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def _apply_pipe(pipe: str, value: Any, context: dict = None) -> Any:
    """Apply a single pipe operator to a value."""
    if pipe == 'strip':
        return value.strip() if isinstance(value, str) else value

    if pipe == 'lower':
        return value.lower() if isinstance(value, str) else value

    if pipe == 'upper':
        return value.upper() if isinstance(value, str) else value

    # |int  or  |int:trueval:falseval
    if pipe == 'int' or pipe.startswith('int:'):
        parts = pipe.split(':', 2)
        if len(parts) == 3:
            truthy_val, falsy_val = parts[1], parts[2]
            try:
                return int(truthy_val) if value else int(falsy_val)
            except (ValueError, TypeError):
                return 0
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    if pipe == 'bool':
        return bool(value)

    if pipe.startswith('bool:'):
        parts = pipe.split(':', 2)
        if len(parts) == 3:
            truthy_val, falsy_val = parts[1], parts[2]
            return truthy_val if value else falsy_val
        return bool(value)

    if pipe.startswith('default:'):
        default_val = pipe[len('default:'):]
        if default_val == 'None':
            default_val = None
        if default_val == 'True':
            default_val = True
        if default_val == 'False':
            default_val = False
        if value is None or value == '':
            return default_val
        return value

    if pipe.startswith('prefix:'):
        prefix = pipe[len('prefix:'):]
        return f"{prefix}{value}" if value is not None else None

    if pipe.startswith('suffix:'):
        suffix = pipe[len('suffix:'):]
        return f"{value}{suffix}" if value is not None else None

    # |truncate:120  -> cap string length
    if pipe.startswith('truncate:'):
        try:
            max_len = int(pipe[len('truncate:'):])
            if isinstance(value, str) and len(value) > max_len:
                return value[:max_len]
        except (ValueError, TypeError):
            pass
        return value

    # |email  -> validate email format, return None if invalid
    if pipe == 'email':
        if isinstance(value, str) and _EMAIL_RE.match(value.strip()):
            return value.strip()
        return None

    # |if:path.to.check  -> return value only when another context field is truthy
    if pipe.startswith('if:'):
        condition_path = pipe[len('if:'):]
        if context:
            check = _resolve_path(condition_path, context)
            return value if check else None
        return value

    # |coalesce:path.fallback  -> use value if non-empty, else resolve fallback path
    if pipe.startswith('coalesce:'):
        if value is not None and value != '':
            return value
        fallback_path = pipe[len('coalesce:'):]
        if context:
            return _resolve_path(fallback_path, context)
        return value

    logger.warning(f"[MappingEngine] Unknown pipe operator: {pipe}")
    return value


def apply_transformation(transform: dict, result: dict):
    """
    Apply a post-mapping transformation rule to the result dict.

    Supported forms:
        {'field': 'name', 'value': 'fixed_value'}          -> set field to fixed value
        {'field': 'full', 'concat': ['address', 'city']}   -> concatenate fields
        {'field': 'full', 'concat': ['address', 'city'], 'separator': ', '}
    """
    field = transform.get('field')
    if not field:
        return

    if 'value' in transform:
        result[field] = transform['value']
        return

    if 'concat' in transform:
        separator = transform.get('separator', ' ')
        parts = [str(result.get(f, '')) for f in transform['concat'] if result.get(f)]
        result[field] = separator.join(parts)
        return


def build_context_from_request(request) -> dict:
    """Build a mapping context dict from a Django request."""
    return {
        'request': request,
        'POST': getattr(request, 'POST', {}),
        'GET': getattr(request, 'GET', {}),
    }


def build_context_from_payload(payload: dict) -> dict:
    """Build a mapping context dict from an MQ message payload."""
    return {
        'payload': payload,
    }


def apply_mappings_for_instruction(instruction, context: dict) -> dict:
    """
    Load all active Mappings attached to an Instruction (via InstructionMapping)
    and apply them in order. Each mapping's output is merged into the result.
    """
    from dose.models import InstructionMapping

    instruction_mappings = InstructionMapping.objects.filter(
        instruction=instruction,
        enabled=True,
    ).select_related('mapping').order_by('order')

    result = {}
    for im in instruction_mappings:
        if not im.mapping.is_active:
            continue
        mapped = apply_mapping(im.mapping, context)
        result.update(mapped)
        logger.info(
            f"[MappingEngine] Applied mapping '{im.mapping.slug}' "
            f"(order={im.order}): {len(mapped)} fields"
        )

    return result
