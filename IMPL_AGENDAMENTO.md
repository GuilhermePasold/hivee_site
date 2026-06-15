# PLANO DE IMPLEMENTAÇÃO — AGENDAMENTO DE SERVIÇOS

> **Versão:** 1.0 — 2026-06-15
> **Baseado em:** HIVEE Marketplace (Django 6 + React 19)
> **Feature:** Fluxo completo de agendamento, aprovação, rastreamento, pagamento e avaliação obrigatória

---

## Sumário Executivo

Implementar o **fluxo completo de contratação** no HIVEE: desde o cliente solicitar um serviço com horário no perfil do prestador até a conclusão com pagamento e avaliação obrigatória.

**Regra de negócio principal:** O cliente **só pode contratar um novo serviço se tiver avaliado o anterior** (serviço concluído sem avaliação bloqueia novas contratações).

**Dependências entre features:**
```
Agendamento → Aprovação → Rastreamento → Conclusão → Pagamento → Avaliação Obrigatória
       ↑                                                                     |
       └─────────────────── Bloqueia novo agendamento ───────────────────────┘
```

---

## Mapa do Fluxo

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PERFIL DO PRESTADOR                                                     │
│  [Horários disponíveis] [Valor/h] [Formulário de solicitação]           │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ Cliente preenche: descrição, endereço, data/hora
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PENDENTE DE APROVAÇÃO (status: solicitado)                              │
│  Prestador recebe notificação (WhatsApp + site)                         │
│  [Aprovar] [Rejeitar] [Sugerir novo horário]                           │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ Prestador aprovou
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ EM ANDAMENTO (status: em_andamento)                                     │
│  [Rastreamento em tempo real]                                           │
│  Prestador: [Iniciar serviço] [Concluir serviço]                        │
│  Cliente: Acompanha status                                              │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ Prestador concluiu
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ AGUARDANDO CONFIRMAÇÃO (status: concluido)                              │
│  Cliente confirma que o serviço foi realizado corretamente              │
│  [Confirmar Conclusão] [Abrir Disputa]                                  │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ Cliente confirmou
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ AGUARDANDO PAGAMENTO (status: aguardando_pagamento)                     │
│  Gera cobrança (PIX/Boleto/Cartão)                                     │
│  Integração: MercadoPago / Asaas / Stripe                               │
│  Split: plataforma retém comissão, repassa ao prestador                │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ Pagamento confirmado (webhook)
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FINALIZADO (status: finalizado)                                         │
│  Prestador: [Emitir Nota Fiscal] (IMPL_NOTA_FISCAL.md)                 │
│  Cliente: ⚠️ AVALIAÇÃO OBRIGATÓRIA (IMPL_AVALIACAO.md)                │
│           [Avaliar serviço] — sem isso, não faz novo agendamento       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Status do Serviço (Modelo `Servico` unificado)

```python
class Servico(models.Model):
    """Serviço contratado — gerencia TODO o ciclo de vida."""
    STATUS = [
        ("solicitado", "Pendente de Aprovação"),       # Cliente pediu
        ("rejeitado", "Rejeitado"),                     # Prestador recusou
        ("cancelado", "Cancelado"),                     # Cliente desistiu
        ("em_andamento", "Em Andamento"),               # Prestador iniciou
        ("concluido", "Aguardando Confirmação"),         # Prestador marcou concluído
        ("aguardando_pagamento", "Aguardando Pagamento"),# Cliente confirmou, aguarda pagamento
        ("finalizado", "Finalizado"),                    # Pagamento confirmado
        ("disputa", "Em Disputa"),                       # Cliente não concordou
    ]

    provider = models.ForeignKey("catalog.Provider", on_delete=models.CASCADE, related_name="servicos")
    cliente_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="servicos_contratados")
    cliente_nome = models.CharField(max_length=200)
    cliente_cpf = models.CharField(max_length=14, blank=True)
    cliente_email = models.EmailField(blank=True)
    cliente_telefone = models.CharField(max_length=15, blank=True)

    descricao = models.TextField(verbose_name="Descreva o serviço necessário")
    endereco = models.TextField(verbose_name="Endereço de realização")
    observacoes = models.TextField(blank=True, verbose_name="Observações adicionais")

    data_solicitada = models.DateTimeField(verbose_name="Data/hora solicitada")
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    data_pagamento = models.DateTimeField(null=True, blank=True)

    valor_combinado = models.DecimalField(max_digits=10, decimal_places=2)
    comissao_plataforma = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # %
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_liquido_prestador = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS, default="solicitado")
    motivo_rejeicao = models.TextField(blank=True)
    sugestao_horario = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

    def __str__(self):
        return f"Serviço #{self.id} - {self.provider.name} x {self.cliente_nome} [{self.get_status_display()}]"
```

