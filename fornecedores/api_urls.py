from rest_framework.routers import DefaultRouter
from fornecedores import api_views
router = DefaultRouter()
router.register('', api_views.FornecedorViewSet, basename='fornecedor')
urlpatterns = router.urls
