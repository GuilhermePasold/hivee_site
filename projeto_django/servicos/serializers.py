from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CategoriaServico, PrestadorPerfil, Contrato, Avaliacao


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaServico
        fields = ['id', 'nome', 'slug', 'icone', 'descricao']


class PrestadorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    especialidades = CategoriaSerializer(many=True, read_only=True)
    localizacao = serializers.CharField(source='get_localizacao', read_only=True)

    class Meta:
        model = PrestadorPerfil
        fields = [
            'id', 'user', 'slug', 'bio', 'foto', 'especialidades', 
            'valor_hora', 'cidade', 'estado', 'localizacao', 
            'anos_experiencia', 'disponivel', 'total_servicos', 'nota_media'
        ]
class ContratoSerializer(serializers.ModelSerializer):
    cliente = UserSerializer(read_only=True)
    prestador = PrestadorSerializer(read_only=True)
    categoria = CategoriaSerializer(read_only=True)

    class Meta:
        model = Contrato
        fields = '__all__'
