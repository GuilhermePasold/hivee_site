from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth.models import User
from ..models import CategoriaServico, PrestadorPerfil, Contrato, UserProfile, Session
import uuid

from ..forms import ClienteEditForm, ClienteForm, PrestadorCadastroForm
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
        queryset = PrestadorPerfil.objects.filter(disponivel=True, deleted=False)
        
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
    queryset = PrestadorPerfil.objects.filter(deleted=False)
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
            profile = UserProfile.objects.filter(user=user).first()
            prestador = PrestadorPerfil.objects.filter(user=user).first()
            if not user.is_active or (profile and profile.deleted) or (prestador and prestador.deleted):
                return Response({
                    'success': False,
                    'message': 'Conta desativada'
                }, status=status.HTTP_403_FORBIDDEN)

            # create a session token
            token = uuid.uuid4().hex
            Session.objects.create(user=user, token=token)
            return Response({
                'success': True,
                'token': token,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        return Response({
            'success': False,
            'message': 'Credenciais inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    permission_classes = []

    def post(self, request):
        token = request.data.get('token') or request.META.get('HTTP_AUTHORIZATION')
        if token and token.startswith('Token '):
            token = token.split(' ', 1)[1]
        if not token:
            return Response({'success': False, 'message': 'Token ausente'}, status=status.HTTP_400_BAD_REQUEST)
        session = Session.objects.filter(token=token, expired=False).first()
        if session:
            session.expired = True
            session.save()
            return Response({'success': True, 'message': 'Desconectado com sucesso'})
        return Response({'success': False, 'message': 'Sessão não encontrada'}, status=status.HTTP_404_NOT_FOUND)


class ProfileAPIView(APIView):
    permission_classes = []

    def get_user_from_token(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        if token and token.startswith('Token '):
            token = token.split(' ', 1)[1]
        if not token:
            return None
        session = Session.objects.filter(token=token, expired=False).first()
        if not session:
            return None
        return session.user

    def get(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response({'success': False, 'message': 'Não autorizado'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'success': True, 'profile': self.serialize_profile(user)})

    def put(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response({'success': False, 'message': 'Não autorizado'}, status=status.HTTP_401_UNAUTHORIZED)
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        form = ClienteEditForm(request.data, instance=profile)
        if not form.is_valid():
            first_error = next(iter(form.errors.values()))[0]
            return Response({
                'success': False,
                'message': first_error,
                'errors': form.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        form.save()
        return Response({
            'success': True,
            'message': 'Perfil atualizado',
            'profile': self.serialize_profile(user),
        })

    def serialize_profile(self, user):
        profile = UserProfile.objects.filter(user=user).first()
        data = UserSerializer(user).data
        if profile:
            data.update({
                'cidade': profile.cidade,
                'estado': profile.estado,
                'telefone': profile.telefone,
                'cep': getattr(profile, 'cep', ''),
            })
        return data

    def delete(self, request):
        """Soft-delete the user/profile."""
        user = self.get_user_from_token(request)
        if not user:
            return Response({'success': False, 'message': 'Não autorizado'}, status=status.HTTP_401_UNAUTHORIZED)
        profile = UserProfile.objects.filter(user=user).first()
        if profile:
            profile.deleted = True
            profile.save()
        # mark prestador profile deleted too if exists
        try:
            prest = PrestadorPerfil.objects.filter(user=user).first()
            if prest:
                prest.deleted = True
                prest.save()
        except Exception:
            pass
        user.is_active = False
        user.save()
        # expire all sessions
        Session.objects.filter(user=user, expired=False).update(expired=True)
        return Response({'success': True, 'message': 'Conta marcada como excluída (soft-delete)'})


class RegisterAPIView(APIView):
    permission_classes = []

    def post(self, request):
        form = ClienteForm(request.data)
        if not form.is_valid():
            first_error = next(iter(form.errors.values()))[0]
            return Response({
                'success': False,
                'message': first_error,
                'errors': form.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        name = form.cleaned_data['name']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        cep = form.cleaned_data.get('cep', '')
            
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
        # Create a linked UserProfile and store CEP if provided
        try:
            UserProfile.objects.create(user=user, cidade='', estado='', telefone='', plano='NENHUM', cep=cep)
        except Exception:
            # If profile can't be created for some reason, ignore to avoid breaking registration
            pass
        
        return Response({
            'success': True,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
class BecomeProfessionalAPIView(APIView):
    permission_classes = []

    def post(self, request):
        form = PrestadorCadastroForm(request.data)
        if not form.is_valid():
            first_error = next(iter(form.errors.values()))[0]
            return Response({
                'success': False,
                'message': first_error,
                'errors': form.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        email = form.cleaned_data['email']
        name = form.cleaned_data['name']
        phone = form.cleaned_data['phone']
        cep = form.cleaned_data['cep']
        category_id = form.cleaned_data['category']
        experience = form.cleaned_data['experience']
        description = form.cleaned_data['description']
        price = form.cleaned_data['price']
        
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
        # Ensure a UserProfile exists and update telefone/cep
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.telefone = phone
        profile.cep = cep
        profile.save()
        prestador.cep = cep
        prestador.anos_experiencia = experience
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


