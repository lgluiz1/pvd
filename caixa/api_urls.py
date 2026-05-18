from rest_framework.routers import DefaultRouter
from caixa import api_views

router = DefaultRouter()
router.register('', api_views.SessaoCaixaViewSet, basename='sessao-caixa')
urlpatterns = router.urls
