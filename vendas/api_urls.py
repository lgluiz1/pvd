from rest_framework.routers import DefaultRouter
from vendas import api_views

router = DefaultRouter()
router.register('', api_views.VendaViewSet, basename='venda')

urlpatterns = router.urls
