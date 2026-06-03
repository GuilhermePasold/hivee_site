from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import serializers

from .models import Category, Provider

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    provider_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "slug", "name", "icon", "tagline", "accent", "provider_count"]


class ProviderSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    rating = serializers.FloatField()
    hourly_rate = serializers.FloatField()
    distance_km = serializers.SerializerMethodField()

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
            "skills",
            "member_since",
        ]

    def get_distance_km(self, obj):
        # `distance_km` is attached by the view when a location is provided.
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

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "is_provider", "provider_slug"]

    def get_is_provider(self, obj):
        return obj.provider_profiles.exists()

    def get_provider_slug(self, obj):
        profile = obj.provider_profiles.first()
        return profile.slug if profile else None


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_email(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return value

    def create(self, validated):
        user = User.objects.create_user(
            username=validated["email"],
            email=validated["email"],
            password=validated["password"],
            first_name=validated["name"],
        )
        return user


class ProviderWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field="slug", queryset=Category.objects.all()
    )

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
            "skills",
        ]

    def create(self, validated):
        base = slugify(validated["name"]) or "prestador"
        slug = base
        i = 1
        while Provider.objects.filter(slug=slug).exists():
            i += 1
            slug = f"{base}-{i}"
        validated["slug"] = slug
        if not validated.get("avatar_url"):
            validated["avatar_url"] = "https://i.pravatar.cc/400?img=15"
        return Provider.objects.create(**validated)
