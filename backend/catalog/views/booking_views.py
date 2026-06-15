"""Agendamento de serviços: ciclo de vida completo + avaliação obrigatória.

Fluxo: solicitar → aprovar/rejeitar → concluir → confirmar → pagar(simulado) →
finalizado → avaliação obrigatória (destrava novas contratações).

Reaproveita `notify_user` (sistema de notificações já existente) em cada transição.
"""

from datetime import datetime, timedelta

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from ..models import AvailabilitySlot, Notification, Provider, Review, Servico
from ..serializers import ServicoSerializer
from ..services import notify_user

COMISSAO_PADRAO = 10  # %


# ── Regras de negócio compartilhadas ───────────────────────────────────────

def servico_pendente_avaliacao(user):
    """Primeiro serviço finalizado do usuário que ainda não foi avaliado (ou None)."""
    return (
        Servico.objects.filter(cliente_user=user, status=Servico.Status.FINALIZADO)
        .filter(review__isnull=True)
        .select_related("provider")
        .first()
    )


def _calcular_valores(valor):
    comissao = round(valor * COMISSAO_PADRAO / 100, 2)
    return comissao, round(valor - comissao, 2)


def _fake_pix(servico):
    valor = float(servico.valor_combinado)
    return (
        f"00020126580014BR.GOV.BCB.PIX0136hivee-{servico.id}"
        f"520400005303986540{valor:.2f}5802BR5905HIVEE6008BRASILIA62070503***6304ABCD"
    )


# ── Solicitação no perfil do prestador ─────────────────────────────────────

class ProviderHorariosView(APIView):
    """GET /api/providers/<slug>/horarios/ — próximos horários livres (14 dias)."""

    def get(self, request, slug=None):
        provider = get_object_or_404(Provider, slug=slug)
        slots = list(AvailabilitySlot.objects.filter(provider=provider))
        if not slots:
            return Response([])
        agora = timezone.localtime()
        ocupados = set(
            Servico.objects.filter(provider=provider, status__in=Servico.ABERTOS)
            .values_list("data_solicitada", flat=True)
        )
        horarios = []
        for i in range(14):
            dia = (agora + timedelta(days=i)).date()
            for slot in slots:
                if slot.day_of_week != dia.weekday():
                    continue
                dt = timezone.make_aware(datetime.combine(dia, slot.start_time))
                if dt > agora and dt not in ocupados:
                    horarios.append(dt.isoformat())
        return Response(sorted(horarios)[:20])


