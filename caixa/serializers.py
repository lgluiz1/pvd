from rest_framework import serializers
from caixa.models import SessaoCaixa, Sangria, Suprimento

class SessaoCaixaSerializer(serializers.ModelSerializer):
    operador_nome = serializers.CharField(source='operador.get_full_name', read_only=True, default='')
    class Meta:
        model = SessaoCaixa
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SangriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sangria
        fields = '__all__'

class SuprimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Suprimento
        fields = '__all__'
