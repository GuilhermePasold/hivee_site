# Análise — Feature de Cadastro de Demanda

## 1. Visão Geral

**Problema:** Um cliente (usuário comum) não encontra um prestador específico e quer
**publicar uma demanda** — ex.: "quero alguém para pintar minha casa" — para que
prestadores verificados vejam e se ofereçam para realizar o serviço.

**Modelo de referência:** TaskRabbit (cliente posta tarefa, prestadores se candidatam)
com elementos do modelo Thumbtack (cliente descreve o que precisa, prestadores pagam
para ter acesso ao lead).

**Público-alvo:**
- **Clientes:** Qualquer usuário logado (não precisa ser prestador)
- **Prestadores:** Apenas prestadores **verificados** (`is_provider === true` e
  `provider_status === "approved"`) podem ver e se oferecer em demandas abertas

---

## 2. Análise do Código Atual

### 2.1 Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 19 + Vite 6 + TypeScript + Tailwind v4 + React Router v7 |
| Backend | Django 6 + DRF + SQLite |
| Auth | Token httpOnly cookie |
| Ícones | lucide-react |
| Animações | Framer Motion |

### 2.2 O que já existe que pode ser reutilizado

- **Autenticação** (`AuthContext.tsx`): `user.is_provider` e `user.provider_status`
  já vêm do backend, prontos para controle de acesso condicional
- **Categorias** (`Category` model + `/api/categories/`): podem ser usadas para
  classificar demandas
- **Estilo glassmorfismo + cores gold/dark**: consistência visual garantida
- **Componentes UI**: `Avatar`, `Icon`, `GlassSelect`, botões `btn-ghost`/`btn-gold`

### 2.3 O que NÃO existe (gaps identificados)

| Item | Status |
|---|---|
| Modelo `Demand` no banco | ❌ Não existe |
| API REST de demandas | ❌ Nenhum endpoint |
| Página de criar demanda | ❌ Precisa ser criada |
| Feed de demandas abertas para prestadores | ❌ Precisa ser criado |
| Botão "Oferecer-se" / "Candidatar-se" | ❌ Não existe |
| Notificação ao cliente quando receber oferta | ❌ Não existe |
| Navbar com link condicional para prestadores | ❌ Links fixos, sem variação por role |
| Tipos TypeScript para demanda/oferta | ❌ Não existem |

---

## 3. Modelo de Dados Proposto

### 3.1 Demand (backend/catalog/models.py)

```python
class Demand(models.Model):
    """Uma demanda publicada por um cliente para prestadores se candidatarem."""

    STATUS_CHOICES = [
        ("open", "Aberta"),
        ("in_progress", "Em andamento"),
        ("closed", "Encerrada"),
        ("cancelled", "Cancelada"),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="demands"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="demands"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="demands")

    # Localização (pode ser diferente da do cliente)
    city = models.CharField(max_length=80, blank=True, default="")
    neighborhood = models.CharField(max_length=80, blank=True, default="")
    state = models.CharField(max_length=2, blank=True, default="")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Prazo e orçamento
    preferred_schedule = models.CharField(
        max_length=160, blank=True, default="",
        help_text="Ex.: 'Segunda-feira de manhã' ou 'Até 15 de julho'"
    )
    budget_hint = models.CharField(
        max_length=80, blank=True, default="",
        help_text="Ex.: 'Até R$ 500' ou 'A combinar'"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    offer_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demanda"
        verbose_name_plural = "Demandas"

    def __str__(self):
        return f"{self.title} — {self.client.email}"
```

### 3.2 DemandOffer (candidatura do prestador)

```python
class DemandOffer(models.Model):
    """Um prestador se oferecendo para realizar uma demanda."""

    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("accepted", "Aceito"),
        ("rejected", "Recusado"),
    ]

    demand = models.ForeignKey(
        Demand, on_delete=models.CASCADE, related_name="offers"
    )
    provider = models.ForeignKey(
        Provider, on_delete=models.CASCADE, related_name="demand_offers"
    )
    message = models.TextField(
        blank=True, default="",
        help_text="Mensagem do prestador para o cliente"
    )
    suggested_value = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("demand", "provider")
        ordering = ["-created_at"]
        verbose_name = "Oferta de demanda"
        verbose_name_plural = "Ofertas de demandas"

    def __str__(self):
        return f"{self.provider.name} → {self.demand.title}"
```

