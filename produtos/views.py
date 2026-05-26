from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from decimal import Decimal
from produtos.models import Produto, Categoria, HistoricoPreco, Embalagem


def clean_decimal(val):
    """Trata valores decimais que podem vir com vírgula do padrão brasileiro."""
    if not val:
        return Decimal('0')
    val_str = str(val).strip()
    if ',' in val_str:
        # Padrão brasileiro (ex: 1.250,50 -> 1250.50)
        val_str = val_str.replace('.', '').replace(',', '.')
    try:
        return Decimal(val_str)
    except Exception:
        return Decimal('0')


@login_required
def produto_lista(request):
    """Lista de produtos com busca e filtros."""
    produtos = Produto.objects.filter(empresa=request.empresa)

    # Filtros
    busca = request.GET.get('busca', '').strip()
    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca) |
            Q(codigo_barras__icontains=busca) |
            Q(codigo_interno__icontains=busca) |
            Q(marca__icontains=busca)
        )

    categoria_id = request.GET.get('categoria', '')
    if categoria_id:
        produtos = produtos.filter(categoria_id=categoria_id)

    status_filter = request.GET.get('status', '')
    if status_filter == 'ativo':
        produtos = produtos.filter(ativo=True)
    elif status_filter == 'inativo':
        produtos = produtos.filter(ativo=False)
    elif status_filter == 'estoque_baixo':
        produtos = produtos.filter(quantidade__lte=models.F('estoque_minimo'))
    elif status_filter == 'favorito':
        produtos = produtos.filter(favorito=True)

    categorias = Categoria.objects.filter(empresa=request.empresa, ativo=True)

    return render(request, 'produtos/lista.html', {
        'produtos': produtos,
        'categorias': categorias,
        'busca': busca,
        'page_title': 'Produtos',
    })


@login_required
def produto_criar(request):
    """Criar novo produto."""
    if request.method == 'POST':
        produto = Produto(empresa=request.empresa)
        produto.nome = request.POST.get('nome', '').strip()
        produto.marca = request.POST.get('marca', '').strip()
        produto.codigo_barras = request.POST.get('codigo_barras', '').strip()
        produto.sem_codigo_barras = request.POST.get('sem_codigo_barras') == 'on'
        produto.unidade_medida = request.POST.get('unidade_medida', 'un')
        produto.valor_compra = clean_decimal(request.POST.get('valor_compra'))
        produto.lucro_percentual = clean_decimal(request.POST.get('lucro_percentual'))
        produto.valor_venda = clean_decimal(request.POST.get('valor_venda'))
        produto.comprado_em_caixa = request.POST.get('comprado_em_caixa') == 'on'
        produto.quantidade = clean_decimal(request.POST.get('quantidade'))
        produto.estoque_minimo = clean_decimal(request.POST.get('estoque_minimo', '5'))

        if produto.comprado_em_caixa:
            produto.valor_caixa = clean_decimal(request.POST.get('valor_caixa'))
            produto.qtd_itens_caixa = clean_decimal(request.POST.get('qtd_itens_caixa'))

        cat_id = request.POST.get('categoria', '')
        if cat_id:
            produto.categoria_id = cat_id

        if request.FILES.get('imagem'):
            produto.imagem = request.FILES['imagem']

        produto.save()

        # Registrar histórico de preço
        HistoricoPreco.objects.create(
            empresa=request.empresa,
            produto=produto,
            valor_compra=produto.valor_compra,
            valor_venda=produto.valor_venda,
            lucro_percentual=produto.lucro_percentual,
            usuario=request.user,
            observacao='Cadastro inicial',
        )

        messages.success(request, f'Produto "{produto.nome}" criado com sucesso!')
        return redirect('produtos:lista')

    categorias = Categoria.objects.filter(empresa=request.empresa, ativo=True)
    embalagens = Embalagem.objects.filter(empresa=request.empresa, ativo=True)
    marcas_existentes = Produto.objects.filter(empresa=request.empresa).exclude(marca='').values_list('marca', flat=True).distinct().order_by('marca')
    
    return render(request, 'produtos/form.html', {
        'categorias': categorias,
        'embalagens': embalagens,
        'marcas_existentes': marcas_existentes,
        'unidades': Produto.UNIDADE_CHOICES,
        'page_title': 'Novo Produto',
    })


