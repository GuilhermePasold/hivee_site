# PLANO DE IMPLEMENTAÇÃO — CANCELAMENTO DE REQUISIÇÃO EM ABERTO

> **Versão:** 1.0 — 2026-06-15
> **Baseado em:** HIVEE Marketplace (Django 6 + React 19)
> **Feature:** Cancelamento de uma requisição de serviço que ainda está pendente de aprovação

---

## Regras de Negócio

| # | Regra |
|---|-------|
| 1 | Só pode cancelar um serviço com status **`solicitado`** (requisição em aberto) |
| 2 | **Cliente** pode cancelar a própria solicitação |
| 3 | **Prestador** NÃO usa `cancelar` — usa `rejeitar` já definido em `IMPL_AGENDAMENTO.md` |
| 4 | Motivo do cancelamento é **opcional** mas incentivado (coleta para analytics) |
| 5 | Após cancelamento, o horário solicitado é **liberado** para outros agendamentos |
| 6 | Cancelamento **não ativa** o bloqueio de avaliação obrigatória (só `finalizado` sem review bloqueia) |
| 7 | `cancelado` é **estado terminal** — não é possível reverter |
| 8 | Nenhuma transação financeira envolvida (serviço em `solicitado` ainda não gerou cobrança) |

---

## Endpoint

```
POST /api/servicos/{id}/cancelar/
```

### Request Body (opcional)

```json
{
  "motivo": "Encontrei outro prestador com preço melhor"
}
```

### Resposta (sucesso — 200 OK)

```json
{
  "id": 42,
  "provider": 7,
  "cliente_user": 1,
  "cliente_nome": "Maria Silva",
  "descricao": "Trocar chuveiro elétrico",
  "endereco": "Rua das Flores, 123 - Centro",
  "data_solicitada": "2026-06-20T14:00:00-03:00",
  "valor_combinado": 120.00,
  "status": "cancelado",
  "motivo_cancelamento": "Encontrei outro prestador com preço melhor",
  "cancelado_em": "2026-06-16T10:30:00-03:00",
  "eventos_rastreamento": [
    {
      "tipo": "cancelamento",
      "descricao": "Cliente cancelou a solicitação",
      "created_at": "2026-06-16T10:30:00-03:00"
    }
  ]
}
```

### Resposta (erro — 400)

```json
{
  "detail": "Só é possível cancelar serviços com status 'solicitado'."
}
```

### Resposta (erro — 403)

```json
{
  "detail": "Você não tem permissão para cancelar este serviço."
}
```

---

## Backend — Implementação

### Localização

```
backend/billing/views.py  →  ServicoViewSet
```

### Código

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from django.shortcuts import get_object_or_404
from ..models import Servico, RastreamentoEvento


class ServicoViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """Cliente cancela uma solicitação em aberto (status = solicitado)."""
        servico = get_object_or_404(Servico, id=pk)

        # Só o cliente que solicitou pode cancelar
        if servico.cliente_user != request.user:
            raise PermissionDenied("Você não tem permissão para cancelar este serviço.")

        # Só pode cancelar se estiver em "solicitado"
        if servico.status != "solicitado":
            return Response(
                {"detail": "Só é possível cancelar serviços com status 'solicitado'."},
                status=400,
            )

        # Coleta motivo (opcional)
        motivo = request.data.get("motivo", "")

        # Atualiza status
        servico.status = "cancelado"
        servico.motivo_cancelamento = motivo
        servico.cancelado_em = timezone.now()
        servico.save(update_fields=["status", "motivo_cancelamento", "cancelado_em"])

        # Registra evento de rastreamento
        RastreamentoEvento.objects.create(
            servico=servico,
            tipo="cancelamento",
            descricao="Cliente cancelou a solicitação",
        )

        # Notifica o prestador
        _notificar_prestador(servico, "servico_cancelado")

        return Response(ServicoSerializer(servico).data)
```

---

## Modelo — Campo Adicional

Adicionar campo `motivo_cancelamento` e `cancelado_em` ao `Servico`:

```python
# backend/billing/models.py — class Servico

# Campos novos (já existe motivo_rejeicao para rejeição do prestador)
motivo_cancelamento = models.TextField(blank=True, verbose_name="Motivo do cancelamento")
cancelado_em = models.DateTimeField(null=True, blank=True, verbose_name="Data/hora do cancelamento")
```

---

## Notificação

```python
# backend/billing/notificacoes.py — adicionar ao dicionário do prestador

