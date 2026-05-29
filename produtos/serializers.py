from rest_framework import serializers
from produtos.models import Produto, Categoria, HistoricoPreco


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome', 'descricao', 'ativo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProdutoSerializer(serializers.ModelSerializer):
    categoria_nome = serializers.CharField(source='categoria.nome', read_only=True, default='')
    estoque_baixo = serializers.BooleanField(read_only=True)
    estoque_critico = serializers.BooleanField(read_only=True)

    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'categoria', 'categoria_nome', 'marca',
            'codigo_barras', 'sem_codigo_barras', 'codigo_interno',
            'unidade_medida',
            'valor_compra', 'lucro_percentual', 'valor_venda',
            'comprado_em_caixa', 'valor_caixa', 'qtd_itens_caixa',
            'quantidade', 'estoque_minimo', 'estoque_baixo', 'estoque_critico',
            'imagem', 'ativo', 'favorito',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'codigo_interno', 'created_at', 'updated_at']


class ProdutoResumoSerializer(serializers.ModelSerializer):
    """Serializer leve para listagens e PDV."""
    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'codigo_barras', 'codigo_interno', 'unidade_medida',
            'valor_venda', 'quantidade', 'favorito', 'imagem',
        ]


class HistoricoPrecoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.get_full_name', read_only=True, default='')

    class Meta:
        model = HistoricoPreco
        fields = [
            'id', 'produto', 'valor_compra', 'valor_venda',
            'lucro_percentual', 'usuario', 'usuario_nome',
            'observacao', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
