"""Populate the marketplace with fictitious-but-realistic providers.

    python manage.py seed              # 180 providers
    python manage.py seed --count 300  # custom amount

Everything here is generated data written to SQLite — the API never serves
hardcoded values.
"""
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from catalog.models import Category, Provider

fake = Faker("pt_BR")

# --- Categories ------------------------------------------------------------
CATEGORIES = [
    {
        "name": "Reformas & Construção",
        "icon": "Hammer",
        "accent": "#f59e0b",
        "tagline": "Pedreiros, mestres de obra e reformas",
        "rate": (45, 160),
        "headlines": [
            "Pedreiro e mestre de obras",
            "Especialista em reformas residenciais",
            "Construção, acabamento e ampliação",
        ],
        "skills": ["Alvenaria", "Reboco", "Piso", "Drywall", "Acabamento", "Telhado"],
    },
    {
        "name": "Elétrica",
        "icon": "Zap",
        "accent": "#eab308",
        "tagline": "Eletricistas residenciais e prediais",
        "rate": (60, 180),
        "headlines": [
            "Eletricista residencial",
            "Instalações e reparos elétricos",
            "Eletricista predial 24h",
        ],
        "skills": ["Instalação", "Quadro de luz", "Tomadas", "Iluminação", "Chuveiro", "Curto-circuito"],
    },
    {
        "name": "Encanamento",
        "icon": "Wrench",
        "accent": "#38bdf8",
        "tagline": "Encanadores e hidráulica em geral",
        "rate": (55, 170),
        "headlines": [
            "Encanador e reparos hidráulicos",
            "Caça-vazamentos profissional",
            "Hidráulica residencial e predial",
        ],
        "skills": ["Vazamentos", "Desentupimento", "Caixa d'água", "Torneiras", "Aquecedor", "Tubulação"],
    },
    {
        "name": "Pintura",
        "icon": "PaintRoller",
        "accent": "#f472b6",
        "tagline": "Pintores residenciais e comerciais",
        "rate": (40, 130),
        "headlines": [
            "Pintor residencial",
            "Pintura, textura e grafiato",
            "Pintura comercial e predial",
        ],
        "skills": ["Pintura interna", "Pintura externa", "Textura", "Grafiato", "Massa corrida", "Verniz"],
    },
    {
        "name": "Limpeza",
        "icon": "Sparkles",
        "accent": "#34d399",
        "tagline": "Diaristas e limpeza profissional",
        "rate": (25, 90),
        "headlines": [
            "Diarista e faxineira",
            "Limpeza pós-obra",
            "Limpeza pesada e detalhada",
        ],
        "skills": ["Faxina", "Pós-obra", "Passar roupa", "Vidros", "Limpeza pesada", "Organização"],
    },
    {
        "name": "Jardinagem",
        "icon": "Sprout",
        "accent": "#84cc16",
        "tagline": "Jardineiros e paisagismo",
        "rate": (35, 120),
        "headlines": [
            "Jardineiro e paisagista",
            "Manutenção de jardins",
            "Projetos de paisagismo",
        ],
        "skills": ["Poda", "Corte de grama", "Paisagismo", "Irrigação", "Plantio", "Adubação"],
    },
    {
        "name": "Beleza & Estética",
        "icon": "Scissors",
        "accent": "#c084fc",
        "tagline": "Cabelo, unhas, maquiagem e estética",
        "rate": (30, 150),
        "headlines": [
            "Cabeleireira e maquiadora",
            "Manicure e pedicure a domicílio",
            "Esteticista facial e corporal",
        ],
        "skills": ["Corte", "Coloração", "Manicure", "Maquiagem", "Sobrancelha", "Limpeza de pele"],
    },
    {
        "name": "Aulas & Reforço",
        "icon": "GraduationCap",
        "accent": "#60a5fa",
        "tagline": "Professores particulares e reforço",
        "rate": (40, 160),
        "headlines": [
            "Professor particular",
            "Reforço escolar e pré-vestibular",
            "Aulas de idiomas",
        ],
        "skills": ["Matemática", "Inglês", "Reforço", "ENEM", "Português", "Física"],
    },
    {
        "name": "Tecnologia & TI",
        "icon": "Laptop",
        "accent": "#22d3ee",
        "tagline": "Suporte técnico, redes e sites",
        "rate": (60, 220),
        "headlines": [
            "Suporte técnico e redes",
            "Desenvolvedor freelancer",
            "Conserto de computadores",
        ],
        "skills": ["Formatação", "Redes", "Sites", "Conserto de PC", "Suporte", "Wi-Fi"],
    },
    {
        "name": "Fotografia",
        "icon": "Camera",
        "accent": "#fb923c",
        "tagline": "Fotógrafos e filmagem",
        "rate": (80, 400),
        "headlines": [
            "Fotógrafo de eventos",
            "Fotografia e filmagem",
            "Ensaios e retratos",
        ],
        "skills": ["Eventos", "Casamentos", "Ensaios", "Edição", "Drone", "Vídeo"],
    },
    {
        "name": "Eventos & Festas",
        "icon": "PartyPopper",
        "accent": "#f43f5e",
        "tagline": "DJs, decoração e buffet",
        "rate": (50, 300),
        "headlines": [
            "DJ para festas e eventos",
            "Decoração de festas",
            "Buffet e equipe de garçons",
        ],
        "skills": ["DJ", "Decoração", "Buffet", "Garçom", "Som e luz", "Cerimonial"],
    },
    {
        "name": "Pets",
        "icon": "PawPrint",
        "accent": "#2dd4bf",
        "tagline": "Banho, tosa, passeio e adestramento",
        "rate": (30, 130),
        "headlines": [
            "Banho e tosa a domicílio",
            "Adestrador de cães",
            "Pet sitter e dog walker",
        ],
        "skills": ["Banho e tosa", "Adestramento", "Passeio", "Pet sitter", "Hospedagem", "Cuidados"],
    },
]

