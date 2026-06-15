# PLANO DE IMPLEMENTAÇÃO — REALIZAR AVALIAÇÃO (REVIEW)

> **Versão:** 1.0 — 2026-06-15
> **Baseado em:** HIVEE Marketplace (Django 6 + React 19)
> **Feature:** Sistema de avaliação com nota e comentário após serviço realizado

---

## Sumário Executivo

Implementar um sistema completo de **avaliação pós-serviço** no HIVEE. Após um serviço ser concluído, o cliente poderá dar uma nota de 1 a 5 estrelas e escrever um comentário sobre o prestador. A avaliação atualiza em tempo real a nota média (`Provider.rating`) e o número total de avaliações (`Provider.reviews_count`).

**Pré-requisito:** Feature de "Serviços em Andamento" (rastreamento) — esta feature depende de um serviço com status `concluido` para liberar a avaliação.

---

## Stack da Feature

| Camada | Tecnologia |
|--------|-----------|
| Modelo | `Review` com nota 1-5, comentário, relação com Serviço + Provider + Cliente |
| Sinal | `django.db.models.signals` para recalcular `Provider.rating` + `reviews_count` |
| Backend | DRF ViewSet (mesmo padrão do `ProviderViewSet`) |
| Permissão | Só o **cliente contratante** do serviço pode avaliar; **uma avaliação por serviço** |
| Frontend | Componente `StarRating` reutilizável + modal/página de avaliação |
| Integração | A média de avaliações alimenta o algoritmo de recomendação (`_score` em `api_views.py`) |

---

## Modelo de Dados

### `Review` (novo — dentro de `catalog/models.py` ou novo app `ratings`)

```python
class Review(models.Model):
    """Avaliação de um serviço realizado, feita pelo cliente contratante.

    Regras:
    - Uma avaliação por serviço (unique_together: servico + reviewer)
    - Só pode avaliar serviços com status "concluido"
    - O reviewer deve ser o cliente que contratou o serviço
    """

    servico = models.ForeignKey(
        "servico.Servico", on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Serviço",
    )
    provider = models.ForeignKey(
        "catalog.Provider", on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Prestador",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="reviews_dados",
        verbose_name="Avaliador",
    )
    nota = models.PositiveSmallIntegerField(
        choices=[(1, "1 - Péssimo"), (2, "2 - Ruim"), (3, "3 - Regular"),
                 (4, "4 - Bom"), (5, "5 - Excelente")],
        verbose_name="Nota",
    )
    comentario = models.TextField(blank=True, verbose_name="Comentário")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("servico", "reviewer")
        ordering = ["-created_at"]
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"

    def __str__(self):
        return f"{'★' * self.nota}{'☆' * (5 - self.nota)} - {self.reviewer.first_name} sobre {self.provider.name}"
```

### Atualização Automática do Provider

Quando uma `Review` é criada/alterada/deletada, `Provider.rating` e `Provider.reviews_count` devem ser recalculados.

```python
# catalog/signals.py
from django.db.models import Avg, Count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def recalcular_rating_provider(sender, instance, **kwargs):
    provider = instance.provider
    agg = Review.objects.filter(provider=provider).aggregate(
        media=Avg("nota"), total=Count("id")
    )
    provider.rating = round(agg["media"] or 0, 2)
    provider.reviews_count = agg["total"] or 0
    provider.save(update_fields=["rating", "reviews_count"])
```

```python
# catalog/apps.py
class CatalogConfig(AppConfig):
    name = "catalog"

    def ready(self):
        import catalog.signals  # noqa
```

---

## API REST (Backend)