---

## API REST — Endpoints Completos

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| `GET` | `/api/providers/{slug}/horarios/` | Horários disponíveis do prestador | `AllowAny` |
| `POST` | `/api/providers/{slug}/solicitar/` | Cliente solicita serviço | `IsAuthenticated` |
| `GET` | `/api/servicos/` | Lista serviços do usuário (filtra por papel) | `IsAuthenticated` |
| `GET` | `/api/servicos/{id}/` | Detalhe do serviço | `IsAuthenticated` |
| `POST` | `/api/servicos/{id}/aprovar/` | Prestador aprova solicitação | `IsAuthenticated` (owner do provider) |
| `POST` | `/api/servicos/{id}/rejeitar/` | Prestador rejeita com motivo | `IsAuthenticated` (owner) |
| `POST` | `/api/servicos/{id}/reagendar/` | Prestador sugere novo horário | `IsAuthenticated` (owner) |
| `POST` | `/api/servicos/{id}/iniciar/` | Prestador inicia (rastreamento) | `IsAuthenticated` (owner) |
| `POST` | `/api/servicos/{id}/concluir/` | Prestador marca como concluído | `IsAuthenticated` (owner) |
| `POST` | `/api/servicos/{id}/confirmar/` | Cliente confirma conclusão | `IsAuthenticated` (cliente) |
| `POST` | `/api/servicos/{id}/disputa/` | Cliente abre disputa | `IsAuthenticated` (cliente) |
| `POST` | `/api/servicos/{id}/cancelar/` | Cliente cancela (só se "solicitado") | `IsAuthenticated` (cliente) |
| `GET` | `/api/servicos/{id}/pagamento/` | Dados do pagamento (QR Code Pix, etc) | `IsAuthenticated` |
| `POST` | `/api/pagamentos/webhook/` | Webhook do gateway de pagamento | `AllowAny` (validação HMAC) |
| `GET` | `/api/servicos/verificar-bloqueio/` | Verifica se cliente pode contratar | `IsAuthenticated` |

---

## 1. Agendamento — Solicitação no Perfil do Prestador

### Frontend: ProviderProfile.tsx — Seção de Agendamento

```tsx
// Adicionar abaixo do "Solicitar orçamento" ou substituir os botões atuais:
<div className="surface flex flex-col gap-3 rounded-3xl p-6">
  {/* Cliente logado vê o formulário de agendamento */}
  {user && (
    <>
      <h3 className="font-display text-lg font-semibold">Agendar serviço</h3>

      {podeContratar === false && (
        <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
          <AlertTriangle className="mb-1 h-4 w-4" />
          Você precisa avaliar o serviço anterior antes de contratar um novo.
          <Link to="/minha-conta/servicos" className="ml-1 underline">Ver serviços</Link>
        </div>
      )}

      {podeContratar && (
        <form onSubmit={handleSolicitar} className="flex flex-col gap-3">
          <textarea
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            placeholder="Descreva o serviço que precisa..."
            className="rounded-xl border border-white/10 bg-zinc-800/50 px-4 py-3 text-sm outline-none focus:ring-1 focus:ring-gold-500"
            rows={3}
            required
          />
          <input
            value={endereco}
            onChange={(e) => setEndereco(e.target.value)}
            placeholder="Endereço de realização do serviço"
            className="rounded-xl border border-white/10 bg-zinc-800/50 px-4 py-3 text-sm outline-none focus:ring-1 focus:ring-gold-500"
            required
          />

          {/* Seletor de horário */}
          <div className="grid grid-cols-2 gap-2">
            <input
              type="date"
              value={data}
              onChange={(e) => setData(e.target.value)}
              min={today}
              className="rounded-xl border border-white/10 bg-zinc-800/50 px-4 py-3 text-sm outline-none focus:ring-1 focus:ring-gold-500"
              required
            />
            <select
              value={horario}
              onChange={(e) => setHorario(e.target.value)}
              className="rounded-xl border border-white/10 bg-zinc-800/50 px-4 py-3 text-sm outline-none focus:ring-1 focus:ring-gold-500"
              required
            >
              <option value="">Selecione horário</option>
              {horariosDisponiveis.map((h) => (
                <option key={h} value={h}>{h}</option>
              ))}
            </select>
          </div>

          <p className="text-sm text-muted-foreground">
            Valor: <span className="font-semibold text-gold">{BRL.format(p.hourly_rate)}/h</span>
          </p>

          <button type="submit" disabled={solicitando} className="btn-gold w-full py-3.5 text-base">
            <CalendarCheck className="h-4 w-4" />
            {solicitando ? "Enviando..." : "Solicitar serviço"}
          </button>
        </form>
      )}
    </>
  )}

  {/* Usuário não logado vê botão de login */}
  {!user && (
    <button onClick={() => navigate("/entrar")} className="btn-gold w-full py-3.5 text-base">
      Entre para solicitar um serviço
    </button>
  )}
</div>
```

