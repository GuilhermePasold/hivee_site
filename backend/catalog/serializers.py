import json
import re
import urllib.request
from urllib.error import URLError

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import serializers

from .models import (
    AvailabilitySlot,
    Category,
    Demand,
    DemandOffer,
    FAQArticle,
    Provider,
    ProviderImage,
    Review,
    Servico,
    SupportCategory,
    SupportMessage,
    SupportTicket,
    SupportTicketLog,
    Tag,
    UserProfile,
)

User = get_user_model()

RECEITAWS_URL = "https://www.receitaws.com.br/v1/cpf/%s"


def validate_cpf(value):
    cpf = re.sub(r"\D", "", value)
    if len(cpf) != 11:
        raise serializers.ValidationError("CPF deve ter 11 dígitos.")
    if cpf == cpf[0] * 11:
        raise serializers.ValidationError("CPF inválido.")
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
        dig = (soma * 10 % 11) % 10
        if int(cpf[i]) != dig:
            raise serializers.ValidationError("CPF inválido.")
    return cpf


def consultar_receita(cpf, nome):
    """Tenta consultar CPF na ReceitaWS. Retorna (cpf_status, cpf_name, erro)."""
    try:
        req = urllib.request.Request(RECEITAWS_URL % cpf, headers={"User-Agent": "HIVEE/1.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode())
    except (URLError, json.JSONDecodeError, OSError):
        return "pending_verification", "", "API indisponível no momento"
    except Exception:
        return "pending_verification", "", "Erro inesperado ao consultar CPF"

    if data.get("status") == "ERROR":
        if "limit" in (data.get("message") or "").lower():
            return "pending_verification", "", "Rate limit excedido — verificação pendente"
        if "inexistente" in (data.get("message") or "").lower():
            raise serializers.ValidationError("CPF não encontrado na base da Receita Federal.")
        return "pending_verification", "", "CPF com status desconhecido"

    nome_receita = (data.get("nome") or "").strip().upper()
    if not nome_receita:
        return "pending_verification", "", "API não retornou nome"

    nome_usuario = nome.strip().upper()
    if nome_receita != nome_usuario:
        return "mismatch", nome_receita, "Nome não confere com o CPF"

    return "verified", nome_receita, ""


class CategorySerializer(serializers.ModelSerializer):
    provider_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "slug", "name", "icon", "tagline", "accent", "provider_count"]


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilitySlot
        fields = ["id", "day_of_week", "start_time", "end_time"]


class TagSerializer(serializers.ModelSerializer):
    provider_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "provider_count"]


class ProviderImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProviderImage
        fields = ["id", "image_url", "alt_text", "created_at"]

    def get_image_url(self, obj) -> str | None:
        return obj.image.url if obj.image else None


class ProviderSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    rating = serializers.FloatField()
    hourly_rate = serializers.FloatField()
    distance_km = serializers.SerializerMethodField()
    availability_slots = AvailabilitySlotSerializer(many=True, read_only=True)
    avatar = serializers.ImageField(read_only=True)
    member_since = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    gallery = ProviderImageSerializer(many=True, read_only=True, source="images")
    profile_completeness = serializers.SerializerMethodField()

    class Meta:
        model = Provider
        fields = [
            "id",
            "slug",
            "name",
            "headline",
            "bio",
            "category",
            "avatar_url",
            "avatar",
            "cover_url",
            "rating",
            "reviews_count",
            "jobs_done",
            "hourly_rate",
            "currency",
            "city",
            "neighborhood",
            "state",
            "latitude",
            "longitude",
            "distance_km",
            "verified",
            "top_rated",
            "response_time",
            "availability",
            "availability_slots",
            "skills",
            "tags",
            "gallery",
            "profile_completeness",
            "member_since",
            "status",
        ]

    def get_distance_km(self, obj) -> float | None:
        value = getattr(obj, "distance_km", None)
        return round(value, 2) if value is not None else None

    def get_member_since(self, obj) -> int:
        return obj.created_at.year if obj.created_at else 2022

    def get_avatar_url(self, obj) -> str | None:
        return obj.avatar_url or None

    def get_profile_completeness(self, obj) -> int:
        """Quão completo está o perfil (0-100), derivado dos dados reais.

        Usa os caches de prefetch (`.all()`) para não gerar N+1 nas listagens.
        """
        checks = [
            bool(obj.avatar_url or obj.avatar),
            bool(obj.headline),
            len(obj.bio or "") >= 40,
            len(obj.tags.all()) >= 3,
            len(obj.availability_slots.all()) >= 1,
            len(obj.images.all()) >= 1,
            obj.latitude is not None and obj.longitude is not None,
        ]
        return round(100 * sum(checks) / len(checks))


