# Config package
# Importar Celery app para que seja carregado com o Django
from .celery import app as celery_app

__all__ = ('celery_app',)