### Backend: Endpoint de Solicitação

```python
@action(detail=True, methods=["get"])
def horarios(self, request, slug=None):
    """Retorna horários disponíveis (futuros, não agendados) de um prestador."""
    provider = self.get_object()
    slots = AvailabilitySlot.objects.filter(provider=provider)
    hoje = timezone.now()

    # Gera os próximos 14 dias de horários, filtrando os já agendados
    servicos_marcados = Servico.objects.filter(
        provider=provider,
        status__in=["solicitado", "em_andamento"],
    ).values_list("data_solicitada", flat=True)

    horarios = []
    for i in range(14):
        dia = hoje.date() + timedelta(days=i)
        dia_semana = dia.weekday()
        for slot in slots.filter(day_of_week=dia_semana):
            horario = datetime.combine(dia, slot.start_time, tzinfo=hoje.tzinfo)
            if horario > hoje and horario not in servicos_marcados:
                horarios.append(horario.isoformat())

    return Response(horarios[:20])  # Limite de 20 opções


@action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
def solicitar(self, request, slug=None):
    """Cliente solicita serviço. Bloqueia se tiver serviço anterior sem avaliação."""
    provider = self.get_object()

    # === REGRA: avaliação obrigatória ===
    tem_servico_nao_avaliado = Servico.objects.filter(
        cliente_user=request.user,
        status="finalizado",
    ).exclude(
        id__in=Review.objects.filter(reviewer=request.user).values("servico_id")
    ).exists()

    if tem_servico_nao_avaliado:
        return Response({
            "detail": "Você tem um serviço finalizado que ainda não foi avaliado. "
                      "Avalie-o antes de contratar um novo.",
            "codigo": "avaliacao_obrigatoria",
            "servico_pendente_id": servico_pendente.id,
        }, status=403)

    serializer = ServicoSerializer(data={
        "provider": provider.id,
        "cliente_user": request.user.id,
        "descricao": request.data.get("descricao"),
        "endereco": request.data.get("endereco"),
        "data_solicitada": request.data.get("data_solicitada"),
        "valor_combinado": float(provider.hourly_rate),
        "observacoes": request.data.get("observacoes", ""),
        "cliente_nome": request.user.first_name or request.user.email,
        "cliente_email": request.user.email,
    })
    serializer.is_valid(raise_exception=True)
    servico = serializer.save(
        cliente_user=request.user,
        status="solicitado",
    )

    # Notifica prestador via WhatsApp + notificação no site
    _notificar_prestador(servico, "nova_solicitacao")

    return Response(ServicoSerializer(servico).data, status=201)
```

---

## 2. Aprovação/Rejeição pelo Prestador

```python
# backend/billing/views.py

class ServicoViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_servico_do_prestador(self, request, pk):
        """Apenas o dono do provider pode aprovar/rejeitar."""
        servico = get_object_or_404(Servico, id=pk)
        if servico.provider.owner != request.user:
            raise PermissionDenied("Só o prestador pode gerenciar este serviço.")
        return servico

    @action(detail=True, methods=["post"])
    def aprovar(self, request, pk=None):
        servico = self._get_servico_do_prestador(request, pk)
        if servico.status != "solicitado":
            return Response({"detail": "Serviço não está pendente."}, status=400)

        servico.status = "em_andamento"
        servico.data_aprovacao = timezone.now()
        servico.save(update_fields=["status", "data_aprovacao"])

        _notificar_cliente(servico, "servico_aprovado")
        return Response(ServicoSerializer(servico).data)

    @action(detail=True, methods=["post"])
    def rejeitar(self, request, pk=None):
        servico = self._get_servico_do_prestador(request, pk)
        if servico.status != "solicitado":
            return Response({"detail": "Serviço não está pendente."}, status=400)

        servico.status = "rejeitado"
        servico.motivo_rejeicao = request.data.get("motivo", "")
        servico.save(update_fields=["status", "motivo_rejeicao"])

        _notificar_cliente(servico, "servico_rejeitado")
        return Response(ServicoSerializer(servico).data)

    @action(detail=True, methods=["post"])
    def reagendar(self, request, pk=None):
        """Prestador sugere outro horário."""
        servico = self._get_servico_do_prestador(request, pk)
        if servico.status != "solicitado":
            return Response({"detail": "Serviço não está pendente."}, status=400)

        novo_horario = request.data.get("data_sugerida")
        if not novo_horario:
            return Response({"detail": "Informe a data/hora sugerida."}, status=400)

        servico.sugestao_horario = novo_horario
        servico.motivo_rejeicao = request.data.get("motivo", "")
        servico.save(update_fields=["sugestao_horario", "motivo_rejeicao"])

        # Cliente precisa aceitar o novo horário
        _notificar_cliente(servico, "reagendamento_sugerido")
        return Response(ServicoSerializer(servico).data)
```