# --- Cities (real centres) -------------------------------------------------
CITIES = [
    {"city": "São Paulo", "state": "SP", "lat": -23.5613, "lng": -46.6565, "weight": 6,
     "bairros": ["Pinheiros", "Vila Mariana", "Moema", "Tatuapé", "Santana", "Itaim Bibi", "Lapa", "Butantã", "Mooca", "Perdizes"]},
    {"city": "Rio de Janeiro", "state": "RJ", "lat": -22.9068, "lng": -43.1729, "weight": 3,
     "bairros": ["Copacabana", "Tijuca", "Botafogo", "Barra da Tijuca", "Méier", "Flamengo"]},
    {"city": "Belo Horizonte", "state": "MG", "lat": -19.9167, "lng": -43.9345, "weight": 2,
     "bairros": ["Savassi", "Pampulha", "Buritis", "Funcionários", "Centro"]},
    {"city": "Curitiba", "state": "PR", "lat": -25.4284, "lng": -49.2733, "weight": 2,
     "bairros": ["Batel", "Água Verde", "Boa Vista", "Portão", "Centro"]},
    {"city": "Porto Alegre", "state": "RS", "lat": -30.0346, "lng": -51.2177, "weight": 2,
     "bairros": ["Moinhos de Vento", "Cidade Baixa", "Petrópolis", "Menino Deus"]},
    {"city": "Brasília", "state": "DF", "lat": -15.7939, "lng": -47.8828, "weight": 2,
     "bairros": ["Asa Sul", "Asa Norte", "Águas Claras", "Lago Sul"]},
    {"city": "Salvador", "state": "BA", "lat": -12.9777, "lng": -38.5016, "weight": 1,
     "bairros": ["Barra", "Pituba", "Itapuã", "Rio Vermelho"]},
    {"city": "Recife", "state": "PE", "lat": -8.0476, "lng": -34.8770, "weight": 1,
     "bairros": ["Boa Viagem", "Espinheiro", "Casa Forte", "Pina"]},
    {"city": "Fortaleza", "state": "CE", "lat": -3.7319, "lng": -38.5267, "weight": 1,
     "bairros": ["Aldeota", "Meireles", "Praia de Iracema", "Cocó"]},
    {"city": "Florianópolis", "state": "SC", "lat": -27.5949, "lng": -48.5482, "weight": 1,
     "bairros": ["Centro", "Trindade", "Lagoa da Conceição", "Campeche"]},
    {"city": "Campinas", "state": "SP", "lat": -22.9099, "lng": -47.0626, "weight": 1,
     "bairros": ["Cambuí", "Taquaral", "Barão Geraldo", "Centro"]},
    {"city": "Goiânia", "state": "GO", "lat": -16.6869, "lng": -49.2648, "weight": 1,
     "bairros": ["Setor Bueno", "Setor Oeste", "Jardim Goiás", "Setor Marista"]},
]

