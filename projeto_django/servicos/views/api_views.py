from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from ..models import CategoriaServico, PrestadorPerfil, Contrato

from ..serializers import CategoriaSerializer, PrestadorSerializer, UserSerializer, ContratoSerializer




class CategoriaListAPIView(generics.ListAPIView):
    queryset = CategoriaServico.objects.filter(ativo=True)
    serializer_class = CategoriaSerializer
    permission_classes = []


class PrestadorListAPIView(generics.ListAPIView):
    serializer_class = PrestadorSerializer
    permission_classes = []

    def get_queryset(self):
        # Allow looking up all providers first
        queryset = PrestadorPerfil.objects.filter(disponivel=True)
        
        especialidade_slug = self.request.query_params.get('especialidade', None)
        categoria_id = self.request.query_params.get('categoria', None)
        cidade = self.request.query_params.get('cidade', None)
        localizacao = self.request.query_params.get('localizacao', None)
        search = self.request.query_params.get('search', None)

        if especialidade_slug:
            queryset = queryset.filter(especialidades__slug=especialidade_slug)
            
        if categoria_id:
            queryset = queryset.filter(especialidades__id=categoria_id)

        if cidade:
            queryset = queryset.filter(cidade__icontains=cidade)
            
        if localizacao:
            # We check if provider's city or state is mentioned in the full location display name
            # Or if provider has no city, we include them
            matching_providers = []
            for p in queryset:
                if p.cidade and p.cidade.lower() in localizacao.lower():
                    matching_providers.append(p.id)
                elif not p.cidade:
                    matching_providers.append(p.id)
            queryset = queryset.filter(id__in=matching_providers)

        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(bio__icontains=search) |
                Q(especialidades__nome__icontains=search)
            ).distinct()

        return queryset


class PrestadorRetrieveAPIView(generics.RetrieveAPIView):
    queryset = PrestadorPerfil.objects.all()
    serializer_class = PrestadorSerializer
    permission_classes = []
    lookup_field = 'pk'


class LoginAPIView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.filter(username=email).first()
            
        if user and user.check_password(password):
            return Response({
                'success': True,
                'token': f'session-token-{user.id}',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        return Response({
            'success': False,
            'message': 'Credenciais inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)


class RegisterAPIView(APIView):
    permission_classes = []

    def post(self, request):
        name = request.data.get('name', '')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'success': False,
                'message': 'Email e senha são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            return Response({
                'success': False,
                'message': 'Usuário já cadastrado com esse email'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        names = name.split(' ', 1)
        first_name = names[0]
        last_name = names[1] if len(names) > 1 else ''
        
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        return Response({
            'success': True,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
class BecomeProfessionalAPIView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        name = request.data.get('name', '')
        phone = request.data.get('phone', '')
        category_id = request.data.get('category')
        experience = request.data.get('experience', 0)
        description = request.data.get('description', '')
        price = request.data.get('price', 0)
        
        # Check if user exists or create one
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.filter(username=email).first()
            
        if user is None:
            names = name.split(' ', 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else ''
            # Create a user with a default password or random
            user = User.objects.create_user(
                username=email,
                email=email,
                password='password123',
                first_name=first_name,
                last_name=last_name
            )
            
        # Create PrestadorPerfil
        prestador, created = PrestadorPerfil.objects.get_or_create(user=user)
        prestador.bio = description
        prestador.valor_hora = price
        prestador.anos_experiencia = int(experience)
        prestador.status_adesao = 'ATIVO'
        prestador.disponivel = True
        
        # Add category
        if category_id:
            try:
                category = CategoriaServico.objects.get(id=category_id)
                prestador.especialidades.add(category)
            except CategoriaServico.DoesNotExist:
                pass
                
        prestador.save()
        
        return Response({
            'success': True,
            'message': 'Profissional cadastrado com sucesso!',
            'prestador_id': prestador.id
        }, status=status.HTTP_201_CREATED)


class PostDemandAPIView(APIView):
    permission_classes = []

    def post(self, request):
        title = request.data.get('title')
        description = request.data.get('description')
        category_id = request.data.get('category')
        budget = request.data.get('budget', 0)
        
        # Hardcode a dummy user for the customer if no authorization header
        user = User.objects.first() # Grab admin or anyone
        
        try:
            category = CategoriaServico.objects.get(id=category_id)
        except CategoriaServico.DoesNotExist:
            # Try by string lookup if category_id is an explicit name
            category = CategoriaServico.objects.filter(nome__icontains=category_id).first()

        contrato = Contrato.objects.create(
            cliente=user,
            titulo=title,
            descricao=description,
            categoria=category,
            valor_acordado=budget,
            status='PENDENTE'
        )
        
        return Response({
            'success': True,
            'message': 'Demanda publicada com sucesso!',
            'contrato_id': contrato.id
        }, status=status.HTTP_201_CREATED)


class ContratoListAPIView(generics.ListAPIView):
    serializer_class = ContratoSerializer
    permission_classes = []

    def get_queryset(self):
        # Return all contracts for simplicity
        return Contrato.objects.all()


