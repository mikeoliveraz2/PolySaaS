#from symbol import parameters
#from django.conf.urls import include, url
from django.urls import path
from . import views 

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
app_name = 'parameter'
urlpatterns = [
    path('', views.ParametersIndexView.as_view(), name='index'),
    path('<int:pk>/', views.ParametersDetailView.as_view(), name='detail'),
    path('<int:pk>/results/', views.ParametersResultsView.as_view(), name='results'),
    
]

