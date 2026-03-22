"""
Management command to validate a Mapping record against sample data.

Usage:
  # Test a mapping by slug with inline JSON payload:
  python manage.py test_mapping --slug dolibarr-thirdparty-post-to-normalized \
      --payload '{"name":"Test Co","email":"test@example.com","phone":"555-1234"}'

  # Test with payload from a JSON file:
  python manage.py test_mapping --slug dolibarr-thirdparty-post-to-normalized \
      --file sample_post.json

  # Test all mappings attached to an Instruction (by ID or requestpath):
  python manage.py test_mapping --instruction-id 5 \
      --payload '{"name":"Test Co","email":"test@example.com"}'

  python manage.py test_mapping --instruction-path /societe/card.php \
      --payload '{"name":"Test Co","email":"test@example.com"}'

  # Show all registered mappings:
  python manage.py test_mapping --list
"""
import json
import sys
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Validate a Mapping or Instruction chain against sample data'

    def add_arguments(self, parser):
        parser.add_argument('--slug', type=str, help='Mapping slug to test')
        parser.add_argument('--payload', type=str, help='Inline JSON payload')
        parser.add_argument('--file', type=str, help='Path to JSON file with sample payload')
        parser.add_argument('--instruction-id', type=int, help='Test all mappings on an Instruction by ID')
        parser.add_argument('--instruction-path', type=str, help='Test all mappings on an Instruction by requestpath')
        parser.add_argument('--list', action='store_true', help='List all Mapping records')
        parser.add_argument('--verbose', action='store_true', help='Show full expression trace')

    def handle(self, *args, **options):
        from dose.models import Mapping, InstructionMapping, Instruction
        from dose.services.mapping_engine import (
            apply_mapping, resolve_expression,
            apply_mappings_for_instruction, build_context_from_payload,
        )

        if options['list']:
            self._list_mappings(Mapping)
            return

        payload = self._load_payload(options)

        if options['slug']:
            self._test_single_mapping(Mapping, options['slug'], payload, options['verbose'])
        elif options['instruction_id'] or options['instruction_path']:
            self._test_instruction_chain(
                Instruction, InstructionMapping, payload,
                options['instruction_id'], options['instruction_path'],
                options['verbose']
            )
        else:
            raise CommandError(
                'Provide --slug, --instruction-id, --instruction-path, or --list'
            )

    def _load_payload(self, options):
        payload_str = options.get('payload')
        file_path = options.get('file')

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                raise CommandError(f'Could not load file {file_path}: {e}')

        if payload_str:
            try:
                return json.loads(payload_str)
            except json.JSONDecodeError as e:
                raise CommandError(f'Invalid JSON payload: {e}')

        if not options.get('list'):
            return {}

        return {}

    def _list_mappings(self, Mapping):
        mappings = Mapping.objects.all().order_by('direction', 'name')
        if not mappings.exists():
            self.stdout.write(self.style.WARNING('No Mapping records found.'))
            return

        self.stdout.write(self.style.SUCCESS(f'\n  {mappings.count()} Mapping record(s):\n'))
        self.stdout.write(f'  {"Slug":<45} {"Direction":<25} {"Active":<8} {"Fields":<6} Name')
        self.stdout.write(f'  {"-"*45} {"-"*25} {"-"*8} {"-"*6} {"-"*30}')

        for m in mappings:
            field_count = len(m.field_mappings or {})
            active = 'Y' if m.is_active else 'N'
            self.stdout.write(
                f'  {m.slug:<45} {m.get_direction_display():<25} {active:<8} {field_count:<6} {m.name}'
            )

        # Show InstructionMapping links
        from dose.models import InstructionMapping
        links = InstructionMapping.objects.select_related('instruction', 'mapping').all()
        if links.exists():
            self.stdout.write(self.style.SUCCESS(f'\n  {links.count()} InstructionMapping link(s):\n'))
            for link in links:
                status = 'enabled' if link.enabled else 'DISABLED'
                self.stdout.write(
                    f'  Instruction "{link.instruction.requestpath}" '
                    f'-> Mapping "{link.mapping.slug}" (order={link.order}, {status})'
                )
        self.stdout.write('')

    def _test_single_mapping(self, Mapping, slug, payload, verbose):
        from dose.services.mapping_engine import apply_mapping, build_context_from_payload

        try:
            mapping = Mapping.objects.get(slug=slug)
        except Mapping.DoesNotExist:
            raise CommandError(f'Mapping with slug "{slug}" not found')

        self.stdout.write(self.style.SUCCESS(f'\n  Testing Mapping: {mapping.name}'))
        self.stdout.write(f'  Slug: {mapping.slug}')
        self.stdout.write(f'  Direction: {mapping.get_direction_display()}')
        self.stdout.write(f'  Active: {mapping.is_active}')

        if not payload:
            self.stdout.write(self.style.WARNING(
                '\n  No payload provided. Showing field_mappings expressions only:\n'
            ))
            for target, expr in (mapping.field_mappings or {}).items():
                self.stdout.write(f'    {target:<30} <- {expr}')
            return

        self.stdout.write(f'\n  Input payload ({len(payload)} fields):')
        for k, v in payload.items():
            self.stdout.write(f'    {k}: {v!r}')

        if verbose and mapping.field_mappings:
            mapping.field_mappings['_debug'] = 'true'

        context = self._build_test_context(mapping, payload)
        result = apply_mapping(mapping, context)

        self.stdout.write(self.style.SUCCESS(f'\n  Output ({len(result)} fields):'))
        for k, v in result.items():
            marker = ''
            if v is None:
                marker = self.style.WARNING(' (None)')
            elif v == '':
                marker = self.style.WARNING(' (empty)')
            self.stdout.write(f'    {k:<30} = {v!r}{marker}')

        unmapped_keys = set(payload.keys()) - self._extract_source_fields(mapping.field_mappings or {})
        if unmapped_keys:
            self.stdout.write(self.style.WARNING(f'\n  Payload fields NOT referenced in mapping:'))
            for k in sorted(unmapped_keys):
                self.stdout.write(f'    - {k}')

        self.stdout.write('')

    def _test_instruction_chain(self, Instruction, InstructionMapping, payload,
                                 instr_id, instr_path, verbose):
        if instr_id:
            try:
                instruction = Instruction.objects.get(id=instr_id)
            except Instruction.DoesNotExist:
                raise CommandError(f'Instruction with id={instr_id} not found')
        else:
            instructions = Instruction.objects.filter(requestpath=instr_path)
            if not instructions.exists():
                raise CommandError(f'No Instruction with requestpath="{instr_path}"')
            instruction = instructions.first()

        links = InstructionMapping.objects.filter(
            instruction=instruction, enabled=True
        ).select_related('mapping').order_by('order')

        self.stdout.write(self.style.SUCCESS(
            f'\n  Testing Instruction: {instruction.requestpath} '
            f'({instruction.requestmethod or "ANY"})'
        ))
        self.stdout.write(f'  Execute script: {instruction.executescript}')
        self.stdout.write(f'  Attached mappings: {links.count()}')

        if not links.exists():
            self.stdout.write(self.style.WARNING(
                '  No InstructionMappings attached. Services will use fallback logic.'
            ))
            return

        if not payload:
            self.stdout.write(self.style.WARNING('\n  No payload provided. Listing attached mappings:\n'))
            for link in links:
                self.stdout.write(
                    f'    [{link.order}] {link.mapping.slug} '
                    f'({link.mapping.get_direction_display()})'
                )
            return

        cumulative = {}

        for link in links:
            mapping = link.mapping
            self.stdout.write(self.style.SUCCESS(
                f'\n  --- Step {link.order}: {mapping.slug} ({mapping.get_direction_display()}) ---'
            ))

            if verbose and mapping.field_mappings:
                mapping.field_mappings['_debug'] = 'true'

            step_payload = cumulative if cumulative else payload
            context = self._build_test_context(mapping, step_payload)

            from dose.services.mapping_engine import apply_mapping as do_apply
            step_result = do_apply(mapping, context)
            cumulative.update(step_result)

            for k, v in step_result.items():
                self.stdout.write(f'    {k:<30} = {v!r}')

            context['payload'] = cumulative

        self.stdout.write(self.style.SUCCESS(f'\n  Final merged output ({len(cumulative)} fields):'))
        for k, v in cumulative.items():
            self.stdout.write(f'    {k:<30} = {v!r}')
        self.stdout.write('')

    def _build_test_context(self, mapping, payload):
        """
        Build a context dict that matches what the mapping expects.
        SOURCE_TO_NORMALIZED mappings use request.POST.xxx, so we simulate
        a mock request with a POST dict. NORMALIZED_TO_TARGET just uses payload.
        """
        from dose.services.mapping_engine import build_context_from_payload

        context = build_context_from_payload(payload)

        has_request_refs = any(
            isinstance(expr, str) and 'request.' in expr
            for expr in (mapping.field_mappings or {}).values()
        )

        if has_request_refs:
            class MockQueryDict(dict):
                def getlist(self, key, default=None):
                    val = self.get(key)
                    if val is None:
                        return default or []
                    return [val] if not isinstance(val, list) else val

            class MockRequest:
                def __init__(self, data):
                    self.POST = MockQueryDict(data)
                    self.GET = MockQueryDict()
                    self.method = 'POST'
                    self.path = '/test'

            context['request'] = MockRequest(payload)
            self.stdout.write(
                '  (Simulating request.POST context for SOURCE_TO_NORMALIZED mapping)'
            )

        return context

    def _extract_source_fields(self, field_mappings: dict) -> set:
        """Extract payload field names referenced in expressions."""
        fields = set()
        for expr in field_mappings.values():
            if not isinstance(expr, str):
                continue
            parts = expr.split('|')
            path = parts[0].strip()
            if path.startswith('payload.'):
                segments = path.split('.')
                if len(segments) >= 2:
                    fields.add(segments[1])
            elif path.startswith('request.POST.'):
                segments = path.split('.')
                if len(segments) >= 3:
                    fields.add(segments[2])
        return fields
