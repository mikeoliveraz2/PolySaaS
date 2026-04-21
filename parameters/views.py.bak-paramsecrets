from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from rest_framework import permissions, renderers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from parameters.models import Parameter
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic



# class ParametersViewSet(viewsets.ModelViewSet):
#     """
#     This viewset automatically provides `list`, `create`, `retrieve`,
#     `update` and `destroy` actions.

#     Additionally we also provide an extra `highlight` action.
#     """
#     queryset = Parameter.objects.all()
#     serializer_class = ParameterSerializer

#     def perform_create(self, serializer):
#         serializer.save(owner=self.request.user)




class ParametersIndexView(generic.ListView):
    template_name = 'parametersindex.html'
    context_object_name = 'latest_parameter_list'

    def get_queryset(self):
        """
        Return the last five published instructions (not including those set to be
        published in the future).
        """
        return Parameter.objects.all


class ParametersDetailView(generic.DetailView):
    model = Parameter
    template_name = 'parameters/parametersdetail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Parameter.objects.all


class ParametersResultsView(generic.DetailView):
    model = Parameter
    template_name = 'parameters/parametersresults.html'