RESPONSE_TIMES = ["em poucos minutos", "em 15 min", "em 1 hora", "em algumas horas", "no mesmo dia"]
AVAILABILITY = ["Disponível hoje", "Disponível esta semana", "Agenda aberta", "Sob agendamento", "Disponível fins de semana"]


class Command(BaseCommand):
    help = "Seed the database with fictitious categories and providers."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=180, help="Number of providers.")
        parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility.")

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])
        Faker.seed(options["seed"])

        self.stdout.write("Limpando dados antigos...")
        Provider.objects.all().delete()
        Category.objects.all().delete()

        categories = []
        for order, c in enumerate(CATEGORIES):
            cat = Category.objects.create(
                name=c["name"],
                slug=slugify(c["name"]),
                icon=c["icon"],
                tagline=c["tagline"],
                accent=c["accent"],
                order=order,
            )
            categories.append((cat, c))
        self.stdout.write(self.style.SUCCESS(f"{len(categories)} categorias criadas."))

        city_pool = []
        for city in CITIES:
            city_pool.extend([city] * city["weight"])

        count = options["count"]
        used_slugs: set[str] = set()
        providers = []

        for i in range(count):
            cat, meta = random.choice(categories)
            city = random.choice(city_pool)

            name = fake.name()
            base_slug = slugify(name)
            slug = f"{base_slug}-{i}"
            while slug in used_slugs:
                slug = f"{base_slug}-{i}-{random.randint(1, 999)}"
            used_slugs.add(slug)

            # Ratings skew high, with a long tail of merely-good pros.
            if random.random() < 0.12:
                rating = round(random.uniform(3.7, 4.3), 2)
            else:
                rating = round(random.uniform(4.4, 5.0), 2)

            reviews = int(random.triangular(4, 520, 70))
            jobs = reviews + random.randint(0, reviews * 3) + random.randint(5, 60)

            lo, hi = meta["rate"]
            hourly = round(random.uniform(lo, hi) / 5) * 5

            img = (i % 70) + 1
            avatar = f"https://i.pravatar.cc/400?img={img}"

            providers.append(
                Provider(
                    name=name,
                    slug=slug,
                    headline=random.choice(meta["headlines"]),
                    bio=fake.paragraph(nb_sentences=3),
                    category=cat,
                    avatar_url=avatar,
                    cover_url="",
                    rating=rating,
                    reviews_count=reviews,
                    jobs_done=jobs,
                    hourly_rate=hourly,
                    currency="BRL",
                    city=city["city"],
                    neighborhood=random.choice(city["bairros"]),
                    state=city["state"],
                    latitude=round(city["lat"] + random.uniform(-0.05, 0.05), 6),
                    longitude=round(city["lng"] + random.uniform(-0.05, 0.05), 6),
                    verified=random.random() < 0.82,
                    top_rated=rating >= 4.8 and reviews > 60,
                    response_time=random.choice(RESPONSE_TIMES),
                    availability=random.choice(AVAILABILITY),
                    skills=random.sample(meta["skills"], k=random.randint(3, 5)),
                    member_since=random.randint(2016, 2024),
                    status="approved",
                )
            )

        Provider.objects.bulk_create(providers)
        self.stdout.write(self.style.SUCCESS(f"{len(providers)} prestadores criados."))
        self.stdout.write(self.style.SUCCESS("Seed concluido com sucesso."))
