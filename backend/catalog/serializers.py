import re
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import serializers

from .models import AvailabilitySlot, Category, Provider, UserProfile

User = get_user_model()


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

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "is_provider", "provider_slug", "cpf"]

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
        if value:
            return validate_cpf(value)
        return value

    def create(self, validated):
        cpf = validated.pop("cpf", "")
        user = User.objects.create_user(
            username=validated["email"],
            email=validated["email"],
            password=validated["password"],
            first_name=validated["name"],
        )
        if cpf:
            UserProfile.objects.create(user=user, cpf=cpf)
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
        ]

    def create(self, validated):
        slots_data = validated.pop("availability_slots", [])
        base = slugify(validated["name"]) or "prestador"
        slug = base
        i = 1
        while Provider.objects.filter(slug=slug).exists():
            i += 1
            slug = f"{base}-{i}"
        validated["slug"] = slug
        if not validated.get("avatar_url"):
            validated["avatar_url"] = "https://i.pravatar.cc/400?img=15"
        validated["status"] = "pending"
        provider = Provider.objects.create(**validated)
        for slot_data in slots_data:
            AvailabilitySlot.objects.create(provider=provider, **slot_data)
        return provider