def _notificar_prestador(servico, tipo):
    msg_map = {
        # ... mensagens existentes ...
        "servico_cancelado": (
            f"❌ {servico.cliente_nome} cancelou a solicitação de serviço.\n"
            f"Serviço: {servico.descricao[:100]}...\n"
            + (f"Motivo: {servico.motivo_cancelamento}" if servico.motivo_cancelamento else "")
        ),
    }
    # Reutiliza a mesma função de envio (WAHA + WebSocket)
    _enviar_notificacao_prestador(servico, msg_map[tipo])
```

---

## Máquina de Estados (Atualizada)

```
solicitado ──→ rejeitado  (prestador recusou)
     │
     ├──→ cancelado  ←── cliente desistiu (ESTA FEATURE)
     │
     ├──→ em_andamento  (prestador aprovou)
     │       │
     │       └──→ concluido ──→ aguardando_pagamento ──→ finalizado
     │                                                        │
     │                                                   [avaliação obrigatória]
     │
     └──→ reagendamento_sugerido ──→ em_andamento | cancelado
```

---

## Interação com Outras Features

| Feature | Impacto |
|---------|---------|
| **Rastreamento** | Cria `RastreamentoEvento` tipo `cancelamento` na timeline do serviço |
| **Notificação** | Prestador recebe notificação via WhatsApp + WebSocket |
| **Disponibilidade** | Horário do serviço cancelado fica livre no `AvailabilitySlot` |
| **Avaliação Obrigatória** | Sem impacto — `_verificar_bloqueio_avaliacao` só olha `status=finalizado` |
| **Pagamento** | Sem impacto — serviço em `solicitado` nunca gerou cobrança |
| **`jobs_done`** | Sem impacto — `jobs_done` só é incrementado no pagamento |

---

## Casos de Borda

| Cenário | Comportamento |
|---------|---------------|
| Serviço em `em_andamento` → tentar cancelar | Erro 400: "Só é possível cancelar serviços com status 'solicitado'" |
| Serviço em `concluido` → tentar cancelar | Erro 400 |
| Serviço em `finalizado` → tentar cancelar | Erro 400 (já foi pago, usaria disputa/reembolso) |
| Serviço em `rejeitado` → tentar cancelar | Erro 400 (já foi rejeitado pelo prestador) |
| Outro usuário tenta cancelar | Erro 403 PermissionDenied |
| Cancelar sem motivo | OK — `motivo_cancelamento` fica vazio |
| Cancelar e depois criar novo serviço | OK — sem restrição |
| Prestador tenta usar `cancelar` | Erro 403 (não é o `cliente_user`) |

---

## Testes

```python
# backend/billing/tests.py

class CancelarServicoTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.cliente = self.criar_usuario("cliente@test.com", "cliente123")
        self.prestador_user = self.criar_usuario("prestador@test.com", "prest123")
        self.provider = self.criar_provider(owner=self.prestador_user)
        self.servico = Servico.objects.create(
            provider=self.provider,
            cliente_user=self.cliente,
            cliente_nome="Cliente Teste",
            descricao="Teste de cancelamento",
            endereco="Rua A, 123",
            data_solicitada=timezone.now() + timedelta(days=1),
            valor_combinado=Decimal("100.00"),
            status="solicitado",
        )

    def test_cancelar_com_sucesso(self):
        self.client.force_authenticate(user=self.cliente)
        res = self.client.post(f"/api/servicos/{self.servico.id}/cancelar/")
        self.assertEqual(res.status_code, 200)
        self.servico.refresh_from_db()
        self.assertEqual(self.servico.status, "cancelado")

    def test_cancelar_com_motivo(self):
        self.client.force_authenticate(user=self.cliente)
        res = self.client.post(f"/api/servicos/{self.servico.id}/cancelar/", {
            "motivo": "Preço muito alto"
        }, format="json")
        self.assertEqual(res.status_code, 200)
        self.servico.refresh_from_db()
        self.assertEqual(self.servico.motivo_cancelamento, "Preço muito alto")

    def test_cancelar_sem_motivo(self):
        self.client.force_authenticate(user=self.cliente)
        res = self.client.post(f"/api/servicos/{self.servico.id}/cancelar/")
        self.assertEqual(res.status_code, 200)
        self.servico.refresh_from_db()
        self.assertEqual(self.servico.motivo_cancelamento, "")

    def test_nao_pode_cancelar_se_nao_for_cliente(self):
        outro = self.criar_usuario("outro@test.com", "outro123")
        self.client.force_authenticate(user=outro)
        res = self.client.post(f"/api/servicos/{self.servico.id}/cancelar/")
        self.assertEqual(res.status_code, 403)

    def test_nao_pode_cancelar_em_andamento(self):
        self.servico.status = "em_andamento"
        self.servico.save()
        self.client.force_authenticate(user=self.cliente)
        res = self.client.post(f"/api/servicos/{self.servico.id}/cancelar/")
        self.assertEqual(res.status_code, 400)
        self.assertIn("solicitado", res.data["detail"])

    def test_nao_pode_cancelar_finalizado(self):
        self.servico.status = "finalizado"
        self.servico.save()
        self.client.force_authenticate(user=self.cliente)
        res = self.client.post(f"/api/servicos/{self.servico.id}/cancelar/")
        self.assertEqual(res.status_code, 400)

    def test_cancelar_cria_evento_rastreamento(self):
        self.client.force_authenticate(user=self.cliente)
        res = self.client.post(f"/api/servicos/{self.servico.id}/cancelar/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(
            RastreamentoEvento.objects.filter(
                servico=self.servico, tipo="cancelamento"
            ).exists()
        )

    def test_cancelar_libera_horario(self):
        """Após cancelar, o horário pode ser reutilizado."""
        self.client.force_authenticate(user=self.cliente)
        self.client.post(f"/api/servicos/{self.servico.id}/cancelar/")
        # O AvailabilitySlot não tem reserva no modelo atual,
        # mas o endpoint de horarios filtra pelo data_solicitada
        # de Servicos com status "solicitado" ou "em_andamento".
        # Cancelado não entra mais nesse filtro, logo o horário
        # reaparece nos disponíveis.
        horarios = self.client.get(f"/api/providers/{self.provider.slug}/horarios/")
        # data_solicitada do servico cancelado deve estar em horarios.data
        self.assertIn(
            self.servico.data_solicitada.isoformat(),
            [h for h in horarios.data],
        )

    def test_prestador_nao_pode_usar_cancelar(self):
        """Prestador usa 'rejeitar', não 'cancelar'."""
        self.client.force_authenticate(user=self.prestador_user)
        res = self.client.post(f"/api/servicos/{self.servico.id}/cancelar/")
        self.assertEqual(res.status_code, 403)