@login_required
def produto_editar(request, pk):
    """Editar produto com modal de atualização de preço."""
    produto = get_object_or_404(Produto, pk=pk, empresa=request.empresa)

    if request.method == 'POST':
        valor_compra_antigo = produto.valor_compra
        valor_venda_antigo = produto.valor_venda

        produto.nome = request.POST.get('nome', produto.nome).strip()
        produto.marca = request.POST.get('marca', produto.marca).strip()
        produto.codigo_barras = request.POST.get('codigo_barras', produto.codigo_barras).strip()
        produto.sem_codigo_barras = request.POST.get('sem_codigo_barras') == 'on'
        produto.unidade_medida = request.POST.get('unidade_medida', 'un')
        produto.valor_compra = clean_decimal(request.POST.get('valor_compra'))
        produto.lucro_percentual = clean_decimal(request.POST.get('lucro_percentual'))
        produto.valor_venda = clean_decimal(request.POST.get('valor_venda'))
        produto.comprado_em_caixa = request.POST.get('comprado_em_caixa') == 'on'
        produto.quantidade = clean_decimal(request.POST.get('quantidade'))
        produto.estoque_minimo = clean_decimal(request.POST.get('estoque_minimo', '5'))
        produto.favorito = request.POST.get('favorito') == 'on'
        produto.ativo = request.POST.get('ativo') == 'on'

        if produto.comprado_em_caixa:
            produto.valor_caixa = clean_decimal(request.POST.get('valor_caixa'))
            produto.qtd_itens_caixa = clean_decimal(request.POST.get('qtd_itens_caixa'))

        cat_id = request.POST.get('categoria', '')
        if cat_id:
            produto.categoria_id = cat_id
        else:
            produto.categoria = None

        if request.FILES.get('imagem'):
            produto.imagem = request.FILES['imagem']

        produto.save()

        # Registrar histórico se preço mudou
        if produto.valor_compra != valor_compra_antigo or produto.valor_venda != valor_venda_antigo:
            HistoricoPreco.objects.create(
                empresa=request.empresa,
                produto=produto,
                valor_compra=produto.valor_compra,
                valor_venda=produto.valor_venda,
                lucro_percentual=produto.lucro_percentual,
                usuario=request.user,
                observacao=request.POST.get('observacao_preco', ''),
            )

        messages.success(request, f'Produto "{produto.nome}" atualizado!')
        return redirect('produtos:lista')

    categorias = Categoria.objects.filter(empresa=request.empresa, ativo=True)
    embalagens = Embalagem.objects.filter(empresa=request.empresa, ativo=True)
    historico = HistoricoPreco.objects.filter(produto=produto)[:10]
    marcas_existentes = Produto.objects.filter(empresa=request.empresa).exclude(marca='').values_list('marca', flat=True).distinct().order_by('marca')

    return render(request, 'produtos/form.html', {
        'produto': produto,
        'categorias': categorias,
        'embalagens': embalagens,
        'historico': historico,
        'marcas_existentes': marcas_existentes,
        'unidades': Produto.UNIDADE_CHOICES,
        'page_title': f'Editar {produto.nome}',
        'editando': True,
    })


@login_required
def produto_detalhe(request, pk):
    """Detalhe do produto."""
    produto = get_object_or_404(Produto, pk=pk, empresa=request.empresa)
    historico = HistoricoPreco.objects.filter(produto=produto)[:20]

    return render(request, 'produtos/detalhe.html', {
        'produto': produto,
        'historico': historico,
        'page_title': produto.nome,
    })