### 3.3 Tipos TypeScript (frontend/src/types.ts)

```typescript
export type DemandStatus = "open" | "in_progress" | "closed" | "cancelled";

export interface Demand {
  id: number;
  client_name: string;
  client_id: number;
  title: string;
  description: string;
  category: Category | null;
  tags: string[];
  city: string;
  neighborhood: string;
  state: string;
  latitude: number | null;
  longitude: number | null;
  preferred_schedule: string;
  budget_hint: string;
  status: DemandStatus;
  offer_count: number;
  created_at: string;
  has_my_offer?: boolean; // true se o prestador logado já se ofereceu
  distance_km?: number | null;
}

export type DemandOfferStatus = "pending" | "accepted" | "rejected";

export interface DemandOffer {
  id: number;
  demand_id: number;
  provider: Provider;
  message: string;
  suggested_value: number | null;
  status: DemandOfferStatus;
  created_at: string;
}

export interface CreateDemandPayload {
  title: string;
  description: string;
  category_slug?: string;
  city?: string;
  neighborhood?: string;
  state?: string;
  latitude?: number;
  longitude?: number;
  preferred_schedule?: string;
  budget_hint?: string;
}
```

---

## 4. API Endpoints

### 4.1 Backend (backend/catalog/urls.py)

| Método | Rota | Descrição | Autenticação |
|---|---|---|---|
| GET | `/api/demands/` | Listar demandas **abertas** para prestadores + demandas do próprio cliente | Obrigatória |
| POST | `/api/demands/` | Criar nova demanda | Obrigatória |
| GET | `/api/demands/:id/` | Detalhe da demanda + ofertas (se for o cliente ou prestador candidatado) | Obrigatória |
| PATCH | `/api/demands/:id/` | Atualizar demanda (só o dono) | Obrigatória |
| POST | `/api/demands/:id/offers/` | Prestador se oferece para a demanda | Obrigatória + provider verified |
| GET | `/api/demands/:id/offers/` | Listar ofertas de uma demanda (só o dono vê) | Obrigatória |
| PATCH | `/api/demands/:id/offers/:oid/` | Aceitar/recusar oferta (só o dono) | Obrigatória |
| GET | `/api/my-demands/` | Demandas do cliente logado | Obrigatória |
| GET | `/api/my-offers/` | Ofertas do prestador logado | Obrigatória |

### 4.2 Regras de negócio por endpoint