class RecommendationSerializer(ProviderSerializer):
    match_score = serializers.IntegerField(read_only=True)
    match_reason = serializers.CharField(read_only=True)

    class Meta(ProviderSerializer.Meta):
        fields = ProviderSerializer.Meta.fields + ["match_score", "match_reason"]


def resolve_tags(names):
    """Transforma uma lista de nomes (texto livre) em objetos Tag, criando os
    que ainda não existem. Dedup por slug."""
    tags, seen = [], set()
    for raw in names:
        name = (raw or "").strip()
        if not name:
            continue
        slug = slugify(name)[:60]
        if not slug or slug in seen:
            continue
        seen.add(slug)
        tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name[:50]})
        tags.append(tag)
    return tags


class ProviderUpdateSerializer(serializers.ModelSerializer):
    """Edição do próprio perfil pelo prestador (campos seguros + tags + agenda)."""

    tags = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False
    )
    availability_slots = AvailabilitySlotSerializer(many=True, required=False)
    hourly_rate = serializers.FloatField(required=False, min_value=0)

    class Meta:
        model = Provider
        fields = [
            "headline",
            "bio",
            "hourly_rate",
            "response_time",
            "availability",
            "city",
            "neighborhood",
            "state",
            "latitude",
            "longitude",
            "tags",
            "availability_slots",
        ]
        extra_kwargs = {f: {"required": False} for f in fields}

    def update(self, instance, validated):
        tags = validated.pop("tags", None)
        slots = validated.pop("availability_slots", None)

        for field, value in validated.items():
            setattr(instance, field, value)
        instance.save()

        if tags is not None:
            resolved = resolve_tags(tags)
            instance.tags.set(resolved)
            # Espelha em `skills` (texto) para manter compatibilidade com telas antigas.
            instance.skills = [t.name for t in resolved]
            instance.save(update_fields=["skills"])

        if slots is not None:
            instance.availability_slots.all().delete()
            for slot in slots:
                AvailabilitySlot.objects.create(provider=instance, **slot)

        return instance


# --- Auth ------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    is_provider = serializers.SerializerMethodField()
    provider_slug = serializers.SerializerMethodField()
    cpf = serializers.SerializerMethodField()
    telefone = serializers.SerializerMethodField()
    provider_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "is_provider", "provider_slug", "cpf", "telefone", "provider_status", "is_staff"]

    def get_is_provider(self, obj) -> bool:
        return obj.provider_profiles.exists()

    def get_telefone(self, obj) -> str:
        try:
            return obj.profile.telefone or ""
        except UserProfile.DoesNotExist:
            return ""

    def get_provider_slug(self, obj) -> str | None:
        profile = obj.provider_profiles.first()
        return profile.slug if profile else None

    def get_cpf(self, obj) -> str | None:
        try:
            return obj.profile.cpf
        except UserProfile.DoesNotExist:
            return None

    def get_provider_status(self, obj) -> str:
        try:
            return obj.profile.provider_status or ""
        except UserProfile.DoesNotExist:
            return ""


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)
    cpf = serializers.CharField(max_length=14, required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return value

    def validate_cpf(self, value):
        if not value:
            return value
        cpf_limpo = validate_cpf(value)
        if UserProfile.objects.filter(cpf=cpf_limpo).exists():
            raise serializers.ValidationError("Este CPF já está cadastrado.")
        nome = self.initial_data.get("name", "")
        status, nome_api, erro = consultar_receita(cpf_limpo, nome)
        if status == "mismatch":
            raise serializers.ValidationError(
                f"Nome informado não confere com o CPF na Receita Federal. "
                f"Nome na Receita: {nome_api}"
            )
        self._cpf_status = status
        self._cpf_name = nome_api
        return cpf_limpo

    def create(self, validated):
        cpf = validated.pop("cpf", "")
        cpf_status = getattr(self, "_cpf_status", "pending_verification")
        cpf_name = getattr(self, "_cpf_name", "")
        nome = validated.get("first_name", validated.get("name", ""))
        user = User.objects.create_user(
            username=validated["email"],
            email=validated["email"],
            password=validated["password"],
            first_name=nome,
        )
        if cpf:
            UserProfile.objects.create(
                user=user, cpf=cpf, cpf_status=cpf_status, cpf_name=cpf_name
            )
        return user


class ProviderWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.all()
    )
    avatar_url = serializers.URLField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True, default="")
    neighborhood = serializers.CharField(required=False, allow_blank=True, default="")
    state = serializers.CharField(required=False, allow_blank=True, default="")
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    response_time = serializers.CharField(required=False, allow_blank=True, default="")
    availability = serializers.CharField(required=False, allow_blank=True, default="")
    availability_slots = AvailabilitySlotSerializer(many=True, required=False)
    cpf = serializers.CharField(max_length=14, required=False, allow_blank=True)

    def validate_cpf(self, value):
        if not value:
            return value
        cpf_limpo = validate_cpf(value)
        owner = self.context.get("request").user if "request" in self.context else None
        if UserProfile.objects.filter(cpf=cpf_limpo).exclude(user=owner).exists():
            raise serializers.ValidationError("Este CPF já está cadastrado.")
        return cpf_limpo

    class Meta:
        model = Provider
        fields = [
            "name",
            "headline",
            "bio",
            "category",
            "avatar_url",
            "hourly_rate",
            "city",
            "neighborhood",
            "state",
            "latitude",
            "longitude",
            "response_time",
            "availability",
            "availability_slots",
            "skills",
            "cpf",
        ]

    def create(self, validated):
        slots_data = validated.pop("availability_slots", [])
        cpf = validated.pop("cpf", "")
        owner = validated.get("owner")

        if owner:
            profile, _ = UserProfile.objects.get_or_create(user=owner)
            if cpf and not profile.cpf:
                profile.cpf = cpf
                profile.cpf_status = "pending_verification"
            profile.provider_status = "pending"
            update = ["provider_status"]
            if cpf and not profile.cpf:
                update += ["cpf", "cpf_status"]
            profile.save(update_fields=update)

        base = slugify(validated["name"]) or "prestador"
        slug = base
        i = 1
        while Provider.objects.filter(slug=slug).exists():
            i += 1
            slug = f"{base}-{i}"
        validated["slug"] = slug
        validated["status"] = "pending"
        provider = Provider.objects.create(**validated)
        for slot_data in slots_data:
            AvailabilitySlot.objects.create(provider=provider, **slot_data)
        return provider


