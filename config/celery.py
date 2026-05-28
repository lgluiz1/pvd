"""
Configuracao do Celery para o PDV Cloud.
Usa Redis como broker e backend.
"""
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Ler configuracoes do Django settings com prefixo CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descobrir tasks automaticamente em todos os apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Task de debug para testar se o Celery esta funcionando."""
    print(f'Request: {self.request!r}')
