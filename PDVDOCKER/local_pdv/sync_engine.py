import requests
from django.utils import timezone
from local_pdv.models import ProdutoLocal, ClienteLocal, VendaLocal, ConfigLocal, SessaoCaixaLocal

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
        cloud_product_ids = []
        for p in produtos_dados:
            cloud_product_ids.append(p['id'])
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
            
        # Deletar produtos locais que não estão mais na nuvem
        produtos_removidos = ProdutoLocal.objects.exclude(id__in=cloud_product_ids).delete()[0]

        # 2. Sincronizar Clientes
        clientes_dados = data.get('clientes', [])
        clientes_sincronizados = 0
        cloud_client_ids = []
        for c in clientes_dados:
            cloud_client_ids.append(c['id'])
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
            
        # Deletar clientes locais que não estão mais na nuvem
        clientes_removidos = ClienteLocal.objects.exclude(id__in=cloud_client_ids).delete()[0]

        # 3. Sincronizar Usuários (Operadores)
        usuarios_dados = data.get('usuarios', [])
        usuarios_sincronizados = 0
        from django.contrib.auth.models import User
        for u in usuarios_dados:
            if u['username'] == 'admin':
                continue  # Protege o admin local para evitar deslogue involuntário e garantir consistência de acesso
            user_local, created = User.objects.get_or_create(username=u['username'])
            
            changed = False
            if created:
                changed = True
                
            for attr in ['first_name', 'last_name', 'email', 'is_active']:
                val = u.get(attr, '') if attr != 'is_active' else u.get(attr, True)
                if getattr(user_local, attr) != val:
                    setattr(user_local, attr, val)
                    changed = True
                    
            if user_local.password != u['password']:
                user_local.password = u['password']
                changed = True
                
            if changed:
                user_local.save()
            usuarios_sincronizados += 1

        config.ultimo_sync = timezone.now()
        config.save()

        # Puxar credenciais MP automaticamente junto com o sync
        try:
            pull_mp_config()
        except Exception:
            pass  # Nao bloquear o sync principal se MP falhar
        
        return True, f"Sincronização concluída! {produtos_sincronizados} produtos, {clientes_sincronizados} clientes e {usuarios_sincronizados} operadores sincronizados."

    except requests.exceptions.RequestException as e:
        return False, f"Erro de conexão com o servidor de nuvem: {str(e)}"


def push_sales_to_cloud():
    """Envia todas as vendas e sessoes de caixa locais pendentes para a nuvem."""
    config = get_config()
    if not config.api_token:
        return False, "Token de API não configurado."

    vendas_pendentes = VendaLocal.objects.filter(synced=False)
    sessoes_pendentes = SessaoCaixaLocal.objects.filter(synced=False)
    
    if not vendas_pendentes.exists() and not sessoes_pendentes.exists():
        return True, "Nada pendente para sincronizar."

    url = f"{config.api_cloud_url.rstrip('/')}/api/sync/upload/"
    headers = {
        "Authorization": f"Token {config.api_token}",
        "Content-Type": "application/json"
    }

    # Serializar sessoes pendentes
    payload_sessoes = []
    for s in sessoes_pendentes:
        payload_sessoes.append({
            "local_id": str(s.id),
            "operador_username": s.operador_username,
            "abertura": s.abertura.isoformat(),
            "fechamento": s.fechamento.isoformat() if s.fechamento else None,
            "valor_abertura": float(s.valor_abertura) if s.valor_abertura else 0.0,
            "valor_fechamento": float(s.valor_fechamento) if s.valor_fechamento is not None else 0.0,
            "status": s.status,
            "observacoes": s.observacoes
        })

    # Serializar vendas pendentes
    payload_vendas = []
    for v in vendas_pendentes:
        itens = []
        for item in v.itens.all():
            itens.append({
                "produto_id": str(item.produto.id),
                "quantidade": float(item.quantidade),
                "valor_unitario": float(item.valor_unitario),
                "total": float(item.total),
            })
        
        payload_vendas.append({
            "local_id": str(v.id),
            "sessao_id": str(v.sessao.id) if v.sessao else None,
            "total": float(v.total),
            "metodo_pagamento": v.metodo_pagamento,
            "status": v.status,
            "cliente_id": str(v.cliente.id) if v.cliente else None,
            "created_at": v.created_at.isoformat(),
            "itens": itens
        })

    try:
        response = requests.post(url, json={"vendas": payload_vendas, "sessoes_caixa": payload_sessoes}, headers=headers, timeout=10)
        if response.status_code == 200:
            # Marcar como sincronizado no local
            vendas_pendentes.update(synced=True)
            sessoes_pendentes.update(synced=True)
            return True, f"Sincronização OK: {vendas_pendentes.count()} vendas e {sessoes_pendentes.count()} sessoes."
        else:
            return False, f"Nuvem recusou o sincronismo: {response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"Sem internet ou erro ao sincronizar vendas: {str(e)}"


def pull_mp_config():
    """Puxa configuracoes do Mercado Pago do Cloud e salva localmente."""
    config = get_config()
    if not config.api_token:
        return False, "Token de API nao configurado."

    url = f"{config.api_cloud_url.rstrip('/')}/api/sync/mp-config/"
    headers = {
        "Authorization": f"Token {config.api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False, f"Erro ao buscar config MP ({response.status_code})"

        data = response.json()
        token_mp = data.get('mp_access_token', '')

        config.mp_access_token = token_mp
        config.empresa_nome = data.get('empresa_nome', config.empresa_nome)
        config.empresa_cnpj = data.get('empresa_cnpj', config.empresa_cnpj)
        config.empresa_telefone = data.get('empresa_telefone', config.empresa_telefone)
        config.empresa_endereco = data.get('empresa_endereco', config.empresa_endereco)
        config.save()

        if token_mp:
            return True, "Sincronizado com sucesso (com MP)!"
        else:
            return True, "Sincronizado com sucesso (sem MP)."

    except requests.exceptions.RequestException as e:
        return False, f"Erro de conexao: {str(e)}"