- **GET /api/demands/**: Se `user.is_provider && user.provider_status === "approved"`,
  retorna demandas com `status=open`. Se não, retorna apenas as demandas do próprio
  `user` (cliente).
- **POST /api/demands/**: Qualquer usuário autenticado pode criar uma demanda. Ao
  criar, um sinal (Django signal) pode disparar notificações para prestadores da
  mesma categoria + cidade.
- **POST /api/demands/:id/offers/**: Apenas prestadores com `provider_status === "approved"`
  podem se oferecer. A oferta fica `status=pending` até o cliente aceitar/recusar.
- **PATCH /api/demands/:id/offers/:oid/**: Só o **dono da demanda** pode aceitar
  (`status=accepted`) ou recusar (`status=rejected`) uma oferta.

---

## 5. Frontend — Novas Páginas e Rotas

### 5.1 Rotas (frontend/src/main.tsx)

```typescript
<Route path="/criar-demanda" element={<CriarDemanda />} />
<Route path="/demandas" element={<ListarDemandas />} />
<Route path="/demanda/:id" element={<DetalheDemanda />} />
<Route path="/minhas-demandas" element={<MinhasDemandas />} />
<Route path="/minhas-ofertas" element={<MinhasOfertas />} />
```

### 5.2 Páginas a criar

| Página | Arquivo | Descrição |
|---|---|---|
| `CriarDemanda.tsx` | `src/pages/CriarDemanda.tsx` | Formulário: título, descrição, categoria, local, prazo, orçamento |
| `ListarDemandas.tsx` | `src/pages/ListarDemandas.tsx` | Feed de demandas abertas (só para prestadores verified) |
| `DetalheDemanda.tsx` | `src/pages/DetalheDemanda.tsx` | Detalhe + ofertas (cliente vê ofertas, prestador vê botão de ofertar) |
| `MinhasDemandas.tsx` | `src/pages/MinhasDemandas.tsx` | Painel do cliente: demandas que criou + status |
| `MinhasOfertas.tsx` | `src/pages/MinhasOfertas.tsx` | Painel do prestador: ofertas que fez + status |

### 5.3 Páginas a modificar

#### Navbar.tsx

O link **"Demandas"** deve aparecer **apenas** para prestadores verificados:

```typescript
const LINKS = [
  { label: "Início", to: "/" },
  { label: "Buscar", to: "/buscar" },
  { label: "Meu Perfil", to: "/minha-conta" },
];

// Condicional: se user?.is_provider && user?.provider_status === "approved"
//   → adicionar { label: "Demandas", to: "/demandas" }
```

Também convém adicionar um link rápido **"Criar demanda"** no `/minha-conta`
para clientes que não são prestadores (ao lado do "Buscar profissionais").

#### MinhaConta.tsx

Adicionar uma nova tab ou seção chamada **"Minhas demandas"** que lista as
demandas do cliente com status (aberta, em andamento, encerrada) e link para
criar nova.

#### Register.tsx (opcional)

Após o cadastro, sugerir ao cliente: "Precisa de um serviço? Publique uma
demanda agora."

---

## 6. Fluxo Completo

### 6.1 Cliente cria uma demanda

```
1. Cliente acessa /minha-conta → clica "Criar demanda"
2. Preenche formulário em /criar-demanda:
   - Título (ex.: "Pintar parede da sala")
   - Descrição detalhada
   - Categoria (dropdown → /api/categories/)
   - Local (cidade/bairro/estado + geolocalização opcional)
   - Prazo preferencial (texto livre)
   - Sugestão de orçamento (texto livre)
3. POST /api/demands/ → demanda criada com status=open
4. Cliente é redirecionado para /minhas-demandas
```

### 6.2 Prestador vê e se oferece

```
1. Prestador verified vê link "Demandas" no header
2. Acessa /demandas → GET /api/demands/ (só demandas abertas)
3. Vê cards com título, descrição resumida, categoria, local, prazo, orçamento
4. Clica em uma → /demanda/:id → GET /api/demands/:id/
5. Vê detalhes + se já se candidatou ou não (has_my_offer)
6. Clica "Oferecer serviço" → modal/form:
   - Mensagem para o cliente (ex.: "Tenho 10 anos de experiência...")
   - Valor sugerido (opcional)
7. POST /api/demands/:id/offers/ → oferta criada com status=pending
```

### 6.3 Cliente avalia ofertas

```
1. Cliente acessa /minhas-demandas → vê lista de demandas
2. Clica em uma demanda → /demanda/:id
3. Aba "Ofertas" → GET /api/demands/:id/offers/
4. Vê cards dos prestadores que se ofereceram:
   - Nome, avatar, categoria, rating
   - Mensagem do prestador
   - Valor sugerido
5. Clica "Aceitar" → PATCH /api/demands/:id/offers/:oid/ { status: "accepted" }
   → demanda muda para status=in_progress
   → Demais ofertas são automaticamente recusadas
6. Clica "Recusar" → PATCH { status: "rejected" }
```

---

## 7. Regras de Negócio Detalhadas

| Regra | Descrição |
|---|---|
| Quem cria | Qualquer usuário autenticado pode criar demanda |
| Quem vê demandas abertas | Apenas prestadores **verificados** (`provider_status === "approved"`) |
| Quem se oferece | Apenas prestadores verificados (um prestador por demanda, uma oferta) |
| Cliente vê ofertas | Só o dono da demanda vê as ofertas recebidas |
| Limite de ofertas | Um prestador só pode fazer **uma** oferta por demanda (unique_together) |
| Aceitação | Ao aceitar uma oferta, as demais viram `rejected` automaticamente |
| Encerramento | Cliente pode encerrar demanda manualmente a qualquer momento |
| Cancelamento | Cliente pode cancelar demanda em aberto a qualquer momento |
| Exclusão | Demanda com ofertas não pode ser excluída (apenas cancelada) |

---

## 8. Considerações de UX/UI

### 8.1 Design System (consistente com o existente)

- **Cards de demanda**: mesmo padrão glassmorphism dos cards de prestador
- **Cores**: fundo escuro, gold accents (#eab308/#facc15), badges de status
- **Tipografia**: Inter (body) + font-display (títulos)
- **Ícones**: lucide-react (`ClipboardList`, `Handshake`, `MailQuestion`, `CircleDollarSign`)

### 8.2 Estados

Cada página deve tratar:

- **Loading**: Skeleton com `animate-pulse` (padrão do projeto)
- **Empty**: Ilustração + texto + CTA (ex.: "Nenhuma demanda publicada ainda")
- **Error**: Toast ou inline error com retry
- **Success**: Feedback visual + redirect

### 8.3 Badges de Status

| Status | Cor |
|---|---|
| `open` (aberta) | Verde (`text-emerald-400`) |
| `in_progress` | Azul (`text-sky-400`) |
| `closed` | Gold / neutro (`text-gold-400`) |
| `cancelled` | Vermelho (`text-rose-400`) |
| `pending` (oferta) | Âmbar (`text-amber-400`) |
| `accepted` (oferta) | Verde (`text-emerald-400`) |
| `rejected` (oferta) | Vermelho (`text-rose-400`) |

### 8.4 Modal de "Oferecer-se"

- Trigger: botão `btn-gold` com texto "Oferecer serviço"
- Modal glass com formulário inline:
  - Campo de mensagem (textarea, obrigatório)
  - Campo de valor sugerido (input numérico, opcional)
  - Botão "Enviar oferta" + "Cancelar"
- Após enviar: feedback de sucesso, botão desabilitado

---

## 9. Plano de Implementação Sugerido

### Fase 1 — Backend (modelos + API)

1. Criar modelos `Demand` e `DemandOffer` em `backend/catalog/models.py`
2. Criar serializers (`DemandSerializer`, `DemandOfferSerializer`,
   `CreateDemandSerializer`, `CreateOfferSerializer`)
3. Criar `DemandViewSet` em `backend/catalog/views/api_views.py`
4. Registrar rotas em `backend/catalog/urls.py`
5. Rodar `makemigrations` + `migrate`

### Fase 2 — Frontend (tipos + API + páginas)

1. Adicionar tipos TypeScript em `frontend/src/types.ts`
2. Adicionar métodos `api.demands.*` em `frontend/src/lib/api.ts`
3. Criar páginas: `CriarDemanda`, `ListarDemandas`, `DetalheDemanda`,
   `MinhasDemandas`, `MinhasOfertas`
4. Modificar `Navbar.tsx` para link condicional
5. Modificar `MinhaConta.tsx` para incluir seção de demandas
6. Registrar rotas em `frontend/src/main.tsx`

### Fase 3 — Integração e refinamentos

1. Implementar notificações (push ou in-app) quando prestador se oferecer
2. Adicionar filtros no feed de demandas (categoria, cidade, data)
3. Limitar número de ofertas que um prestador pode fazer por dia (anti-spam)
4. Adicionar página de busca de demandas para prestadores

---

## 10. Riscos e Pontos de Atenção

| Risco | Mitigação |
|---|---|
| Prestador assediar cliente | Botão "Denunciar" + moderação manual |
| Spam de ofertas | Rate limiting por prestador/dia |
| Demanda fictícia | Cliente precisa ter conta com CPF verificado |
| Prestador não verificado ver demandas | Validar `provider_status === "approved"` no backend |
| Cliente não encerrar demanda | Timeout automático após 30 dias sem atividade |
| Dados sensíveis (endereço) | Exibir apenas cidade/bairro (não endereço completo) |

---

## 11. Referências

- **TaskRabbit**: Cliente posta tarefa, prestadores se candidatam
  (fonte: [How to build a home service website like Thumbtack or TaskRabbit](https://www.fatbit.com/fab/build-home-service-marketplace-thumbtack-taskrabbit))
- **Thumbtack**: Cliente descreve projeto, prestadores pagam por lead
  (fonte: [Thumbtack Business Model](https://www.brineweb.com/blog/thumbtack-business-model-how-thumbtack-works-and-makes-money))
- **Modelo híbrido**: Cliente publica grátis, prestador verificado paga para ver
  demandas relevantes (modelo de monetização futura)
- **Padrão HIVEE**: Dark mode + glassmorphism + gold accents + Framer Motion