### Notificações

```python
# backend/billing/notificacoes.py
def _notificar_prestador(servico, tipo):
    """Envia notificação via WhatsApp + notificação no site (WebSocket)."""
    msg_map = {
        "nova_solicitacao": f"🔔 Nova solicitação de serviço de {servico.cliente_nome}!\n"
                            f"{servico.descricao[:100]}...\n"
                            f"Data: {servico.data_solicitada:%d/%m/%Y %H:%M}\n"
                            f"Acesse HIVEE para aprovar ou rejeitar.",
        "confirmacao_cliente": f"✅ {servico.cliente_nome} confirmou a conclusão do serviço #{servico.id}.",
    }

def _notificar_cliente(servico, tipo):
    """Envia notificação via WhatsApp + WebSocket + e-mail."""
    msg_map = {
        "servico_aprovado": f"✅ Seu serviço com {servico.provider.name} foi aprovado! "
                            f"O prestador iniciará em breve.",
        "servico_rejeitado": f"❌ {servico.provider.name} rejeitou sua solicitação. "
                             f"Motivo: {servico.motivo_rejeicao}",
        "reagendamento_sugerido": f"🔄 {servico.provider.name} sugeriu um novo horário. "
                                  f"Acesse para confirmar.",
        "servico_concluido": f"✅ {servico.provider.name} marcou o serviço como concluído. "
                             f"Confirme a conclusão para liberar o pagamento.",
        "pagamento_confirmado": f"💰 Pagamento do serviço #{servico.id} confirmado! "
                                f"Avalie o prestador em HIVEE.",
    }
```

---

## 3. Rastreamento (Em Andamento)

```python
@action(detail=True, methods=["post"])
def iniciar(self, request, pk=None):
    """Prestador marca início do serviço (status → em_andamento)."""
    servico = self._get_servico_do_prestador(request, pk)
    if servico.status not in ("solicitado", "aprovado"):
        return Response({"detail": "Serviço precisa estar aprovado."}, status=400)

    servico.status = "em_andamento"
    servico.data_inicio = timezone.now()
    servico.save(update_fields=["status", "data_inicio"])

    _notificar_cliente(servico, "servico_iniciado")

    # Criar evento de rastreamento
    RastreamentoEvento.objects.create(
        servico=servico,
        tipo="inicio",
        descricao="Prestador iniciou o serviço",
    )

    return Response(ServicoSerializer(servico).data)


@action(detail=True, methods=["post"])
def concluir(self, request, pk=None):
    """Prestador marca como concluído (status → concluido)."""
    servico = self._get_servico_do_prestador(request, pk)
    if servico.status != "em_andamento":
        return Response({"detail": "Serviço não está em andamento."}, status=400)

    servico.status = "concluido"
    servico.data_conclusao = timezone.now()
    servico.save(update_fields=["status", "data_conclusao"])

    RastreamentoEvento.objects.create(
        servico=servico, tipo="conclusao",
        descricao="Prestador marcou serviço como concluído",
    )

    _notificar_cliente(servico, "servico_concluido")
    return Response(ServicoSerializer(servico).data)


@action(detail=True, methods=["post"])
def confirmar(self, request, pk=None):
    """Cliente confirma que o serviço foi realizado (status → aguardando_pagamento)."""
    servico = get_object_or_404(Servico, id=pk, cliente_user=request.user)
    if servico.status != "concluido":
        return Response({"detail": "Prestador ainda não marcou como concluído."}, status=400)

    servico.status = "aguardando_pagamento"
    servico.save(update_fields=["status"])

    # Gera cobrança automaticamente
    from .pagamento import gerar_cobranca
    transacao = gerar_cobranca(servico)

    RastreamentoEvento.objects.create(
        servico=servico, tipo="confirmacao_cliente",
        descricao="Cliente confirmou conclusão do serviço",
    )

    return Response({
        "servico": ServicoSerializer(servico).data,
        "pagamento": TransacaoSerializer(transacao).data,
    })
```

### Modelo de Rastreamento

```python
class RastreamentoEvento(models.Model):
    TIPOS = [
        ("inicio", "Serviço iniciado"),
        ("atualizacao", "Atualização do prestador"),
        ("conclusao", "Serviço concluído pelo prestador"),
        ("confirmacao_cliente", "Cliente confirmou conclusão"),
        ("disputa", "Disputa aberta"),
        ("cancelamento", "Serviço cancelado"),
    ]

    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name="eventos_rastreamento")
    tipo = models.CharField(max_length=30, choices=TIPOS)
    descricao = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Evento de Rastreamento"
        verbose_name_plural = "Eventos de Rastreamento"
```