# --- Demandas (cliente publica, prestadores se oferecem) -------------------
class DemandOfferSerializer(serializers.ModelSerializer):
    """Oferta de um prestador, vista pelo cliente dono da demanda."""

    provider = ProviderSerializer(read_only=True)
    suggested_value = serializers.FloatField(allow_null=True)
    demand_id = serializers.IntegerField(source="demand.id", read_only=True)

    class Meta:
        model = DemandOffer
        fields = [
            "id",
            "demand_id",
            "provider",
            "message",
            "suggested_value",
            "status",
            "created_at",
        ]


class DemandSerializer(serializers.ModelSerializer):
    """Leitura de uma demanda. `has_my_offer`/`distance_km` vêm do contexto/anotação."""

    category = CategorySerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    client_name = serializers.SerializerMethodField()
    client_id = serializers.IntegerField(source="client.id", read_only=True)
    distance_km = serializers.SerializerMethodField()
    has_my_offer = serializers.SerializerMethodField()

    class Meta:
        model = Demand
        fields = [
            "id",
            "client_name",
            "client_id",
            "title",
            "description",
            "category",
            "tags",
            "city",
            "neighborhood",
            "state",
            "latitude",
            "longitude",
            "preferred_schedule",
            "budget_hint",
            "status",
            "offer_count",
            "created_at",
            "has_my_offer",
            "distance_km",
        ]

    def get_tags(self, obj) -> list[str]:
        return [t.name for t in obj.tags.all()]

    def get_client_name(self, obj) -> str:
        return obj.client.first_name or obj.client.email.split("@")[0]

    def get_distance_km(self, obj) -> float | None:
        value = getattr(obj, "distance_km", None)
        return round(value, 2) if value is not None else None

    def get_has_my_offer(self, obj) -> bool:
        # O viewset injeta o conjunto de ids de demanda em que o prestador logado
        # já se ofereceu, evitando uma query por card na listagem.
        ids = self.context.get("offered_demand_ids")
        if ids is not None:
            return obj.id in ids
        return False


