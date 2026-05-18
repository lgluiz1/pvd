from django.urls import path
from rest_framework.routers import DefaultRouter
from empresas import api_views

router = DefaultRouter()
router.register('', api_views.EmpresaViewSet, basename='empresa')

urlpatterns = router.urls