---

## 4. Pagamento (Não existe — criar do zero)

### Modelo

```python
class Transacao(models.Model):
    STATUS = [
        ("pendente", "Pendente"),
        ("pago", "Pago"),
        ("cancelado", "Cancelado"),
        ("reembolsado", "Reembolsado"),
    ]

    servico = models.OneToOneField(Servico, on_delete=models.CASCADE, related_name="transacao")
    gateway = models.CharField(max_length=20, choices=[("mercadopago", "Mercado Pago"), ("fake", "Simulado")])
    gateway_id = models.CharField(max_length=100, blank=True, verbose_name="ID no gateway")
    valor_bruto = models.DecimalField(max_digits=10, decimal_places=2)
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2)
    valor_liquido = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=[("pix", "Pix"), ("boleto", "Boleto"), ("card", "Cartão")])
    qr_code = models.TextField(blank=True, verbose_name="QR Code Pix (base64)")
    qr_code_texto = models.TextField(blank=True, verbose_name="Copia e Cola Pix")
    link_pagamento = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")
    pago_em = models.DateTimeField(null=True, blank=True)
    metadados_gateway = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
```

### Integração — Gateway Fake (MVP) + Mercado Pago (Produção)

```python
# backend/billing/pagamento.py
import os, uuid, json
from decimal import Decimal
from django.conf import settings

def gerar_cobranca(servico: Servico) -> Transacao:
    """Gera cobrança — usa gateway fake em dev, Mercado Pago em produção."""
    gateway = os.getenv("GATEWAY_PAGAMENTO", "fake")
    valor_bruto = servico.valor_combinado
    comissao = valor_bruto * servico.comissao_plataforma / Decimal("100")
    valor_liquido = valor_bruto - comissao

    if gateway == "mercadopago":
        return _cobrar_mercadopago(servico, valor_bruto, comissao, valor_liquido)
    else:
        return _cobrar_fake(servico, valor_bruto, comissao, valor_liquido)


def _cobrar_fake(servico, valor_bruto, comissao, valor_liquido):
    """Gateway fake para desenvolvimento — gera Pix simulado."""
    return Transacao.objects.create(
        servico=servico,
        gateway="fake",
        gateway_id=f"fake_{uuid.uuid4().hex[:12]}",
        valor_bruto=valor_bruto,
        valor_comissao=comissao,
        valor_liquido=valor_liquido,
        metodo="pix",
        qr_code="fake_qr_base64",
        qr_code_texto=f"00020126580014BR.GOV.BCB.PIX0136fake-pix-hivee-{servico.id}520400005303986540{float(valor_bruto):.2f}5802BR5913HIVEE6008BRASILIA62070503***6304FFFF",
        link_pagamento=f"{settings.BASE_URL}/api/pagamentos/fake/{servico.id}/pagar",
        status="pendente",
    )


def _cobrar_mercadopago(servico, valor_bruto, comissao, valor_liquido):
    """Gera cobrança via Mercado Pago com split."""
    import mercadopago
    sdk = mercadopago.SDK(os.getenv("MERCADO_PAGO_ACCESS_TOKEN"))

    payment_data = {
        "transaction_amount": float(valor_bruto),
        "description": f"Serviço #{servico.id} - {servico.provider.name}",
        "payment_method_id": "pix",
        "payer": {
            "email": servico.cliente_email,
            "first_name": servico.cliente_nome.split()[0] if servico.cliente_nome else "Cliente",
        },
        "application_fee": float(comissao),  # split: comissão da plataforma
    }

    result = sdk.payment().create(payment_data)
    resp = result["response"]

    return Transacao.objects.create(
        servico=servico,
        gateway="mercadopago",
        gateway_id=str(resp["id"]),
        valor_bruto=valor_bruto,
        valor_comissao=comissao,
        valor_liquido=valor_liquido,
        metodo="pix",
        qr_code=resp.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64", ""),
        qr_code_texto=resp.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code", ""),
        link_pagamento=resp.get("point_of_interaction", {}).get("transaction_data", {}).get("ticket_url", ""),
        status="pendente",
        metadados_gateway=resp,
    )
```

### Webhook de Pagamento