class CreateDemandSerializer(serializers.ModelSerializer):
    """Criação de demanda por qualquer usuário autenticado."""

    category_slug = serializers.SlugRelatedField(
        source="category",
        slug_field="slug",
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False
    )

    class Meta:
        model = Demand
        fields = [
            "title",
            "description",
            "category_slug",
            "tags",
            "city",
            "neighborhood",
            "state",
            "latitude",
            "longitude",
            "preferred_schedule",
            "budget_hint",
        ]
        extra_kwargs = {
            "city": {"required": False},
            "neighborhood": {"required": False},
            "state": {"required": False},
            "latitude": {"required": False, "allow_null": True},
            "longitude": {"required": False, "allow_null": True},
            "preferred_schedule": {"required": False},
            "budget_hint": {"required": False},
        }

    def create(self, validated):
        tags = validated.pop("tags", None)
        demand = Demand.objects.create(**validated)
        if tags:
            demand.tags.set(resolve_tags(tags))
        return demand


class CreateOfferSerializer(serializers.ModelSerializer):
    """Prestador se oferece para uma demanda (mensagem + valor opcional)."""

    message = serializers.CharField(max_length=2000, allow_blank=True, required=False)
    suggested_value = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True, min_value=0
    )

    class Meta:
        model = DemandOffer
        fields = ["message", "suggested_value"]


# --- Suporte ao usuário ----------------------------------------------------
class SupportCategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = SupportCategory
        fields = ["id", "slug", "name", "icon", "order", "article_count"]


class FAQArticleSerializer(serializers.ModelSerializer):
    category = SupportCategorySerializer(read_only=True)

    class Meta:
        model = FAQArticle
        fields = ["id", "category", "question", "slug", "answer", "order"]


class SupportMessageSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportMessage
        fields = ["id", "author_name", "content", "is_staff", "attachment", "created_at"]
        read_only_fields = ["is_staff"]

    def get_author_name(self, obj) -> str:
        return obj.author.first_name or obj.author.email


class SupportTicketLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicketLog
        fields = ["id", "from_status", "to_status", "changed_by_name", "note", "created_at"]

    def get_changed_by_name(self, obj) -> str:
        return obj.changed_by.first_name if obj.changed_by else "Sistema"


class SupportTicketSerializer(serializers.ModelSerializer):
    messages = SupportMessageSerializer(many=True, read_only=True)
    logs = SupportTicketLogSerializer(many=True, read_only=True)
    category = SupportCategorySerializer(read_only=True)
    category_slug = serializers.SlugRelatedField(
        source="category",
        slug_field="slug",
        queryset=SupportCategory.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    can_transition = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "user_name",
            "category",
            "category_slug",
            "subject",
            "description",
            "status",
            "priority",
            "assigned_to",
            "assigned_to_name",
            "messages",
            "logs",
            "can_transition",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]
        read_only_fields = [
            "status",
            "assigned_to",
            "created_at",
            "updated_at",
            "resolved_at",
            "closed_at",
        ]

    def get_user_name(self, obj) -> str:
        return obj.user.first_name or obj.user.email

    def get_assigned_to_name(self, obj) -> str | None:
        return obj.assigned_to.first_name if obj.assigned_to else None

    def get_can_transition(self, obj) -> list[str]:
        request = self.context.get("request")
        if not request:
            return []
        # Import tardio evita ciclo (views importa serializers).
        from .views.api_views import SupportTicketViewSet

        return SupportTicketViewSet._allowed_transitions(obj, request.user)


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_nome = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "nota", "comentario", "reviewer_nome", "created_at"]

    def get_reviewer_nome(self, obj) -> str:
        return obj.reviewer.first_name or obj.reviewer.email.split("@")[0]


class ServicoSerializer(serializers.ModelSerializer):
    provider_slug = serializers.CharField(source="provider.slug", read_only=True)
    provider_nome = serializers.CharField(source="provider.name", read_only=True)
    provider_avatar = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    review = ReviewSerializer(read_only=True)
    valor_combinado = serializers.FloatField(read_only=True)
    valor_comissao = serializers.FloatField(read_only=True)
    valor_liquido = serializers.FloatField(read_only=True)

    class Meta:
        model = Servico
        fields = [
            "id", "provider_slug", "provider_nome", "provider_avatar",
            "cliente_user", "cliente_nome", "cliente_email", "cliente_telefone",
            "descricao", "endereco", "observacoes",
            "data_solicitada", "data_aprovacao", "data_inicio", "data_conclusao", "data_pagamento",
            "valor_combinado", "valor_comissao", "valor_liquido",
            "status", "status_display", "motivo_rejeicao", "sugestao_horario",
            "pix_copia_cola", "pago", "review", "created_at",
        ]

    def get_provider_avatar(self, obj) -> str | None:
        avatar = obj.provider.avatar.url if obj.provider.avatar else None
        return avatar or obj.provider.avatar_url or None
