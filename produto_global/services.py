import requests
import logging
from produto_global.models import ProdutoGlobal

logger = logging.getLogger(__name__)


def buscar_produto_por_ean(ean):
    """Busca produto em APIs externas e no banco global interno."""
    # 1. Verificar banco interno
    try:
        produto = ProdutoGlobal.objects.get(ean=ean)
        return {
            'found': True,
            'source': 'internal',
            'nome': produto.nome,
            'marca': produto.marca,
            'categoria': produto.categoria,
            'imagem': produto.imagem,
        }
    except ProdutoGlobal.DoesNotExist:
        pass

    # 2. Consultar OpenFoodFacts
    resultado = _buscar_openfoodfacts(ean)
    if resultado:
        _salvar_produto_global(ean, resultado, 'OpenFoodFacts')
        return resultado

    # 3. Consultar Open EAN
    resultado = _buscar_open_ean(ean)
    if resultado:
        _salvar_produto_global(ean, resultado, 'OpenEAN')
        return resultado

    return {'found': False}


def _buscar_openfoodfacts(ean):
    """Consulta API do OpenFoodFacts."""
    try:
        url = f'https://world.openfoodfacts.org/api/v0/product/{ean}.json'
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 1:
                product = data.get('product', {})
                return {
                    'found': True,
                    'source': 'OpenFoodFacts',
                    'nome': product.get('product_name', ''),
                    'marca': product.get('brands', ''),
                    'categoria': product.get('categories', '').split(',')[0].strip() if product.get('categories') else '',
                    'imagem': product.get('image_url', ''),
                }
    except Exception as e:
        logger.warning(f'OpenFoodFacts error for {ean}: {e}')
    return None


def _buscar_open_ean(ean):
    """Consulta API do Open EAN Database."""
    try:
        url = f'https://opengtindb.org/api/lookup?ean={ean}'
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('name'):
                return {
                    'found': True,
                    'source': 'OpenEAN',
                    'nome': data.get('name', ''),
                    'marca': data.get('brand', ''),
                    'categoria': data.get('category', ''),
                    'imagem': '',
                }
    except Exception as e:
        logger.warning(f'OpenEAN error for {ean}: {e}')
    return None


def _salvar_produto_global(ean, dados, fonte):
    """Salva produto no banco global para uso futuro."""
    try:
        ProdutoGlobal.objects.create(
            ean=ean,
            nome=dados.get('nome', ''),
            marca=dados.get('marca', ''),
            categoria=dados.get('categoria', ''),
            imagem=dados.get('imagem', ''),
            fonte=fonte,
        )
    except Exception as e:
        logger.warning(f'Error saving global product {ean}: {e}')
