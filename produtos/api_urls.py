from rest_framework.routers import DefaultRouter
from produtos import api_views

router = DefaultRouter()
router.register('', api_views.ProdutoViewSet, basename='produto')

urlpatterns = router.urls
