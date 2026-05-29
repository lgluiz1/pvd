import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from local_pdv.models import ProdutoLocal, ClienteLocal, VendaLocal, ItemVendaLocal, ConfigLocal, SessaoCaixaLocal, PagamentoPix
from local_pdv.sync_engine import pull_snapshot_from_cloud, push_sales_to_cloud, get_config, pull_mp_config

def login_view(request):
    """Página de Login Offline/Local do Operador."""
    if request.user.is_authenticated:
        return redirect('caixa_home')

    # Se não houver nenhum usuário no banco local (primeiro acesso),
    # criamos um superusuário local padrão 'admin'/'admin' para permitir o login inicial e configuração.
    from django.contrib.auth.models import User
    if not User.objects.exists():
        User.objects.create_superuser('admin', 'admin@local.com', 'admin')

    erro = None
    if request.method == 'POST':
        usuario_digitado = request.POST.get('username', '').strip()
        senha_digitada = request.POST.get('password', '')

        # Autentica contra o SQLite local contendo usuários sincronizados!
        user = authenticate(request, username=usuario_digitado, password=senha_digitada)
        if user is not None:
            login(request, user)
            return redirect('caixa_home')
        else:
            erro = "Usuário ou senha inválidos. Caso seja o primeiro acesso, certifique-se de que a máquina foi sincronizada."

    return render(request, 'local_pdv/login.html', {'erro': erro})


def logout_view(request):
    """Efetua logout do caixa local."""
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def caixa_home(request):
    """Página principal do Frente de Caixa (POS)."""
    config = get_config()
    produtos = ProdutoLocal.objects.all().order_by('nome')
    clientes = ClienteLocal.objects.all().order_by('nome')
    
    # Filtra produtos com estoque baixo para alertas na tela
    produtos_estoque_baixo = [p for p in produtos if p.estoque_baixo]
    # Caixa atual
    sessao_aberta = SessaoCaixaLocal.objects.filter(operador_username=request.user.username, status='aberta').first()

    vendas_recentes = []
    if sessao_aberta:
        vendas_recentes = VendaLocal.objects.filter(sessao=sessao_aberta).order_by('-created_at')

    return render(request, 'local_pdv/caixa.html', {
        'produtos': produtos,
        'clientes': clientes,
        'config': config,
        'produtos_estoque_baixo': produtos_estoque_baixo,
        'sessao_aberta': sessao_aberta,
        'mp_configurado': config.mp_configurado,
        'vendas_recentes': vendas_recentes,
    })


@login_required(login_url='login')
def abrir_caixa(request):
    if request.method == 'POST':
        valor_abertura = request.POST.get('valor_abertura', '0').replace(',', '.')
        try:
            valor = float(valor_abertura)
        except ValueError:
            valor = 0.0

        SessaoCaixaLocal.objects.create(
            operador_username=request.user.username,
            valor_abertura=valor,
            status='aberta'
        )
    return redirect('caixa_home')


@login_required(login_url='login')
def fechar_caixa(request):
    sessao = SessaoCaixaLocal.objects.filter(operador_username=request.user.username, status='aberta').first()
    if sessao and request.method == 'POST':
        # Fechamento simples sem checar divergência complexa
        valor_informado = request.POST.get('valor_fechamento', '0').replace(',', '.')
        try:
            valor_fechamento = float(valor_informado)
        except ValueError:
            valor_fechamento = 0.0

        observacoes = request.POST.get('observacoes', '')

        sessao.valor_fechamento = valor_fechamento
        sessao.observacoes = observacoes
        sessao.fechamento = timezone.now()
        sessao.status = 'fechada'
        sessao.synced = False
        sessao.save()

        # Push immediately to cloud before logging out
        push_sales_to_cloud()

    return redirect('logout')