### Endpoints

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/reviews/?provider=<slug>` | Lista avaliações de um prestador | `AllowAny` |
| GET | `/api/reviews/{id}/` | Detalhe de uma avaliação | `AllowAny` |
| POST | `/api/servicos/{id}/avaliar/` | Criar avaliação para serviço concluído | `IsAuthenticated` (cliente) |
| PATCH | `/api/reviews/{id}/` | Editar própria avaliação | `IsAuthenticated` (dono) |
| DELETE | `/api/reviews/{id}/` | Deletar própria avaliação | `IsAuthenticated` (dono) |

### Serializer

```python
# catalog/serializers.py
class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()
    reviewer_avatar = serializers.SerializerMethodField()
    tempo_relativo = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id", "servico_id", "provider", "reviewer", "reviewer_name",
            "reviewer_avatar", "nota", "comentario", "tempo_relativo",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "reviewer", "created_at", "updated_at"]

    def get_reviewer_name(self, obj) -> str:
        return obj.reviewer.first_name or obj.reviewer.email.split("@")[0]

    def get_reviewer_avatar(self, obj) -> str | None:
        try:
            return obj.reviewer.profile.avatar_url if hasattr(obj.reviewer, "profile") else None
        except Exception:
            return None

    def get_tempo_relativo(self, obj) -> str:
        diff = timezone.now() - obj.created_at
        if diff.days > 365:
            return f"{diff.days // 365} ano(s) atrás"
        if diff.days > 30:
            return f"{diff.days // 30} mês(es) atrás"
        if diff.days > 0:
            return f"{diff.days} dia(s) atrás"
        if diff.seconds > 3600:
            return f"{diff.seconds // 3600}h atrás"
        return f"{max(1, diff.seconds // 60)}min atrás"
```

### ViewSet

```python
# catalog/views/api_views.py ou novo arquivo review_views.py

class ReviewViewSet(ViewSet):
    lookup_field = "id"

    def list(self, request):
        provider_slug = request.query_params.get("provider")
        qs = Review.objects.select_related("reviewer", "provider")
        if provider_slug:
            qs = qs.filter(provider__slug=provider_slug)
        return Response(ReviewSerializer(qs, many=True).data)

    def create(self, request, servico_id=None):
        """Vinculado a /api/servicos/{servico_id}/avaliar/"""
        from servico.models import Servico
        servico = get_object_or_404(Servico, id=servico_id)

        if servico.status != "concluido":
            return Response({"detail": "Serviço precisa estar concluído para ser avaliado."},
                            status=400)
        if servico.user != request.user:
            return Response({"detail": "Só o contratante pode avaliar este serviço."},
                            status=403)
        if Review.objects.filter(servico=servico, reviewer=request.user).exists():
            return Response({"detail": "Você já avaliou este serviço."},
                            status=409)

        serializer = ReviewSerializer(data={
            "servico_id": servico.id,
            "provider": servico.provider.id,
            "nota": request.data.get("nota"),
            "comentario": request.data.get("comentario", ""),
        })
        serializer.is_valid(raise_exception=True)
        review = serializer.save(reviewer=request.user)
        return Response(ReviewSerializer(review).data, status=201)

    def update(self, request, id=None):
        review = get_object_or_404(Review, id=id)
        if review.reviewer != request.user:
            return Response({"detail": "Você não pode editar esta avaliação."}, status=403)
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, id=None):
        review = get_object_or_404(Review, id=id)
        if review.reviewer != request.user:
            return Response({"detail": "Você não pode excluir esta avaliação."}, status=403)
        review.delete()
        return Response(status=204)
```

### URLs

```python
# catalog/urls.py (adicionar)
path("api/reviews/", ReviewViewSet.as_view({"get": "list"}), name="review-list"),
path("api/reviews/<int:id>/", ReviewViewSet.as_view({"get": "retrieve", "patch": "update", "delete": "destroy"}), name="review-detail"),
path("api/servicos/<int:servico_id>/avaliar/", ReviewViewSet.as_view({"post": "create"}), name="review-create"),
```

---

## Frontend

### 1. Componente `StarRating`

```tsx
// frontend/src/components/ui/StarRating.tsx
import { Star } from "lucide-react";

interface Props {
  value: number;
  onChange?: (value: number) => void;
  readonly?: boolean;
  size?: number;
}

export default function StarRating({ value, onChange, readonly = false, size = 24 }: Props) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={readonly}
          onClick={() => onChange?.(star)}
          className={`transition-colors ${
            readonly ? "cursor-default" : "cursor-pointer hover:scale-110"
          }`}
        >
          <Star
            size={size}
            className={
              star <= value
                ? "fill-gold-400 text-gold-400"
                : "text-zinc-600"
            }
          />
        </button>
      ))}
    </div>
  );
}
```

### 2. Modal de Avaliação

```tsx
// frontend/src/components/AvaliarServicoModal.tsx
import { useState } from "react";
import { api } from "@/lib/api";
import StarRating from "@/components/ui/StarRating";