class SolicitarServicoView(APIView):
    """POST /api/providers/<slug>/solicitar/ — cliente solicita um serviço."""

    permission_classes = [IsAuthenticated]

    def post(self, request, slug=None):
        provider = get_object_or_404(Provider, slug=slug, status="approved")

        if provider.owner_id == request.user.id:
            return Response(
                {"detail": "Você não pode contratar a si mesmo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pendente = servico_pendente_avaliacao(request.user)
        if pendente:
            return Response(
                {
                    "detail": f"Avalie o serviço com {pendente.provider.name} antes de contratar outro.",
                    "codigo": "avaliacao_obrigatoria",
                    "servico_id": pendente.id,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        descricao = (request.data.get("descricao") or "").strip()
        raw_data = request.data.get("data_solicitada")
        if not descricao or not raw_data:
            return Response(
                {"detail": "Descrição e data/hora são obrigatórias."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data_solicitada = parse_datetime(raw_data)
        if data_solicitada is None:
            return Response(
                {"detail": "Data/hora inválida."}, status=status.HTTP_400_BAD_REQUEST
            )
        if timezone.is_naive(data_solicitada):
            data_solicitada = timezone.make_aware(data_solicitada)

        valor = float(provider.hourly_rate)
        comissao, liquido = _calcular_valores(valor)
        telefone = getattr(getattr(request.user, "profile", None), "telefone", "")

        servico = Servico.objects.create(
            provider=provider,
            cliente_user=request.user,
            cliente_nome=request.user.first_name or request.user.email,
            cliente_email=request.user.email,
            cliente_telefone=telefone or "",
            descricao=descricao,
            endereco=(request.data.get("endereco") or "").strip(),
            observacoes=(request.data.get("observacoes") or "").strip(),
            data_solicitada=data_solicitada,
            valor_combinado=valor,
            comissao_percent=COMISSAO_PADRAO,
            valor_comissao=comissao,
            valor_liquido=liquido,
        )

        if provider.owner_id:
            notify_user(
                recipient=provider.owner,
                tipo=Notification.Tipo.ORDER_REQUESTED,
                title="Nova solicitação de serviço",
                body=f"{servico.cliente_nome}: {descricao[:80]}",
                link=f"/minha-conta/servicos/{servico.id}",
                payload={"servico_id": servico.id},
            )
        return Response(ServicoSerializer(servico).data, status=status.HTTP_201_CREATED)


# ── Gestão do serviço (cliente + prestador) ────────────────────────────────

class ServicoViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def _as_prestador(self, request, pk):
        servico = get_object_or_404(Servico, pk=pk)
        if servico.provider.owner_id != request.user.id:
            return None
        return servico

    def _as_cliente(self, request, pk):
        return Servico.objects.filter(pk=pk, cliente_user=request.user).first()

    def list(self, request):
        papel = request.query_params.get("papel", "cliente")
        if papel == "prestador":
            qs = Servico.objects.filter(provider__owner=request.user)
        else:
            qs = Servico.objects.filter(cliente_user=request.user)
        qs = qs.select_related("provider").prefetch_related("review")
        return Response(ServicoSerializer(qs, many=True).data)

    def retrieve(self, request, pk=None):
        servico = get_object_or_404(
            Servico.objects.select_related("provider"), pk=pk
        )
        if request.user.id not in (servico.cliente_user_id, servico.provider.owner_id):
            return Response({"detail": "Sem acesso."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ServicoSerializer(servico).data)

    @action(detail=False, methods=["get"], url_path="verificar-bloqueio")
    def verificar_bloqueio(self, request):
        pendente = servico_pendente_avaliacao(request.user)
        if pendente:
            return Response({
                "pode_contratar": False,
                "servico_id": pendente.id,
                "provider_nome": pendente.provider.name,
                "mensagem": f"Avalie o serviço com {pendente.provider.name} antes de contratar outro.",
            })
        return Response({"pode_contratar": True})

    # --- Transições do prestador ---
    @action(detail=True, methods=["post"])
    def aprovar(self, request, pk=None):
        servico = self._as_prestador(request, pk)
        if not servico:
            return _forbidden()
        if servico.status != Servico.Status.SOLICITADO:
            return _bad("Serviço não está pendente.")
        servico.status = Servico.Status.EM_ANDAMENTO
        servico.data_aprovacao = timezone.now()
        servico.data_inicio = timezone.now()
        servico.save(update_fields=["status", "data_aprovacao", "data_inicio", "updated_at"])
        _notify_cliente(servico, Notification.Tipo.ORDER_CONFIRMED,
                        "Serviço aprovado!",
                        f"{servico.provider.name} aprovou e iniciou seu serviço.")
        return Response(ServicoSerializer(servico).data)

    @action(detail=True, methods=["post"])
    def rejeitar(self, request, pk=None):
        servico = self._as_prestador(request, pk)
        if not servico:
            return _forbidden()
        if servico.status != Servico.Status.SOLICITADO:
            return _bad("Serviço não está pendente.")
        servico.status = Servico.Status.REJEITADO
        servico.motivo_rejeicao = (request.data.get("motivo") or "").strip()
        servico.save(update_fields=["status", "motivo_rejeicao", "updated_at"])
        _notify_cliente(servico, Notification.Tipo.ORDER_CANCELLED,
                        "Solicitação recusada",
                        f"{servico.provider.name} recusou. {servico.motivo_rejeicao}".strip())
        return Response(ServicoSerializer(servico).data)

    @action(detail=True, methods=["post"])
    def concluir(self, request, pk=None):
        servico = self._as_prestador(request, pk)
        if not servico:
            return _forbidden()
        if servico.status != Servico.Status.EM_ANDAMENTO:
            return _bad("Serviço não está em andamento.")
        servico.status = Servico.Status.CONCLUIDO
        servico.data_conclusao = timezone.now()
        servico.save(update_fields=["status", "data_conclusao", "updated_at"])
        _notify_cliente(servico, Notification.Tipo.ORDER_COMPLETED,
                        "Serviço concluído",
                        f"{servico.provider.name} marcou como concluído. Confirme para liberar o pagamento.")
        return Response(ServicoSerializer(servico).data)

    # --- Transições do cliente ---
    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        servico = self._as_cliente(request, pk)
        if not servico:
            return _forbidden()
        if servico.status != Servico.Status.CONCLUIDO:
            return _bad("O prestador ainda não concluiu o serviço.")
        servico.status = Servico.Status.AGUARDANDO_PAGAMENTO
        servico.pix_copia_cola = _fake_pix(servico)
        servico.save(update_fields=["status", "pix_copia_cola", "updated_at"])
        return Response(ServicoSerializer(servico).data)

    @action(detail=True, methods=["post"])
    def pagar(self, request, pk=None):
        """Pagamento SIMULADO (sem gateway): marca pago e finaliza."""
        servico = self._as_cliente(request, pk)
        if not servico:
            return _forbidden()
        if servico.status != Servico.Status.AGUARDANDO_PAGAMENTO:
            return _bad("Serviço não está aguardando pagamento.")
        servico.status = Servico.Status.FINALIZADO
        servico.pago = True
        servico.data_pagamento = timezone.now()
        servico.save(update_fields=["status", "pago", "data_pagamento", "updated_at"])
        # incrementa serviços concluídos do prestador
        Provider.objects.filter(pk=servico.provider_id).update(
            jobs_done=servico.provider.jobs_done + 1
        )
        if servico.provider.owner_id:
            notify_user(
                recipient=servico.provider.owner,
                tipo=Notification.Tipo.ORDER_CONFIRMED,
                title="Pagamento recebido",
                body=f"O serviço #{servico.id} foi pago. Valor líquido: R$ {servico.valor_liquido}.",
                link=f"/minha-conta/servicos/{servico.id}",
                payload={"servico_id": servico.id},
            )
        return Response(ServicoSerializer(servico).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        servico = self._as_cliente(request, pk)
        if not servico:
            return _forbidden()
        if servico.status != Servico.Status.SOLICITADO:
            return _bad("Só dá para cancelar antes da aprovação.")
        servico.status = Servico.Status.CANCELADO
        servico.save(update_fields=["status", "updated_at"])
        if servico.provider.owner_id:
            notify_user(
                recipient=servico.provider.owner,
                tipo=Notification.Tipo.ORDER_CANCELLED,
                title="Solicitação cancelada",
                body=f"{servico.cliente_nome} cancelou a solicitação.",
                link=f"/minha-conta/servicos/{servico.id}",
                payload={"servico_id": servico.id},
            )
        return Response(ServicoSerializer(servico).data)

    @action(detail=True, methods=["post"])
    def disputa(self, request, pk=None):
        servico = self._as_cliente(request, pk)
        if not servico:
            return _forbidden()
        if servico.status != Servico.Status.CONCLUIDO:
            return _bad("Só dá para abrir disputa de um serviço concluído.")
        servico.status = Servico.Status.DISPUTA
        servico.motivo_rejeicao = (request.data.get("motivo") or "").strip()
        servico.save(update_fields=["status", "motivo_rejeicao", "updated_at"])
        if servico.provider.owner_id:
            notify_user(
                recipient=servico.provider.owner,
                tipo=Notification.Tipo.ORDER_DISPUTED,
                title="Disputa aberta",
                body=f"{servico.cliente_nome} abriu uma disputa no serviço #{servico.id}.",
                link=f"/minha-conta/servicos/{servico.id}",
                payload={"servico_id": servico.id},
            )
        return Response(ServicoSerializer(servico).data)

    @action(detail=True, methods=["post"])
    def avaliar(self, request, pk=None):
        """Avaliação obrigatória: cria Review e recalcula o rating do prestador."""
        servico = self._as_cliente(request, pk)
        if not servico:
            return _forbidden()
        if servico.status != Servico.Status.FINALIZADO:
            return _bad("Só dá para avaliar serviços finalizados.")
        if hasattr(servico, "review"):
            return _bad("Este serviço já foi avaliado.")
        try:
            nota = int(request.data.get("nota"))
        except (TypeError, ValueError):
            return _bad("Informe uma nota de 1 a 5.")
        if not 1 <= nota <= 5:
            return _bad("A nota deve ser de 1 a 5.")

        Review.objects.create(
            servico=servico,
            reviewer=request.user,
            provider=servico.provider,
            nota=nota,
            comentario=(request.data.get("comentario") or "").strip(),
        )
        _recalcular_rating(servico.provider)
        if servico.provider.owner_id:
            notify_user(
                recipient=servico.provider.owner,
                tipo=Notification.Tipo.ORDER_REVIEWED,
                title="Você recebeu uma avaliação",
                body=f"{servico.cliente_nome} avaliou seu serviço com {nota}★.",
                link=f"/prestador/{servico.provider.slug}",
                payload={"servico_id": servico.id, "nota": nota},
            )
        servico.refresh_from_db()
        return Response(ServicoSerializer(servico).data)


# ── helpers ────────────────────────────────────────────────────────────────

def _recalcular_rating(provider):
    agg = Review.objects.filter(provider=provider).aggregate(avg=Avg("nota"), n=Count("id"))
    provider.rating = round(agg["avg"] or 0, 2)
    provider.reviews_count = agg["n"] or 0
    provider.save(update_fields=["rating", "reviews_count"])


def _notify_cliente(servico, tipo, title, body):
    notify_user(
        recipient=servico.cliente_user,
        tipo=tipo,
        title=title,
        body=body,
        link=f"/minha-conta/servicos/{servico.id}",
        payload={"servico_id": servico.id},
    )


def _forbidden():
    return Response({"detail": "Você não pode gerenciar este serviço."},
                    status=status.HTTP_403_FORBIDDEN)


def _bad(msg):
    return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
