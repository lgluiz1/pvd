import requests
from django.utils import timezone
from local_pdv.models import ProdutoLocal, ClienteLocal, VendaLocal, ConfigLocal

def get_config():
    """Recupera ou cria as configurações de API do POS Local."""
    config = ConfigLocal.objects.first()
    if not config:
        import os
        config = ConfigLocal.objects.create(
            api_token=os.environ.get('API_TOKEN', 'your_copied_api_token_here'),
            api_cloud_url=os.environ.get('API_CLOUD_URL', 'https://pvd.luizgustavo.tech')
        )
    return config

def pull_snapshot_from_cloud():
    """Busca o snapshot completo da Nuvem (SaaS) e sincroniza os cadastros locais."""
    config = get_config()
    if not config.api_token:
        return False, "Token de API não configurado."

    url = f"{config.api_cloud_url.rstrip('/')}/api/sync/snapshot/"
    headers = {
        "Authorization": f"Token {config.api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False, f"Erro na nuvem ({response.status_code}): {response.text}"
        
        data = response.json()
        
        # 1. Sincronizar Produtos
        produtos_dados = data.get('produtos', [])
        produtos_sincronizados = 0
        for p in produtos_dados:
            ProdutoLocal.objects.update_or_create(
                id=p['id'],
                defaults={
                    'nome': p['nome'],
                    'codigo_barras': p.get('codigo_barras'),
                    'codigo_interno': p.get('codigo_interno'),
                    'valor_venda': p['valor_venda'],
                    'unidade_medida': p.get('unidade_medida', 'un'),
                    'quantidade': p.get('quantidade', 0),
                    'estoque_minimo': p.get('estoque_minimo', 5),
                }
            )
            produtos_sincronizados += 1

        # 2. Sincronizar Clientes
        clientes_dados = data.get('clientes', [])
        clientes_sincronizados = 0
        for c in clientes_dados:
            ClienteLocal.objects.update_or_create(
                id=c['id'],
                defaults={
                    'nome': c['nome'],
                    'nfc_uid': c.get('nfc_uid'),
                    'limite_credito': c.get('limite_credito', 0),
                    'saldo_devedor': c.get('saldo_devedor', 0),
                }
            )
            clientes_sincronizados += 1

        # 3. Sincronizar Usuários (Operadores)
        usuarios_dados = data.get('usuarios', [])
        usuarios_sincronizados = 0
        from django.contrib.auth.models import User
        for u in usuarios_dados:
            user_local, created = User.objects.update_or_create(
                username=u['username'],
                defaults={
                    'first_name': u.get('first_name', ''),
                    'last_name': u.get('last_name', ''),
                    'email': u.get('email', ''),
                    'is_active': u.get('is_active', True),
                }
            )
            # Define o hash da senha vindo diretamente do Cloud
            user_local.password = u['password']
            user_local.save()
            usuarios_sincronizados += 1

        config.ultimo_sync = timezone.now()
        config.save()
        
        return True, f"Sincronização concluída! {produtos_sincronizados} produtos, {clientes_sincronizados} clientes e {usuarios_sincronizados} operadores sincronizados."

    except requests.exceptions.RequestException as e:
        return False, f"Erro de conexão com o servidor de nuvem: {str(e)}"


def push_sales_to_cloud():
    """Envia todas as vendas locais pendentes para a nuvem."""
    config = get_config()
    if not config.api_token:
        return False, "Token de API não configurado."

    vendas_pendentes = VendaLocal.objects.filter(synced=False)
    if not vendas_pendentes.exists():
        return True, "Nenhuma venda pendente para sincronizar."

    url = f"{config.api_cloud_url.rstrip('/')}/api/sync/upload/"
    headers = {
        "Authorization": f"Token {config.api_token}",
        "Content-Type": "application/json"
    }

    # Serializar vendas pendentes
    payload = []
    for v in vendas_pendentes:
        itens = []
        for item in v.itens.all():
            itens.append({
                "produto_id": item.produto.id,
                "quantidade": float(item.quantidade),
                "valor_unitario": float(item.valor_unitario),
                "total": float(item.total),
            })
        
        payload.append({
            "local_id": str(v.id),
            "total": float(v.total),
            "metodo_pagamento": v.metodo_pagamento,
            "cliente_id": v.cliente.id if v.cliente else None,
            "created_at": v.created_at.isoformat(),
            "itens": itens
        })

    try:
        response = requests.post(url, json={"vendas": payload}, headers=headers, timeout=10)
        if response.status_code == 200:
            # Marcar como sincronizado no local
            vendas_pendentes.update(synced=True)
            return True, f"{vendas_pendentes.count()} vendas pendentes enviadas com sucesso!"
        else:
            return False, f"Nuvem recusou o sincronismo: {response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"Sem internet ou erro ao sincronizar vendas: {str(e)}"
