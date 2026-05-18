from rest_framework.routers import DefaultRouter
from estoque import api_views

router = DefaultRouter()
router.register('', api_views.MovimentacaoViewSet, basename='movimentacao')

urlpatterns = router.urls