```python
@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_pagamento(request):
    """Recebe notificação de pagamento do gateway."""
    gateway = request.data.get("gateway", "fake")

    if gateway == "mercadopago":
        transacao_id = request.data.get("data", {}).get("id")
        transacao = get_object_or_404(Transacao, gateway_id=str(transacao_id))
    else:
        transacao_id = request.data.get("transacao_id")
        transacao = get_object_or_404(Transacao, id=transacao_id)

    transacao.status = "pago"
    transacao.pago_em = timezone.now()
    transacao.save()

    servico = transacao.servico
    servico.status = "finalizado"
    servico.data_pagamento = timezone.now()
    servico.save()

    # Incrementa jobs_done do provider
    servico.provider.jobs_done += 1
    servico.provider.save(update_fields=["jobs_done"])

    # Notifica cliente: pode avaliar
    _notificar_cliente(servico, "pagamento_confirmado")

    # Notifica prestador: NF-e disponível
    _notificar_prestador(servico, "pagamento_recebido")

    return Response({"status": "ok"})
```

### Frontend: Página de Pagamento

```tsx
// ServicoDetailPage.tsx — quando status === "aguardando_pagamento"
{servico.status === "aguardando_pagamento" && servico.transacao?.metodo === "pix" && (
  <div className="surface rounded-3xl p-6 text-center">
    <h3 className="font-display text-xl font-semibold">Pagamento via Pix</h3>
    <p className="mt-2 text-sm text-muted-foreground">
      Escaneie o QR Code ou copie o código abaixo para pagar
    </p>
    {servico.transacao.qr_code && (
      <img src={`data:image/png;base64,${servico.transacao.qr_code}`}
           className="mx-auto mt-4 h-48 w-48" alt="QR Code Pix" />
    )}
    <div className="mt-4 flex items-center gap-2 rounded-xl border border-white/10 bg-zinc-800/50 p-3">
      <code className="flex-1 truncate text-xs text-zinc-300">
        {servico.transacao.qr_code_texto}
      </code>
      <button onClick={() => copyToClipboard(servico.transacao.qr_code_texto!)}
              className="btn-ghost shrink-0 px-3 py-1.5 text-xs">
        <Copy className="h-3.5 w-3.5" /> Copiar
      </button>
    </div>
    <p className="mt-4 text-xs text-muted-foreground">
      Após o pagamento, a confirmação pode levar alguns segundos.
    </p>
  </div>
)}
```

---

## 5. Avaliação Obrigatória — Bloqueio de Novas Contratações

### Regra de Negócio (Backend)

```python
# Verificação no momento de solicitar novo serviço
def _verificar_bloqueio_avaliacao(user) -> dict:
    """Retorna se o usuário pode contratar e qual serviço está bloqueando."""
    servico_sem_review = Servico.objects.filter(
        cliente_user=user,
        status="finalizado",
    ).exclude(
        id__in=Review.objects.filter(reviewer=user).values("servico_id")
    ).first()

    if servico_sem_review:
        return {
            "pode_contratar": False,
            "servico_id": servico_sem_review.id,
            "servico_prestador": servico_sem_review.provider.name,
            "mensagem": f"Você precisa avaliar o serviço com {servico_sem_review.provider.name} antes de contratar outro.",
        }

    return {"pode_contratar": True}


@action(detail=False, methods=["get"])
def verificar_bloqueio(self, request):
    """Endpoint para o frontend verificar antes de exibir o formulário."""
    resultado = _verificar_bloqueio_avaliacao(request.user)
    return Response(resultado)
```

### Frontend: Bloqueio Visual

```tsx
// ProviderProfile.tsx — antes de mostrar o formulário de solicitação
useEffect(() => {
  if (user) {
    api.verificarBloqueio().then(setBloqueio).catch(() => undefined);
  }
}, [user]);
```

### Fluxo Obrigatório

```
1. Serviço finalizado
       ↓
2. Cliente tenta contratar NOVO serviço
       ↓
3. Backend verifica: existe Servico.finalizado SEM Review?
       ├── NÃO → permite contratar
       └── SIM → bloqueia com 403 + mensagem + link
                     ↓
4. Cliente é redirecionado para avaliar o serviço pendente
       ↓
5. POST /api/servicos/{id}/avaliar/ (nota + comentário)
       ↓
6. Review criado → sinal recalcula Provider.rating
       ↓
7. Cliente volta a poder contratar
```

---

## 6. Dashboard do Cliente — Central de Serviços

### Frontend: `ServicosPage.tsx`

```tsx
// Aba "[N] Pendente de avaliação" com destaque
<TabButton active={tab === "pendentes-avaliacao"} onClick={() => setTab("pendentes-avaliacao")}>
  <Star className="h-4 w-4" />
  Aguardando avaliação
  {servicosPendentesAvaliacao.length > 0 && (
    <span className="ml-1 rounded-full bg-rose-500/25 px-2 py-0.5 text-[11px] font-semibold text-rose-200">
      {servicosPendentesAvaliacao.length}
    </span>
  )}
</TabButton>
```