interface Props {
  servicoId: number;
  providerName: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AvaliarServicoModal({ servicoId, providerName, onClose, onSuccess }: Props) {
  const [nota, setNota] = useState(0);
  const [comentario, setComentario] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit() {
    if (nota === 0) return;
    setSaving(true);
    try {
      await api.avaliarServico(servicoId, { nota, comentario });
      onSuccess();
    } catch {
      /* toast error */
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="surface w-full max-w-md rounded-3xl p-8">
        <h2 className="font-display text-2xl font-bold">Avaliar {providerName}</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Sua nota ajuda outros clientes a escolherem. Seja honesto(a).
        </p>

        <div className="mt-6 flex justify-center">
          <StarRating value={nota} onChange={setNota} size={36} />
        </div>

        <textarea
          value={comentario}
          onChange={(e) => setComentario(e.target.value)}
          placeholder="Conte como foi sua experiência (opcional)..."
          rows={4}
          className="mt-6 w-full rounded-2xl border border-white/10 bg-zinc-800/50 px-4 py-3 text-sm text-zinc-100 outline-none focus:ring-1 focus:ring-gold-500"
        />

        <div className="mt-6 flex gap-3">
          <button onClick={onClose} className="btn-ghost flex-1 py-3">Cancelar</button>
          <button
            onClick={submit}
            disabled={nota === 0 || saving}
            className="btn-gold flex-1 py-3 disabled:opacity-50"
          >
            {saving ? "Enviando..." : "Enviar avaliação"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

### 3. Seção de Reviews no Perfil do Prestador

```tsx
// ProviderProfile.tsx — adicionar abaixo do "Sobre"
import StarRating from "@/components/ui/StarRating";

// State
const [reviews, setReviews] = useState<Review[]>([]);

// Fetch
useEffect(() => {
  api.reviews({ provider: slug }).then(setReviews).catch(() => undefined);
}, [slug]);

// Render
<section className="surface mt-6 rounded-3xl p-6 sm:p-8">
  <h2 className="font-display text-2xl font-semibold">
    Avaliações <span className="text-gold">({reviews.length})</span>
  </h2>

  {reviews.length === 0 ? (
    <p className="mt-4 text-sm text-muted-foreground">
      Este profissional ainda não tem avaliações.
    </p>
  ) : (
    <div className="mt-6 space-y-6">
      {reviews.map((r) => (
        <div key={r.id} className="border-b border-white/10 pb-6 last:border-0">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gold-500/20 text-sm font-bold text-gold-300">
              {r.reviewer_name[0]?.toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-foreground">{r.reviewer_name}</p>
              <StarRating value={r.nota} readonly size={14} />
            </div>
            <span className="ml-auto text-xs text-muted-foreground">{r.tempo_relativo}</span>
          </div>
          {r.comentario && (
            <p className="mt-3 text-sm leading-relaxed text-foreground/80">{r.comentario}</p>
          )}
        </div>
      ))}
    </div>
  )}
</section>
```

### 4. Botão "Avaliar" na Página de Serviço

```tsx
// ServicoDetailPage.tsx
{servico.status === "concluido" && !servico.minha_avaliacao && (
  <button onClick={() => setAbrirModal(true)} className="btn-gold w-full py-3.5 text-base">
    <Star className="h-4 w-4" /> Avaliar serviço
  </button>
)}
```

### 5. TypeScript

```typescript
// frontend/src/types.ts — adicionar
export interface Review {
  id: number;
  servico_id: number;
  provider: number;
  reviewer: number;
  reviewer_name: string;
  reviewer_avatar: string | null;
  nota: number;
  comentario: string;
  tempo_relativo: string;
  created_at: string;
  updated_at: string;
}
```

---

## Fluxo Completo

```
1. Cliente contrata prestador → serviço "solicitado"
       ↓
2. [Rastreamento] Prestador inicia → "em_andamento"
       ↓
3. Prestador conclui → "concluido"
       ↓
4. Cliente vê botão "Avaliar serviço" na página do serviço
       ↓
5. Modal de avaliação aparece (1-5 estrelas + comentário opcional)
       ↓
6. POST /api/servicos/{id}/avaliar/ (valida: concluído, dono, único)
       ↓
7. Signal recalcula Provider.rating + reviews_count
       ↓
8. Nota aparece em tempo real no card/perfil do prestador
       ↓
9. Avaliação entra no algoritmo de recomendação (_score)
```

---

## Impacto no Score de Recomendação

O `_score()` em `api_views.py` já usa `provider.rating` e `provider.reviews_count`:

```python
RATING_WEIGHT = 42
rating_pts = (rating / MAX_RATING) * RATING_WEIGHT
review_pts = min(reviews / REVIEWS_SATURATION, 1.0) * REVIEWS_WEIGHT
```

Com avaliações reais:
- Prestadores bem avaliados sobem no ranking
- Prestadores novos (sem avaliações) têm `rating=0`, pontuam 0 em `RATING_WEIGHT`
- Mecanismo anti-fraude: só clientes que **contrataram e concluíram** o serviço podem avaliar

---

## Anti-Fraude e Moderação

| Regra | Implementação |
|-------|-------------|
| Só comprovados avaliam | Avaliação só permitida para `servico.user == request.user` |
| Uma avaliação por serviço | `unique_together = ("servico", "reviewer")` |
| Sem auto-avaliação | `reviewer` é o cliente, não o provider |
| Edição permitida | Só o dono da avaliação pode editar |
| Exclusão | Só o dono pode excluir (recalcula média) |
| Comentário opcional | Nota sozinha já é válida |

---

## Sprints de Implementação

### Sprint 1 — Modelo e Signal
- [ ] Adicionar `Review` model em `catalog/models.py`
- [ ] Criar `catalog/signals.py` com `recalcular_rating_provider`
- [ ] Configurar `CatalogConfig.ready()` em `apps.py`
- [ ] Migrations
- [ ] Admin registration

### Sprint 2 — API REST
- [ ] `ReviewSerializer` com campos virtuais
- [ ] `ReviewViewSet` (list, create/avaliar, update, destroy)
- [ ] Rotas `api/reviews/` e `api/servicos/{id}/avaliar/`
- [ ] Testes (criar, validar permissões, sinal, duplicata)

### Sprint 3 — Frontend
- [ ] `StarRating` component
- [ ] `AvaliarServicoModal`
- [ ] Seção de reviews em `ProviderProfile.tsx`
- [ ] Botão avaliar em `ServicoDetailPage`
- [ ] Tipos no `types.ts`
- [ ] Métodos no `api.ts`
- [ ] Rotas no React Router

### Sprint 4 — Integração e Refino
- [ ] Exibir nota média no card de busca (`ProviderCard.tsx`) — já existe
- [ ] Conectar com feature de rastreamento
- [ ] Notificar prestador por WhatsApp/chat quando receber review
- [ ] Dashboard de avaliações no admin

---

## Dependências

Nenhuma nova dependência Python. Tudo utiliza:
- `django.db.models.signals` (já incluso)
- `rest_framework` (já incluso)
- `lucide-react` (já incluso — `Star` já é usado)

---

## Links de Referência

- [Artigo: Sistema de Avaliação em Marketplaces — RoarBit](https://blog.roarbit.com.br/sistema-de-avaliacao-e-reputacao-em-marketplaces-como-implementar-corretamente/)
- [Django Signals Documentation](https://docs.djangoproject.com/en/6.0/topics/signals/)
- [DRF ViewSet Documentation](https://www.django-rest-framework.org/api-guide/viewsets/)
- [Projeto referência: coderr-backend (Review System)](https://github.com/RobbyRunge/coderr-backend)

---

## Anotações do Review (Código Atual)

| Item | Observação |
|------|-----------|
| `Provider.rating` e `reviews_count` já existem | Ótimo — o signal alimenta esses campos |
| `Star` icon da lucide-react já é usado no `ProviderCard` | Consistência visual mantida |
| Cliente é representado por `User` (auth) + `Cliente` (MTV) | Usar `User` como `reviewer` para compatibilidade com auth |
| `ProviderSwipe` não é review | É só like/dislike para recommendation |
| `ProviderProfile` já mostra rating | Só conectar com dados reais |
| Algoritmo `_score()` já pondera rating | Avaliações reais melhoram a recomendação |
| Serviço (`Servico`) é pré-requisito | Deve vir da feature de rastreamento |
