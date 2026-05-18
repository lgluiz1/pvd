from rest_framework import serializers
from promocoes.models import Promocao

class PromocaoSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    vigente = serializers.BooleanField(read_only=True)
    class Meta:
        model = Promocao
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