### Frontend: `ServicoDetailPage.tsx` — Timeline de Status

```tsx
// Timeline visual do serviço
<div className="surface rounded-3xl p-6">
  <h3 className="font-display text-lg font-semibold">Status do serviço</h3>
  <div className="mt-4 space-y-4">
    {statusHistory.map((evento, i) => (
      <div key={i} className="flex gap-4">
        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          evento.ativo ? "bg-gold-500/20 text-gold-300" : "bg-zinc-800 text-zinc-500"
        }`}>
          {evento.icone}
        </div>
        <div>
          <p className="font-medium text-foreground">{evento.titulo}</p>
          <p className="text-xs text-muted-foreground">{evento.data}</p>
        </div>
      </div>
    ))}
  </div>
</div>
```

---

## 7. Cronograma de Status (Timeline)

```
solicitado ──→ rejeitado (prestador recusou)
    │              cancelado (cliente desistiu)
    │
    ├──→ aprovado ──→ em_andamento ──→ concluido (prestador)
    │       │              │                │
    │       │              │                └──→ aguardando_pagamento (cliente confirmou)
    │       │              │                              │
    │       │              │                              ├──→ finalizado (pagamento ok)
    │       │              │                              │       ↓
    │       │              │                              │   [Avaliação Obrigatória]
    │       │              │                              │
    │       │              │                              └──→ cancelado (pagamento não realizado)
    │       │              │
    │       │              └──→ disputa (cliente não concordou)
    │       │
    │       └──→ reagendamento_sugerido (prestador sugeriu novo horário)
    │                    │
    │                    └──→ cliente aceita → em_andamento
    │                    └──→ cliente recusa → cancelado
    │
    └──→ cancelado (antes de aprovar)
```

---

## 8. Sprints de Implementação

### Sprint 1 — Modelo Servico + Agendamento
- [ ] Criar app `billing` ou adicionar ao `catalog`
- [ ] Modelo `Servico` (STATUS expandido), `RastreamentoEvento`, `Transacao`
- [ ] Migrations + admin
- [ ] Serializer + ViewSet (CRUD básico)
- [ ] Endpoint `GET /api/providers/{slug}/horarios/`
- [ ] Endpoint `POST /api/providers/{slug}/solicitar/`
- [ ] Regra de bloqueio por avaliação anterior
- [ ] Testes

### Sprint 2 — Aprovação + Rastreamento
- [ ] Endpoints: aprovar, rejeitar, reagendar, iniciar, concluir, confirmar
- [ ] Timeline de eventos (`RastreamentoEvento`)
- [ ] Notificações (WhatsApp + WebSocket)
- [ ] Dashboard do prestador: "Serviços pendentes"
- [ ] Página de detalhe do serviço com timeline

### Sprint 3 — Pagamento
- [ ] Modelo `Transacao`
- [ ] Gateway fake (MVP) — gera QR Code Pix simulado
- [ ] Integração Mercado Pago (produção)
- [ ] Webhook de confirmação de pagamento
- [ ] Incrementar `Provider.jobs_done` no pagamento
- [ ] Página de pagamento no frontend (QR Code, copia e cola)

### Sprint 4 — Avaliação Obrigatória + Integração Final
- [ ] Conectar com `Review` (IMPL_AVALIACAO.md)
- [ ] Bloqueio: verificar avaliação anterior ao solicitar
- [ ] Notificação "Você tem N serviço(s) pendente(s) de avaliação"
- [ ] Conectar com emissão de NF (IMPL_NOTA_FISCAL.md) após pagamento
- [ ] Testes de fluxo completo (solicitar → aprovar → executar → pagar → avaliar)

---

## 9. Provider — Campos Adicionais

```python
# Adicionar ao Provider (catalog/models.py)
class Provider(models.Model):
    # ... campos existentes ...

    # Para agendamento
    aceita_agendamento = models.BooleanField(default=True)
    preco_fixo = models.BooleanField(default=False,
        help_text="Se True, o valor é o hourly_rate; se False, cliente sugere valor")
    tempo_medio_servico = models.PositiveIntegerField(null=True, blank=True,
        help_text="Duração média em minutos (para cálculo de disponibilidade)")
    # Para pagamento
    chave_pix = models.CharField(max_length=100, blank=True,
        verbose_name="Chave Pix para recebimento")
    conta_mercadopago_id = models.CharField(max_length=100, blank=True,
        verbose_name="ID da conta no Mercado Pago (split)")
```

---

## 10. Variáveis de Ambiente

```env
# Gateway de pagamento (fake | mercadopago)
GATEWAY_PAGAMENTO=fake

# Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN=APP_USR-...
MERCADO_PAGO_PUBLIC_KEY=APP_USR-...

