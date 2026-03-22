from django.db import models
from .tenant_aware_model import TenantAwareModel
from .instruction import Instruction
from .pass_through_endpoint import PassThroughEndpoint


class MappingDirection(models.TextChoices):
    SOURCE_TO_NORMALIZED = 'SOURCE_TO_NORMALIZED', 'Source -> Normalized'
    NORMALIZED_TO_TARGET = 'NORMALIZED_TO_TARGET', 'Normalized -> Target'


class Mapping(TenantAwareModel):
    """
    Defines how to map fields from source -> normalized, or normalized -> target.
    Reusable across instructions / services. Field expressions support pipes:
        request.POST.name|strip
        request.POST.email|lower|default:None
        lookup:country_code->iso2
        now:iso
        'literal_string'
    """
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name e.g. 'Dolibarr Thirdparty -> Normalized Customer'"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        help_text="Used in instruction references"
    )
    description = models.TextField(blank=True)

    source_endpoint = models.ForeignKey(
        PassThroughEndpoint,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='outgoing_mappings',
        help_text="Optional: source system (e.g. Dolibarr passthrough)"
    )
    target_endpoint = models.ForeignKey(
        PassThroughEndpoint,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='incoming_mappings',
        help_text="Optional: target system (e.g. Odoo XML-RPC)"
    )

    direction = models.CharField(
        max_length=25,
        choices=MappingDirection.choices,
        default=MappingDirection.SOURCE_TO_NORMALIZED
    )

    field_mappings = models.JSONField(
        default=dict,
        help_text=(
            "Dict of {target_field: source_expression}. "
            "Expressions: 'request.POST.name|strip', "
            "'payload.email|lower|default:None', "
            "'lookup:country_code->iso2', 'now:iso', \"'literal'\""
        )
    )

    transformations = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "List of post-mapping rules. "
            "[{'field': 'full_address', 'expression': 'address + \", \" + zip + \" \" + town'}]"
        )
    )

    version = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = [('slug', 'direction')]
        verbose_name = 'Mapping'
        verbose_name_plural = 'Mappings'

    def __str__(self):
        return f"{self.name} ({self.get_direction_display()})"


class InstructionMapping(models.Model):
    """
    Links Instructions to one or more Mappings.
    Order matters when multiple mappings are attached (chaining).
    """
    instruction = models.ForeignKey(
        Instruction,
        on_delete=models.CASCADE,
        related_name='mappings'
    )
    mapping = models.ForeignKey(
        Mapping,
        on_delete=models.PROTECT
    )
    order = models.PositiveSmallIntegerField(
        default=1,
        help_text="Execution order when multiple mappings are attached"
    )
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        unique_together = [('instruction', 'mapping')]
        verbose_name = 'Instruction Mapping'
        verbose_name_plural = 'Instruction Mappings'

    def __str__(self):
        return f"{self.instruction} -> {self.mapping} (order={self.order})"