```

---

## TypeScript — Interface (já parcialmente em IMPL_AGENDAMENTO.md)

```typescript
// types.ts — adicionar/confirmar campos
export interface Servico {
  // ... campos existentes ...
  motivo_cancelamento?: string;
  cancelado_em?: string | null;
}
```

---

## Frontend — Contrato (sem design visual)

### Hook/Mutation necessária

```typescript
// api.ts (já definido em IMPL_AGENDAMENTO.md — só confirmar)
cancelarServico: (id: number, motivo?: string) =>
  request<Servico>(`/servicos/${id}/cancelar/`, {
    method: "POST",
    body: motivo ? { motivo } : {},
  }),
```

### Locais de uso (apenas referência)

| Tela | Ação |
|------|------|
| `ServicoDetailPage.tsx` | Botão "Cancelar solicitação" quando `status === "solicitado"` |
| `ServicosPage.tsx` | Botão "Cancelar" no card/listagem de serviço pendente |
| `ProviderProfile.tsx` | Desabilitar se já existe solicitação pendente (sem cancelar daqui) |

---

## Arquivos Alterados

| Arquivo | Mudança |
|---------|---------|
| `backend/billing/models.py` | Adicionar `motivo_cancelamento` e `cancelado_em` a `Servico` |
| `backend/billing/serializers.py` | Incluir novos campos no `ServicoSerializer` |
| `backend/billing/views.py` | Adicionar action `cancelar` ao `ServicoViewSet` |
| `backend/billing/notificacoes.py` | Adicionar `servico_cancelado` ao mapa de mensagens |
| `backend/billing/tests.py` | Adicionar classe `CancelarServicoTests` com 9 testes |
| `frontend/src/types.ts` | Adicionar campos `motivo_cancelamento` e `cancelado_em` à interface `Servico` |
| `frontend/src/lib/api.ts` | Método `cancelarServico` já incluído em `IMPL_AGENDAMENTO.md` |

---

## Fora de Escopo (Futuro)

| Situação | Motivo |
|----------|--------|
| Cancelamento de serviço em `em_andamento` | Envolveria reembolso, avaliação de horas trabalhadas, disputa |
| Cancelamento pelo prestador | Já coberto por `rejeitar` (status `solicitado`) |
| Cancelamento em `aguardando_pagamento` | Envolveria estorno de transação, reembolso |
| Cancelamento em `reagendamento_sugerido` | Cliente pode simplesmente não aceitar o novo horário |

---

## Resumo

```
solicitado ──→ cancelado
     │
     └── 1. Valida: só o cliente, só status solicitado
         2. Salva motivo (opcional)
         3. Cria RastreamentoEvento
         4. Notifica prestador
         5. Libera horário
```