# URL base (para links de pagamento)
BASE_URL=http://localhost:8000
```

---

## Dependências (requirements.txt)

```
# Pagamento
mercadopago>=2.0.0    # SDK oficial Mercado Pago
# ou
stripe>=7.0.0         # Alternativa internacional
```

---

## TypeScript (types.ts)

```typescript
export type ServicoStatus =
  | "solicitado" | "rejeitado" | "cancelado"
  | "em_andamento" | "concluido"
  | "aguardando_pagamento" | "finalizado" | "disputa";

export interface Servico {
  id: number;
  provider: number;
  provider_nome: string;
  provider_slug: string;
  provider_avatar: string;
  cliente_user: number;
  cliente_nome: string;
  descricao: string;
  endereco: string;
  data_solicitada: string;
  data_inicio: string | null;
  data_conclusao: string | null;
  valor_combinado: number;
  status: ServicoStatus;
  motivo_rejeicao: string;
  transacao?: Transacao;
  minha_avaliacao?: Review | null;
  eventos_rastreamento?: RastreamentoEvento[];
}

export interface Transacao {
  id: number;
  servico: number;
  metodo: "pix" | "boleto" | "card";
  valor_bruto: number;
  valor_comissao: number;
  valor_liquido: number;
  qr_code: string;
  qr_code_texto: string;
  link_pagamento: string;
  status: "pendente" | "pago" | "cancelado" | "reembolsado";
}

export interface RastreamentoEvento {
  id: number;
  tipo: string;
  descricao: string;
  created_at: string;
}

export interface BloqueioAvaliacao {
  pode_contratar: boolean;
  servico_id?: number;
  servico_prestador?: string;
  mensagem?: string;
}
```

---

## api.ts — Novos Métodos

```typescript
export const api = {
  // ... métodos existentes ...

  // Agendamento
  horariosProvider: (slug: string) =>
    request<string[]>(`/providers/${slug}/horarios/`),
  solicitarServico: (slug: string, data: any) =>
    request<Servico>(`/providers/${slug}/solicitar/`, { method: "POST", body: data }),

  // Gerenciamento do serviço
  servicos: () => request<Servico[]>("/servicos/"),
  servico: (id: number) => request<Servico>(`/servicos/${id}/`),
  aprovarServico: (id: number) =>
    request<Servico>(`/servicos/${id}/aprovar/`, { method: "POST" }),
  rejeitarServico: (id: number, motivo: string) =>
    request<Servico>(`/servicos/${id}/rejeitar/`, { method: "POST", body: { motivo } }),
  iniciarServico: (id: number) =>
    request<Servico>(`/servicos/${id}/iniciar/`, { method: "POST" }),
  concluirServico: (id: number) =>
    request<Servico>(`/servicos/${id}/concluir/`, { method: "POST" }),
  confirmarServico: (id: number) =>
    request<{ servico: Servico; pagamento: Transacao }>(`/servicos/${id}/confirmar/`, { method: "POST" }),
  cancelarServico: (id: number) =>
    request<Servico>(`/servicos/${id}/cancelar/`, { method: "POST" }),

  // Pagamento
  verificarBloqueio: () =>
    request<BloqueioAvaliacao>("/servicos/verificar-bloqueio/"),

  // Review (conectar com fluxo obrigatório)
  avaliarServico: (servicoId: number, data: { nota: number; comentario?: string }) =>
    request<Review>(`/servicos/${servicoId}/avaliar/`, { method: "POST", body: data }),
};
```

---

## Rotas do Frontend

```tsx
// frontend/src/main.tsx
<Route path="/minha-conta" element={<MinhaConta />} />
<Route path="/minha-conta/servicos" element={<ServicosPage />} />
<Route path="/minha-conta/servicos/:id" element={<ServicoDetailPage />} />
```

---

## Anotações do Review (Código Atual)

| Item | Observação |
|------|-----------|
| `AvailabilitySlot` já existe | Aproveitar para gerar horários disponíveis |
| `Provider.hourly_rate` já existe | Usar como valor base do serviço |
| `Provider.jobs_done` já existe | Incrementar no pagamento |
| `Provider.owner` → `User` | Para identificar o prestador como usuário do sistema |
| `Cliente` model existe mas é MTV | Prefira `User` como `cliente_user` para compatibilidade com auth |
| Chat WebSocket + WAHA já existem | Usar para notificações em tempo real |
| `agent` com APScheduler já existe | Para follow-up de serviços parados (ex: "seu serviço está pendente de pagamento há 2 dias") |
| NÃO existe modelo de pagamento | Criar `Transacao` do zero |
| NÃO existe modelo de rastreamento | Criar `RastreamentoEvento` |
| Produto final: 3 features integradas | Agendamento + Pagamento + Avaliação Obrigatória (ciclo fechado) |
