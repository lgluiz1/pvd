from rest_framework.routers import DefaultRouter
from clientes import api_views
router = DefaultRouter()
router.register('', api_views.ClienteViewSet, basename='cliente')
urlpatterns = router.urls
