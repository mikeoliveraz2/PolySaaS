from rest_framework import serializers
from dose.models import Subscription, AtomicService
class AtomicServiceSerializer(serializers.ModelSerializer):
    config_json = serializers.JSONField(default={'name': 'value'})
    class Meta:
        model = AtomicService
        fields = '__all__'
class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
from .models import (
    Tenant, UserProfile, MLEngine, MLTaxonomy, MLDataset, CallBackData, Instruction, Task,
    NavigationPanel, NavigationItem, DashboardButton, IgnorePath, RequestLog, ErrorLog
)

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class MLEngineSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLEngine
        fields = '__all__'

class MLTaxonomySerializer(serializers.ModelSerializer):
    class Meta:
        model = MLTaxonomy
        fields = '__all__'

class MLDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLDataset
        fields = '__all__'

class CallBackDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallBackData
        fields = '__all__'

class InstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instruction
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

class NavigationPanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavigationPanel
        fields = '__all__'

class NavigationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavigationItem
        fields = '__all__'

class DashboardButtonSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardButton
        fields = '__all__'


class IgnorePathSerializer(serializers.ModelSerializer):
    class Meta:
        model = IgnorePath
        fields = '__all__'

class RequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestLog
        fields = '__all__'

class ErrorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorLog
        fields = '__all__'

from .models import PassThroughEndpoint

class PassThroughEndpointSerializer(serializers.ModelSerializer):
    proxy_url = serializers.SerializerMethodField()
    admin_url = serializers.SerializerMethodField()
    polysniffer_url = serializers.SerializerMethodField()

    class Meta:
        model = PassThroughEndpoint
        fields = [
            'id', 'is_enabled', 'provider', 'endpoint_url', 'description',
            'trigger_path', 'menu_title', 'menu_icon', 'menu_sort_order',
            'show_in_menu', 'passthrough_type', 'integration_mode',
            'api_endpoint', 'api_auth_type', 'api_key_header',
            'inject_proxy_script', 'created_at',
            'proxy_url', 'admin_url', 'polysniffer_url',
        ]
        read_only_fields = ['created_at', 'proxy_url', 'admin_url', 'polysniffer_url']

    def get_proxy_url(self, obj):
        return f'/admin/polysniffer/proxy/{obj.id}/'

    def get_admin_url(self, obj):
        return f'/admin/dose/passthroughendpoint/{obj.id}/change/'

    def get_polysniffer_url(self, obj):
        return f'/admin/polysniffer/capture/{obj.id}/'

from rest_framework import serializers



    # Serializer to match the subscribe form fields
class SubscriptionCreateSerializer(serializers.Serializer):
    tenant_name = serializers.CharField(max_length=255)
    tenant_shortname = serializers.CharField(max_length=32)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128)
    email = serializers.EmailField()
    zip = serializers.CharField(max_length=10)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    card_name = serializers.CharField(max_length=255)
    stripe_token = serializers.CharField(max_length=255)