@login_required
def categoria_lista(request):
    """CRUD de categorias."""
    categorias = Categoria.objects.filter(empresa=request.empresa)

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        if nome:
            Categoria.objects.create(
                empresa=request.empresa,
                nome=nome,
                descricao=request.POST.get('descricao', ''),
            )
            messages.success(request, f'Categoria "{nome}" criada!')
        return redirect('produtos:categorias')

    return render(request, 'produtos/categorias.html', {
        'categorias': categorias,
        'page_title': 'Categorias',
    })


@login_required
def embalagem_lista(request):
    """CRUD simples de tipos de embalagens/cargas."""
    embalagens = Embalagem.objects.filter(empresa=request.empresa)

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        qtd = request.POST.get('quantidade_itens', '').replace(',', '.')
        
        if nome and qtd:
            try:
                Embalagem.objects.create(
                    empresa=request.empresa,
                    nome=nome,
                    quantidade_itens=Decimal(qtd)
                )
                messages.success(request, f'Embalagem "{nome}" cadastrada com sucesso!')
            except Exception as e:
                messages.error(request, 'Erro ao cadastrar embalagem. Verifique os valores.')
                
        return redirect('produtos:embalagens')

    return render(request, 'produtos/embalagens.html', {
        'embalagens': embalagens,
        'page_title': 'Tipos de Embalagem',
    })


@login_required
def buscar_por_codigo(request):
    """API interna: buscar produto por código de barras (AJAX)."""
    codigo = request.GET.get('codigo', '').strip()
    if not codigo:
        return JsonResponse({'found': False})

    try:
        produto = Produto.objects.get(
            empresa=request.empresa,
            codigo_barras=codigo,
            ativo=True
        )
        return JsonResponse({
            'found': True,
            'produto': {
                'id': str(produto.id),
                'nome': produto.nome,
                'valor_venda': str(produto.valor_venda),
                'quantidade': produto.quantidade,
                'codigo_barras': produto.codigo_barras,
                'imagem': produto.imagem.url if produto.imagem else '',
            }
        })
    except Produto.DoesNotExist:
        return JsonResponse({'found': False})


@login_required
def entrada_estoque(request):
    """Tela rápida para dar entrada em estoque via código de barras."""
    if request.method == 'POST':
        produto_id = request.POST.get('produto_id')
        qtd_adicionar = clean_decimal(request.POST.get('quantidade_adicionar'))
        novo_custo = clean_decimal(request.POST.get('novo_custo'))
        novo_venda = clean_decimal(request.POST.get('novo_venda'))
        
        if produto_id and qtd_adicionar > 0:
            produto = get_object_or_404(Produto, id=produto_id, empresa=request.empresa)
            
            estoque_anterior = produto.quantidade
            produto.quantidade += qtd_adicionar
            
            preco_mudou = False
            if novo_custo and novo_custo != produto.valor_compra:
                produto.valor_compra = novo_custo
                preco_mudou = True
            if novo_venda and novo_venda != produto.valor_venda:
                produto.valor_venda = novo_venda
                preco_mudou = True
                
            produto.save()
            
            # Registrar no histórico
            obs = f"Entrada Rápida: +{qtd_adicionar} {produto.unidade_medida}. Estoque de {estoque_anterior} para {produto.quantidade}."
            
            HistoricoPreco.objects.create(
                empresa=request.empresa,
                produto=produto,
                valor_compra=produto.valor_compra,
                valor_venda=produto.valor_venda,
                lucro_percentual=produto.lucro_percentual,
                usuario=request.user,
                observacao=obs,
            )
            
            messages.success(request, f'Estoque de "{produto.nome}" atualizado com sucesso! Novo saldo: {produto.quantidade}')
            return redirect('produtos:entrada_estoque')
            
    return render(request, 'produtos/entrada_estoque.html', {
        'page_title': 'Entrada Rápida de Estoque'
    })

# Import necessário para F expression
from django.db import models
