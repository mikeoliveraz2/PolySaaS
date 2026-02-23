from rest_framework import viewsets
from drf_yasg.utils import swagger_auto_schema
from dose.models import UserProfile
from .models import (
    Tenant, MLEngine, MLTaxonomy, MLDataset, CallBackData, Instruction, Task,
    NavigationPanel, NavigationItem, DashboardButton, IgnorePath
)
from .serializers import (
    TenantSerializer, UserProfileSerializer, MLEngineSerializer, MLTaxonomySerializer, MLDatasetSerializer,
    CallBackDataSerializer, InstructionSerializer, TaskSerializer, NavigationPanelSerializer,
    NavigationItemSerializer, DashboardButtonSerializer, IgnorePathSerializer
)

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

    @swagger_auto_schema(operation_description="List all tenants.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a tenant by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    @swagger_auto_schema(operation_description="List all user profiles.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a user profile by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class MLEngineViewSet(viewsets.ModelViewSet):
    queryset = MLEngine.objects.all()
    serializer_class = MLEngineSerializer

    @swagger_auto_schema(operation_description="List all ML engines.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve an ML engine by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class MLTaxonomyViewSet(viewsets.ModelViewSet):
    queryset = MLTaxonomy.objects.all()
    serializer_class = MLTaxonomySerializer

    @swagger_auto_schema(operation_description="List all ML taxonomies.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve an ML taxonomy by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class MLDatasetViewSet(viewsets.ModelViewSet):
    queryset = MLDataset.objects.all()
    serializer_class = MLDatasetSerializer

    @swagger_auto_schema(operation_description="List all ML datasets.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve an ML dataset by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class CallBackDataViewSet(viewsets.ModelViewSet):
    queryset = CallBackData.objects.all()
    serializer_class = CallBackDataSerializer

    @swagger_auto_schema(operation_description="List all callback data.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve callback data by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class InstructionViewSet(viewsets.ModelViewSet):
    queryset = Instruction.objects.all()
    serializer_class = InstructionSerializer

    @swagger_auto_schema(operation_description="List all instructions.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve an instruction by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @swagger_auto_schema(operation_description="List all tasks.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a task by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class NavigationPanelViewSet(viewsets.ModelViewSet):
    queryset = NavigationPanel.objects.all()
    serializer_class = NavigationPanelSerializer

    @swagger_auto_schema(operation_description="List all navigation panels.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a navigation panel by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class NavigationItemViewSet(viewsets.ModelViewSet):
    queryset = NavigationItem.objects.all()
    serializer_class = NavigationItemSerializer

    @swagger_auto_schema(operation_description="List all navigation items.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a navigation item by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class DashboardButtonViewSet(viewsets.ModelViewSet):
    queryset = DashboardButton.objects.all()
    serializer_class = DashboardButtonSerializer

    @swagger_auto_schema(operation_description="List all dashboard buttons.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve a dashboard button by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

class IgnorePathViewSet(viewsets.ModelViewSet):
    queryset = IgnorePath.objects.all()
    serializer_class = IgnorePathSerializer

    @swagger_auto_schema(operation_description="List all ignore paths.")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(operation_description="Retrieve an ignore path by ID.")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


from .models import PassThroughEndpoint
from .serializers import PassThroughEndpointSerializer

class PassThroughEndpointViewSet(viewsets.ModelViewSet):
    """
    CRUD API for Pass Through Endpoints.

    Each endpoint represents an external service (Nextcloud, Liferay, etc.)
    that PolySaaS proxies and integrates. Responses include computed proxy_url,
    admin_url, and polysniffer_url links.
    """
    queryset = PassThroughEndpoint.objects.all().order_by('menu_sort_order')
    serializer_class = PassThroughEndpointSerializer

    @swagger_auto_schema(
        operation_description="List all passthrough endpoints with proxy links.",
        tags=['Passthrough Endpoints']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a passthrough endpoint by ID, including proxy and PolySniffer URLs.",
        tags=['Passthrough Endpoints']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new passthrough endpoint for an external service.",
        tags=['Passthrough Endpoints']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a passthrough endpoint.",
        tags=['Passthrough Endpoints']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a passthrough endpoint.",
        tags=['Passthrough Endpoints']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a passthrough endpoint.",
        tags=['Passthrough Endpoints']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