@login_required(login_url='login')
def ajax_validar_fechamento(request):
    """Calcula se o valor de fechamento informado é menor que as vendas em dinheiro + abertura."""
    if request.method == 'POST':
        sessao = SessaoCaixaLocal.objects.filter(operador_username=request.user.username, status='aberta').first()
        if not sessao:
            return JsonResponse({'error': 'Nenhuma sessão aberta'}, status=400)
        
        valor_informado = request.POST.get('valor_fechamento', '0').replace(',', '.')
        try:
            valor_fechamento = float(valor_informado)
        except ValueError:
            valor_fechamento = 0.0

        from django.db.models import Sum
        total_vendas_dinheiro = sessao.vendas.filter(
            status='concluida', 
            forma_pagamento='dinheiro'
        ).aggregate(total=Sum('total'))['total'] or 0.0

        total_esperado = float(sessao.valor_abertura) + float(total_vendas_dinheiro)

        if valor_fechamento < total_esperado:
            return JsonResponse({
                'warning': True, 
                'message': 'Você está fechando o caixa com valor menor que o processado na sessão. Deseja finalizar assim mesmo?'
            })
        
        return JsonResponse({'warning': False})
    return JsonResponse({'error': 'Método inválido'}, status=405)

@login_required(login_url='login')
def ajax_buscar_produto(request):
    """Busca rápida por código de barras ou código interno."""
    query = request.GET.get('query', '').strip()
    if not query:
        return JsonResponse({'error': 'Consulta vazia'}, status=400)

    try:
        # Busca por código de barras ou código interno
        produto = ProdutoLocal.objects.filter(
            codigo_barras=query
        ).first() or ProdutoLocal.objects.filter(
            codigo_interno=query
        ).first()

        if not produto:
            # Tentar busca por nome parcial
            produto = ProdutoLocal.objects.filter(nome__icontains=query).first()

        if produto:
            return JsonResponse({
                'success': True,
                'id': str(produto.id),
                'nome': produto.nome,
                'valor_venda': float(produto.valor_venda),
                'unidade_medida': produto.unidade_medida,
                'quantidade': float(produto.quantidade),
                'estoque_minimo': float(produto.estoque_minimo),
                'estoque_baixo': produto.estoque_baixo,
                'codigo_barras': produto.codigo_barras,
                'codigo_interno': produto.codigo_interno,
            })
        
        return JsonResponse({'success': False, 'error': 'Produto não cadastrado'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url='login')
def ajax_buscar_cliente_nfc(request):
    """Busca rápida de cliente offline pelo UID do Cartão NFC."""
    uid = request.GET.get('uid', '').strip()
    if not uid:
        return JsonResponse({'error': 'UID vazio'}, status=400)

    try:
        cliente = ClienteLocal.objects.filter(nfc_uid=uid).first()
        if cliente:
            return JsonResponse({
                'success': True,
                'id': str(cliente.id),
                'nome': cliente.nome,
                'limite_credito': float(cliente.limite_credito),
                'saldo_devedor': float(cliente.saldo_devedor),
                'limite_disponivel': float(cliente.limite_disponivel),
            })
        return JsonResponse({'success': False, 'error': 'Cartão NFC não cadastrado ou cliente inexistente.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
@login_required(login_url='login')
def ajax_finalizar_venda(request):
    """Salva a venda offline/localmente, debita estoque local e agenda envio ao Cloud."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método inválido'}, status=400)

    try:
        data = json.loads(request.body)
        total = data.get('total', 0)
        metodo_pagamento = data.get('metodo_pagamento')
        cliente_id = data.get('cliente_id')
        itens = data.get('itens', [])

        if not itens:
            return JsonResponse({'success': False, 'error': 'Lista de produtos vazia.'})

        # Carregar cliente se fornecido
        cliente = None
        if cliente_id:
            cliente = ClienteLocal.objects.get(id=cliente_id)
            # Se for fiado, verificar limite disponível
            if metodo_pagamento == 'fiado':
                if float(total) > float(cliente.limite_disponivel):
                    return JsonResponse({
                        'success': False, 
                        'error': f'Crédito insuficiente! Disponível: R$ {cliente.limite_disponivel:.2f}'
                    })
                # Debita o saldo devedor offline
                cliente.saldo_devedor += total
                cliente.save()

        # Validar existência dos itens antes de criar a venda
        for it in itens:
            try:
                prod_local = ProdutoLocal.objects.get(id=it['id'])
            except ProdutoLocal.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Produto com ID {it["id"]} não encontrado no banco local.'})

        # Identificar Caixa Aberto
        sessao = SessaoCaixaLocal.objects.filter(operador_username=request.user.username, status='aberta').first()
        if not sessao:
            return JsonResponse({'success': False, 'error': 'Não há nenhum caixa aberto para o seu usuário. Abra o caixa primeiro.'})

        # Criar a venda local
        venda = VendaLocal.objects.create(
            sessao=sessao,
            total=total,
            metodo_pagamento=metodo_pagamento,
            cliente=cliente
        )

        alertas_estoque = []

        # Processar itens e decrementar estoque local
        for it in itens:
            prod_local = ProdutoLocal.objects.get(id=it['id'])
            quantidade_vendida = it['quantidade']
            
            ItemVendaLocal.objects.create(
                venda=venda,
                produto=prod_local,
                quantidade=quantidade_vendida,
                valor_unitario=it['valor_unitario'],
                total=it['total']
            )

            # Baixa estoque local
            prod_local.quantidade -= quantidade_vendida
            prod_local.save()

            if prod_local.estoque_baixo:
                alertas_estoque.append(f"{prod_local.nome} está com estoque baixo ({prod_local.quantidade:.3f} {prod_local.unidade_medida})!")

        # Tentar sincronizar em segundo plano imediatamente (se falhar, fica pendente)
        push_sales_to_cloud()

        return JsonResponse({
            'success': True,
            'venda_id': str(venda.id),
            'alertas_estoque': alertas_estoque
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url='login')
def ajax_sync_snapshot(request):
    """Gatilho manual de carga de dados (Nuvem -> Local)."""
    push_sales_to_cloud()
    success, message = pull_snapshot_from_cloud()
    if success:
        # Serializar produtos e clientes locais para o JS recarregar sem reload!
        produtos = list(ProdutoLocal.objects.all().values(
            'id', 'nome', 'codigo_barras', 'codigo_interno', 'valor_venda', 'unidade_medida'
        ))
        # Converter Decimal para float para ser serializável em JSON e UUID para str
        for p in produtos:
            p['id'] = str(p['id'])
            p['valor_venda'] = float(p['valor_venda'])

        clientes = list(ClienteLocal.objects.all().values(
            'id', 'nome', 'nfc_uid', 'limite_credito', 'saldo_devedor'
        ))
        for c in clientes:
            c['id'] = str(c['id'])
            c['limite_credito'] = float(c['limite_credito'])
            c['saldo_devedor'] = float(c['saldo_devedor'])

        config = get_config()
        ultimo_sync = config.ultimo_sync.strftime('%d/%m %H:%M') if config.ultimo_sync else "Nunca"

        # Alertas de estoque baixo
        alertas_estoque = []
        for p in ProdutoLocal.objects.all():
            if p.estoque_baixo:
                alertas_estoque.append(f"{p.nome} está com estoque baixo ({p.quantidade:.3f} {p.unidade_medida})!")

        return JsonResponse({
            'success': True,
            'message': message,
            'produtos': produtos,
            'clientes': clientes,
            'ultimo_sync': ultimo_sync,
            'alertas_estoque': alertas_estoque,
            'mp_configurado': config.mp_configurado,
        })
    return JsonResponse({'success': False, 'message': message})


@login_required(login_url='login')
def ajax_sync_push(request):
    """Gatilho manual de envio de vendas pendentes."""
    success, message = push_sales_to_cloud()
    return JsonResponse({'success': success, 'message': message})


@csrf_exempt
@login_required(login_url='login')
def ajax_save_config(request):
    """Salva configurações de integração locais."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            config = get_config()
            config.api_token = data.get('api_token', '').strip()
            config.api_cloud_url = data.get('api_cloud_url', '').strip()
            config.save()
            return JsonResponse({'success': True, 'message': 'Configurações de integração salvas!'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'error': 'Método inválido'}, status=400)


@csrf_exempt
@login_required(login_url='login')
def ajax_gerar_pix(request):
    """Gera um pagamento PIX via Mercado Pago."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo invalido'}, status=400)

    from local_pdv.mp_service import gerar_pix

    try:
        data = json.loads(request.body)
        valor = float(data.get('valor', 0))
        descricao = data.get('descricao', 'Venda PDV')

        if valor <= 0:
            return JsonResponse({'success': False, 'error': 'Valor invalido.'})

        config = get_config()
        if not config.mp_configurado:
            return JsonResponse({'success': False, 'error': 'Mercado Pago nao configurado. Sincronize com o Cloud primeiro.'})

        ok, resultado = gerar_pix(valor, descricao, config.mp_access_token)

        if ok:
            # Salvar registro local
            pag = PagamentoPix.objects.create(
                mp_payment_id=resultado['payment_id'],
                valor=valor,
                qr_code=resultado.get('qr_code', ''),
                qr_code_base64=resultado.get('qr_code_base64', ''),
                status='pending',
            )

            return JsonResponse({
                'success': True,
                'payment_id': resultado['payment_id'],
                'qr_code': resultado.get('qr_code', ''),
                'qr_code_base64': resultado.get('qr_code_base64', ''),
            })
        else:
            return JsonResponse({'success': False, 'error': str(resultado)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url='login')
def ajax_status_pix(request):
    """Consulta o status de um pagamento PIX no Mercado Pago."""
    from local_pdv.mp_service import consultar_pagamento

    payment_id = request.GET.get('payment_id', '')
    if not payment_id:
        return JsonResponse({'error': 'payment_id obrigatorio'}, status=400)

    config = get_config()
    if not config.mp_configurado:
        return JsonResponse({'success': False, 'error': 'MP nao configurado.'})

    ok, dados = consultar_pagamento(payment_id, config.mp_access_token)

    if ok:
        status = dados.get('status', '')

        # Se aprovado, atualizar registro local
        if status == 'approved':
            PagamentoPix.objects.filter(mp_payment_id=payment_id).update(status='approved')

        return JsonResponse({
            'success': True,
            'status': status,
            'status_detail': dados.get('status_detail', ''),
        })
    else:
        return JsonResponse({'success': False, 'error': str(dados)})


@login_required(login_url='login')
def ajax_sync_mp(request):
    """Forca sincronizacao das credenciais MP do Cloud."""
    ok, msg = pull_mp_config()
    config = get_config()
    return JsonResponse({
        'success': ok,
        'message': msg,
        'mp_configurado': config.mp_configurado,
    })

@csrf_exempt
@login_required(login_url='login')
def cancelar_venda(request, venda_id):
    if request.method == 'POST':
        try:
            venda = VendaLocal.objects.get(id=venda_id)
            if venda.status == 'cancelada':
                return JsonResponse({'success': False, 'error': 'Venda já está cancelada.'})
            
            venda.status = 'cancelada'
            venda.synced = False  # Força sincronizar o cancelamento
            venda.save()
            
            # Devolvemos estoque local? Sim.
            for item in venda.itens.all():
                produto = item.produto
                produto.quantidade += item.quantidade
                produto.save()

            return JsonResponse({'success': True})
        except VendaLocal.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Venda não encontrada.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método inválido.'})


@login_required(login_url='login')
def get_venda_detalhes(request, venda_id):
    try:
        venda = VendaLocal.objects.get(id=venda_id)
        itens = []
        for item in venda.itens.all():
            itens.append({
                'produto_nome': item.produto.nome,
                'quantidade': float(item.quantidade),
                'unidade_medida': item.produto.unidade_medida,
                'valor_unitario': float(item.valor_unitario),
                'total': float(item.total),
            })
        
        data = {
            'success': True,
            'id': str(venda.id),
            'numero': str(venda.id)[:8],
            'total': float(venda.total),
            'metodo_pagamento': venda.metodo_pagamento.upper(),
            'status': venda.status,
            'created_at': venda.created_at.strftime('%d/%m/%Y %H:%M:%S'),
            'cliente': venda.cliente.nome if venda.cliente else None,
            'itens': itens
        }
        return JsonResponse(data)
    except VendaLocal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Venda não encontrada.'})
