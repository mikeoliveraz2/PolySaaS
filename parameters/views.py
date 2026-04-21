from django.db.models import Q
from django.views import generic

from parameters.models import Parameter


def _parameters_visible_queryset(request):
    qs = Parameter.objects.all()
    user = getattr(request, "user", None)
    if user and user.is_superuser:
        return qs
    return qs.filter(Q(encrypted_payload__isnull=True) | Q(encrypted_payload=""))


class ParametersIndexView(generic.ListView):
    template_name = "parametersindex.html"
    context_object_name = "latest_parameter_list"

    def get_queryset(self):
        return _parameters_visible_queryset(self.request)


class ParametersDetailView(generic.DetailView):
    model = Parameter
    template_name = "parameters/parametersdetail.html"

    def get_queryset(self):
        return _parameters_visible_queryset(self.request)


class ParametersResultsView(generic.DetailView):
    model = Parameter
    template_name = "parameters/parametersresults.html"

    def get_queryset(self):
        return _parameters_visible_queryset(self.request)

