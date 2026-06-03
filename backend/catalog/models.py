from django.conf import settings
from django.db import models


class Category(models.Model):
    """A service category."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    icon = models.CharField(
        max_length=40,
        help_text="lucide-react icon name in PascalCase (e.g. 'Wrench').",
    )
    tagline = models.CharField(max_length=140, blank=True)
    accent = models.CharField(max_length=7, default="#eab308", help_text="Hex accent color.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self) -> str:
        return self.name


class Provider(models.Model):
    """A service provider listed on the marketplace."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    headline = models.CharField(max_length=160)
    bio = models.TextField(blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="providers"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="provider_profiles",
    )

    avatar_url = models.URLField()
    cover_url = models.URLField(blank=True)

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    reviews_count = models.PositiveIntegerField(default=0)
    jobs_done = models.PositiveIntegerField(default=0)

    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="BRL")

    city = models.CharField(max_length=80)
    neighborhood = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=2, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    verified = models.BooleanField(default=False)
    top_rated = models.BooleanField(default=False)
    response_time = models.CharField(max_length=40, default="em 1 hora")
    availability = models.CharField(max_length=60, default="Disponível esta semana")
    skills = models.JSONField(default=list)
    member_since = models.PositiveIntegerField(default=2022)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-top_rated", "-rating", "-reviews_count"]
        verbose_name = "Prestador"
        verbose_name_plural = "Prestadores"

    def __str__(self) -> str:
        return f"{self.name} - {self.category.name}"


class ProviderImage(models.Model):
    """Optional gallery image for a service provider."""

    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="providers/gallery/%Y/%m/%d/")
    alt_text = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Imagem do prestador"
        verbose_name_plural = "Imagens dos prestadores"

    def __str__(self) -> str:
        return self.alt_text or f"Imagem de {self.provider.name}"


class Cliente(models.Model):
    """Classic MTV customer record, independent from DRF token auth."""

    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15)
    senha = models.CharField(max_length=128)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self) -> str:
        return self.nome
