from rest_framework.routers import DefaultRouter
from promocoes import api_views
router = DefaultRouter()
router.register('', api_views.PromocaoViewSet, basename='promocao')
urlpatterns = router.urls
