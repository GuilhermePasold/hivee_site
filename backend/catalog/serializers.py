import json
import re
import urllib.request
from urllib.error import URLError

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import serializers

from .models import AvailabilitySlot, Category, Provider, UserProfile

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


class ProviderSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    rating = serializers.FloatField()
    hourly_rate = serializers.FloatField()
    distance_km = serializers.SerializerMethodField()
    availability_slots = AvailabilitySlotSerializer(many=True, read_only=True)
    avatar = serializers.ImageField(read_only=True)
    member_since = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

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


class RecommendationSerializer(ProviderSerializer):
    match_score = serializers.IntegerField(read_only=True)
    match_reason = serializers.CharField(read_only=True)

    class Meta(ProviderSerializer.Meta):
        fields = ProviderSerializer.Meta.fields + ["match_score", "match_reason"]


# --- Auth ------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    is_provider = serializers.SerializerMethodField()
    provider_slug = serializers.SerializerMethodField()
    cpf = serializers.SerializerMethodField()
    provider_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "is_provider", "provider_slug", "cpf", "provider_status"]

    def get_is_provider(self, obj) -> bool:
        return obj.provider_profiles.exists()

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
