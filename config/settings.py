"""
Django settings for PDV SaaS Cloud.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me')

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'corsheaders',
    'django_filters',
    # Local apps
    'core',
    'empresas',
    'usuarios',
    'produtos',
    'estoque',
    'vendas',
    'caixa',
    'financeiro',
    'clientes',
    'fornecedores',
    'promocoes',
    'produto_global',
    'auditoria',
    'sync',
    'relatorios',
    'assinaturas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.TenantMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

import dj_database_url

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom user model
AUTH_USER_MODEL = 'usuarios.Usuario'

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'core.authentication.TokenEmpresaAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DATETIME_FORMAT': '%d/%m/%Y %H:%M:%S',
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if not DEBUG else []

# CSRF
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'https://pvd.luizgustavo.tech,http://localhost:8037').split(',')

# Login
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

JAZZMIN_SETTINGS = {
    "site_title": "PDV Cloud Admin",
    "site_header": "PDV Nuvem",
    "site_brand": "PDV Admin",
    "site_logo": None,
    "welcome_sign": "Bem-vindo ao Painel PDV Cloud",
    "copyright": "Luiz Gustavo Tech",
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Início",  "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
    ],
    "usermenu_links": [
        {"name": "Suporte", "url": "https://pvd.luizgustavo.tech", "new_window": True, "icon": "fas fa-headset"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "empresas.Empresa": "fas fa-building",
        "empresas.PDVTerminal": "fas fa-desktop",
        "produtos.Produto": "fas fa-box",
        "produtos.Categoria": "fas fa-tags",
        "clientes.Cliente": "fas fa-user-tie",
        "vendas.Venda": "fas fa-shopping-cart",
        "vendas.ItemVenda": "fas fa-receipt",
        "caixa.SessaoCaixa": "fas fa-cash-register",
        "caixa.Sangria": "fas fa-money-bill-wave",
        "caixa.Suprimento": "fas fa-hand-holding-usd",
        "financeiro.ContaFiado": "fas fa-book",
        "financeiro.ParcelaFiado": "fas fa-file-invoice-dollar",
        "financeiro.PagamentoFiado": "fas fa-money-check-alt",
        "estoque.MovimentacaoEstoque": "fas fa-exchange-alt",
        "core.Tenant": "fas fa-sitemap",
        "assinaturas.PlanoEmpresa": "fas fa-file-contract",
        "assinaturas.Fatura": "fas fa-file-invoice-dollar",
        "assinaturas.ConfigEfi": "fas fa-cogs",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": True,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": True,
    "sidebar_disable_expand": True,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": True,
    "sidebar_nav_flat_style": True,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": True
}

