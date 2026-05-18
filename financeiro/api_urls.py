from rest_framework.routers import DefaultRouter
from financeiro import api_views
router = DefaultRouter()
router.register('', api_views.ContaFiadoViewSet, basename='fiado')
urlpatterns = router.urls
