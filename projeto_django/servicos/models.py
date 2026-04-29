from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


# ============================================================
# PERFIL DE USUÁRIO — diferencia Cliente de Prestador
# ============================================================
class UserProfile(models.Model):
    TIPO_CHOICES = [
        ('CLIENTE', 'Cliente'),
        ('PRESTADOR', 'Prestador de Serviço'),
    ]
    PLANO_CHOICES = [
        ('BASICO', 'Basic — R$ 9,99/mês'),
        ('PREMIUM', 'Premium — R$ 100,00/mês'),
        ('NENHUM', 'Sem plano'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='CLIENTE')
    cidade = models.CharField(max_length=100, blank=True, default='')
    estado = models.CharField(max_length=2, blank=True, default='')
    telefone = models.CharField(max_length=20, blank=True, default='')
    # Campos exclusivos de CLIENTE
    plano = models.CharField(max_length=10, choices=PLANO_CHOICES, default='NENHUM')
    servicos_usados_mes = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.tipo})'

    def pode_contratar(self):
        """Verifica se o cliente ainda pode contratar com base no plano."""
        if self.tipo != 'CLIENTE':
            return False
        if self.plano == 'PREMIUM':
            return True
        if self.plano == 'BASICO' and self.servicos_usados_mes < 2:
            return True
        return False


# ============================================================
# CATEGORIA DE SERVIÇO
# ============================================================
class CategoriaServico(models.Model):
    ICONE_CHOICES = [
        ('⚡', 'Elétrica'),
        ('🔧', 'Hidráulica'),
        ('🧹', 'Limpeza'),
        ('🎨', 'Pintura'),
        ('🪚', 'Marcenaria'),
        ('❄️', 'Ar-Condicionado'),
        ('🏠', 'Reforma Geral'),
        ('📦', 'Mudança'),
        ('🌿', 'Jardinagem'),
        ('🔒', 'Segurança'),
        ('💻', 'Tecnologia'),
        ('🔨', 'Outros'),
    ]

    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icone = models.CharField(max_length=5, choices=ICONE_CHOICES, default='🔨')
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Categoria de Serviço'
        verbose_name_plural = 'Categorias de Serviços'
        ordering = ['nome']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.icone} {self.nome}'


# ============================================================
# PERFIL DO PRESTADOR
# ============================================================
class PrestadorPerfil(models.Model):
    STATUS_ADESAO = [
        ('PENDENTE', 'Pendente de Pagamento'),
        ('ATIVO', 'Ativo'),
        ('SUSPENSO', 'Suspenso'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='prestador_perfil')
    slug = models.SlugField(unique=True, blank=True)
    bio = models.TextField(max_length=500, blank=True, help_text='Apresentação curta (máx. 500 caracteres)')
    foto = models.ImageField(upload_to='prestadores/fotos/%Y/%m/', blank=True, null=True)
    especialidades = models.ManyToManyField(CategoriaServico, related_name='prestadores', blank=True)
    valor_hora = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cidade = models.CharField(max_length=100, default='')
    estado = models.CharField(max_length=2, default='')
    anos_experiencia = models.PositiveIntegerField(default=0)
    disponivel = models.BooleanField(default=True)
    # Monetização: taxa de adesão anual R$ 400,00
    status_adesao = models.CharField(max_length=10, choices=STATUS_ADESAO, default='PENDENTE')
    data_adesao = models.DateField(null=True, blank=True)
    # Estatísticas (calculadas via signals ou manualmente)
    total_servicos = models.PositiveIntegerField(default=0)
    nota_media = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de Prestador'
        verbose_name_plural = 'Perfis de Prestadores'
        ordering = ['-nota_media', '-total_servicos']

    def save(self, *args, **kwargs):
        if not self.slug:
            username = self.user.username
            base_slug = slugify(username)
            slug = base_slug
            n = 1
            while PrestadorPerfil.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Prestador: {self.user.get_full_name() or self.user.username}'

    def get_localizacao(self):
        if self.cidade and self.estado:
            return f'{self.cidade}/{self.estado}'
        return self.cidade or self.estado or 'Localização não informada'


# ============================================================
# CONTRATO DE SERVIÇO (substitui o Order)
# ============================================================
class Contrato(models.Model):
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('ACEITO', 'Aceito pelo Prestador'),
        ('EM_EXECUCAO', 'Em Execução'),
        ('CONCLUIDO', 'Concluído'),
        ('CANCELADO', 'Cancelado'),
        ('DISPUTADO', 'Em Disputa'),
    ]
    PAGAMENTO_STATUS = [
        ('AGUARDANDO', 'Aguardando pagamento'),
        ('RETIDO', 'Retido (Escrow)'),
        ('LIBERADO', 'Liberado ao Prestador'),
        ('REEMBOLSADO', 'Reembolsado ao Cliente'),
    ]

    cliente = models.ForeignKey(User, on_delete=models.PROTECT, related_name='contratos_como_cliente')
    prestador = models.ForeignKey(PrestadorPerfil, on_delete=models.SET_NULL, null=True, blank=True, related_name='contratos')

    categoria = models.ForeignKey(CategoriaServico, on_delete=models.SET_NULL, null=True)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    endereco_servico = models.CharField(max_length=300)
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_agendada = models.DateField(null=True, blank=True)
    hora_agendada = models.TimeField(null=True, blank=True)
    horas_estimadas = models.PositiveIntegerField(default=1)
    valor_acordado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Rastreio de status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDENTE')
    data_aceite = models.DateTimeField(null=True, blank=True)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    # Sistema de Escrow (simulado)
    status_pagamento = models.CharField(max_length=15, choices=PAGAMENTO_STATUS, default='AGUARDANDO')
    observacoes_prestador = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Contrato de Serviço'
        verbose_name_plural = 'Contratos de Serviços'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f'Contrato #{self.pk} — {self.titulo} ({self.get_status_display()})'

    def pode_avaliar(self):
        """Verifica se o contrato pode receber avaliação."""
        return self.status == 'CONCLUIDO' and not hasattr(self, 'avaliacao')


# ============================================================
# AVALIAÇÃO DO PRESTADOR
# ============================================================
class Avaliacao(models.Model):
    ESTRELAS_CHOICES = [(i, str(i)) for i in range(1, 6)]

    contrato = models.OneToOneField(Contrato, on_delete=models.CASCADE, related_name='avaliacao')
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avaliacoes_feitas')
    prestador = models.ForeignKey(PrestadorPerfil, on_delete=models.CASCADE, related_name='avaliacoes_recebidas')
    estrelas = models.PositiveSmallIntegerField(choices=ESTRELAS_CHOICES)
    comentario = models.TextField(max_length=1000, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.estrelas}★ para {self.prestador} por {self.cliente.username}'
