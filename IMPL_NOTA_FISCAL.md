# PLANO DE IMPLEMENTAÇÃO — GERAR NOTA FISCAL (NFS-e)

> **Versão:** 1.0 — 2026-06-15
> **Baseado em:** HIVEE Marketplace (Django 6 + React 19)
> **Feature:** Geração de Nota Fiscal de Serviço Eletrônica (NFS-e padrão nacional) para serviços realizados

---

## Sumário Executivo

Implementar um fluxo completo de **emissão de NFS-e** no HIVEE, seguindo o padrão nacional obrigatório a partir de 2026 (Reforma Tributária). O prestador poderá emitir nota fiscal para um serviço concluído, com split de pagamento entre plataforma e prestador. A emissão pode ser feita via API externa (NFE.io, Nuvem Fiscal) ou via integração direta com a SEFIN Nacional (certificado A1).

**Pré-requisito:** Feature de "Serviços em Andamento" (rastreamento) deve existir — esta feature depende de um serviço com status `concluido` para emitir a nota.

---

## Stack da Feature

| Camada | Tecnologia |
|--------|-----------|
| Modelos | Django Models (`servico`, `nota_fiscal`, `nota_fiscal_item`) |
| API de Emissão | NFE.io REST API (ou Nuvem Fiscal) — recomendado por ser white-label e ter split de pagamento nativo |
| Alternativa Nacional | `pynfse-nacional` (SEFIN) — exige certificado digital A1 ICP-Brasil |
| Backend REST | DRF ViewSet (mesmo padrão do `ProviderViewSet`) |
| Frontend | React + Tailwind, página `MinhaConta` (prestador) + área do cliente |
| Background | Celery / APScheduler (já existe no `agent`) para reemissão e consulta |
| Webhook | Receber callback de autorização da NFS-e |

---

## Modelos de Dados

### `servico` (novo app `billing` ou dentro de `catalog`)

```python
class Servico(models.Model):
    """Serviço contratado entre cliente e prestador."""
    STATUS = [
        ("solicitado", "Solicitado"),
        ("em_andamento", "Em Andamento"),
        ("concluido", "Concluído"),
        ("cancelado", "Cancelado"),
    ]

    provider = models.ForeignKey("catalog.Provider", on_delete=models.CASCADE, related_name="servicos")
    cliente = models.ForeignKey("catalog.Cliente", on_delete=models.CASCADE, related_name="servicos")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    descricao = models.TextField()
    valor_combinado = models.DecimalField(max_digits=10, decimal_places=2)
    comissao_plataforma = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)  # %
    data_agendamento = models.DateTimeField(null=True, blank=True)
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="solicitado")
    endereco = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"

    def __str__(self):
        return f"Serviço #{self.id} - {self.provider.name} x {self.cliente.nome}"
```

### `nota_fiscal`

```python
class NotaFiscal(models.Model):
    """Nota Fiscal de Serviço Eletrônica (NFS-e padrão nacional)."""
    STATUS = [
        ("pendente", "Pendente"),
        ("autorizada", "Autorizada"),
        ("rejeitada", "Rejeitada"),
        ("cancelada", "Cancelada"),
    ]

    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name="notas_fiscais")
    prestador = models.ForeignKey("catalog.Provider", on_delete=models.CASCADE, related_name="notas_fiscais")
    cliente_cpf_cnpj = models.CharField(max_length=18)
    cliente_nome = models.CharField(max_length=200)
    cliente_email = models.EmailField(blank=True)
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2)
    valor_comissao = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_liquido_prestador = models.DecimalField(max_digits=10, decimal_places=2)
    aliquota_iss = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    valor_iss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    codigo_servico_municipio = models.CharField(max_length=20, blank=True)
    descricao_servico = models.TextField()
    chave_acesso = models.CharField(max_length=50, unique=True, null=True, blank=True)
    numero_nfse = models.CharField(max_length=20, null=True, blank=True)
    xml_autorizado = models.TextField(blank=True)
    link_danfse = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pendente")
    motivo_rejeicao = models.TextField(blank=True)
    metadados_api = models.JSONField(default=dict, blank=True)
    emitida_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"

    def __str__(self):
        return f"NFS-e #{self.numero_nfse or self.id} - {self.prestador.name}"
```

### `nota_fiscal_item` (opcional — para serviços compostos)

```python
class NotaFiscalItem(models.Model):
    nota_fiscal = models.ForeignKey(NotaFiscal, on_delete=models.CASCADE, related_name="itens")
    descricao = models.CharField(max_length=200)
    quantidade = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
```

---

## API REST (Backend)

### Endpoints

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/api/servicos/` | Lista serviços do usuário logado | `IsAuthenticated` |
| POST | `/api/servicos/` | Cria novo serviço | `IsAuthenticated` |
| GET | `/api/servicos/{id}/` | Detalhe do serviço | `IsAuthenticated` |
| PATCH | `/api/servicos/{id}/` | Atualiza status do serviço | `IsAuthenticated` |
| POST | `/api/servicos/{id}/emitir-nota/` | Emite NFS-e para serviço concluído | `IsAuthenticated` (prestador) |
| GET | `/api/notas-fiscais/` | Lista notas fiscais do usuário | `IsAuthenticated` |
| GET | `/api/notas-fiscais/{id}/` | Detalhe da nota fiscal | `IsAuthenticated` |
| GET | `/api/notas-fiscais/{id}/pdf/` | Download do DANFSe em PDF | `IsAuthenticated` |
| POST | `/api/notas-fiscais/{id}/cancelar/` | Cancelamento da NFS-e | `IsAuthenticated` (prestador) |

### ViewSets (padrão DRF, mesmo pattern do `ProviderViewSet`)

```python
# backend/billing/views.py
class ServicoViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Retorna serviços onde o usuário é cliente OU prestador."""
        servicos = Servico.objects.filter(
            Q(user=request.user) | Q(provider__owner=request.user)
        ).select_related("provider", "cliente")
        return Response(ServicoSerializer(servicos, many=True).data)

    @action(detail=True, methods=["post"])
    def emitir_nota(self, request, pk=None):
        servico = self.get_object()
        if servico.status != "concluido":
            return Response({"detail": "Serviço precisa estar concluído."}, status=400)
        if servico.notas_fiscais.filter(status__in=["pendente", "autorizada"]).exists():
            return Response({"detail": "Já existe nota fiscal para este serviço."}, status=409)
        nota = emitir_nfse(servico)  # função de integração
        return Response(NotaFiscalSerializer(nota).data, status=201)
```

---

## Integração com API de NFS-e

### Opção A — NFE.io (Recomendada para MVP)

**Vantagens:** Não exige certificado A1, API REST moderna, whitabel, split de pagamento nativo, webhooks.

**Configuração:**
```env
NFEIO_API_KEY=sk_...
NFEIO_ENVIRONMENT=sandbox  # sandbox | production
```

**Função de emissão:**
```python
# backend/billing/nfeio.py
import os, requests
from django.conf import settings

NFEIO_API_KEY = os.getenv("NFEIO_API_KEY")
NFEIO_BASE = "https://api.nfe.io" if settings.DEBUG else "https://api.nfe.io"

def emitir_nfse(servico: Servico) -> NotaFiscal:
    """Emite NFS-e via NFE.io."""
    prestador = servico.provider
    cliente = servico.cliente

    payload = {
        "cliente": {
            "cpf_cnpj": re.sub(r"\D", "", cliente.cpf),
            "nome": cliente.nome,
            "email": cliente.email,
        },
        "servico": {
            "descricao": servico.descricao,
            "valor": float(servico.valor_combinado),
            "iss_retido": False,
            "codigo_servico": "01.01",  # municipio-specific
        },
        "split": {
            "comissao": float(servico.comissao_plataforma),
            "valor_comissao": float(servico.valor_combinado * servico.comissao_plataforma / 100),
        }
    }

    resp = requests.post(
        f"{NFEIO_BASE}/v2/nota-fiscal",
        headers={"Authorization": NFEIO_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    data = resp.json()

    nota = NotaFiscal.objects.create(
        servico=servico,
        prestador=prestador,
        cliente_cpf_cnpj=cliente.cpf,
        cliente_nome=cliente.nome,
        valor_servico=servico.valor_combinado,
        valor_liquido_prestador=float(servico.valor_combinado * (1 - servico.comissao_plataforma / 100)),
        descricao_servico=servico.descricao,
        chave_acesso=data.get("chave_acesso"),
        numero_nfse=data.get("numero"),
        xml_autorizado=data.get("xml"),
        link_danfse=data.get("danfse_url"),
        status="autorizada",
        metadados_api=data,
        emitida_em=timezone.now(),
    )
    return nota
```

### Opção B — SEFIN Nacional (via pynfse-nacional)

**Vantagens:** Gratuito (só custo do certificado A1), padrão oficial do governo.

**Necessário:**
- Certificado digital A1 ICP-Brasil (ex: Certisign, Soluti) — ~R$ 200/ano
- Prestador com CNPJ (MEI, Simples, etc.)
- Homologação: `sefin.producaorestrita.nfse.gov.br`
- Produção: `sefin.nfse.gov.br`

```python
# backend/billing/sefim.py
from pynfse_nacional import (
    Ambiente, Certificado, NfseClient, Prestador, Tomador, Servico, Valores
)

def emitir_nfse_sefin(servico: Servico) -> NotaFiscal:
    certificado = Certificado(
        arquivo="caminho/certificado.pfx",
        senha="senha",
    )
    client = NfseClient(
        certificado=certificado,
        ambiente=Ambiente.HOMOLOGACAO if settings.DEBUG else Ambiente.PRODUCAO,
    )

    prestador_obj = Prestador(
        cnpj=re.sub(r"\D", "", servico.provider.cnpj or ""),
        im="",  # inscricao municipal
        regime_tributario=1,  # Simples Nacional
    )
    tomador_obj = Tomador(
        cpf_cnpj=re.sub(r"\D", "", servico.cliente.cpf),
        nome=servico.cliente.nome,
    )
    servico_obj = Servico(
        descricao=servico.descricao,
        valor=float(servico.valor_combinado),
        codigo_servico="01.01",
        aliquota_iss=2.0,
    )

    resultado = client.transmitir(
        prestador=prestador_obj,
        tomador=tomador_obj,
        servico=servico_obj,
    )

    nota = NotaFiscal.objects.create(
        servico=servico,
        prestador=servico.provider,
        cliente_cpf_cnpj=servico.cliente.cpf,
        cliente_nome=servico.cliente.nome,
        valor_servico=servico.valor_combinado,
        valor_liquido_prestador=float(servico.valor_combinado),
        descricao_servico=servico.descricao,
        chave_acesso=resultado.chave_acesso,
        numero_nfse=resultado.numero_nfse,
        xml_autorizado=resultado.xml,
        status="autorizada",
        emitida_em=timezone.now(),
    )
    return nota
```

---

## Frontend

### Páginas Novas

| Rota | Tela | Descrição |
|------|------|-----------|
| `/minha-conta/servicos` | `ServicosPage` | Lista de serviços (cliente vê os que contratou; prestador vê os que prestou) |
| `/minha-conta/servicos/{id}` | `ServicoDetailPage` | Detalhe do serviço, botão "Emitir Nota Fiscal" (prestador) |
| `/minha-conta/notas-fiscais` | `NotasFiscaisPage` | Lista de notas emitidas/recebidas |
| `/minha-conta/notas-fiscais/{id}` | `NotaFiscalDetailPage` | Detalhe da nota, link para DANFSe, botão cancelar |

### Modificações em Rotas (frontend/src/main.tsx)

```tsx
<Route path="/minha-conta" element={<MinhaConta />} />
<Route path="/minha-conta/servicos" element={<ServicosPage />} />
<Route path="/minha-conta/servicos/:id" element={<ServicoDetailPage />} />
<Route path="/minha-conta/notas-fiscais" element={<NotasFiscaisPage />} />
<Route path="/minha-conta/notas-fiscais/:id" element={<NotaFiscalDetailPage />} />
```

### Botão "Emitir Nota" no Perfil do Prestador (ProviderProfile.tsx)

Após o serviço ser concluído (via feature de rastreamento), o prestador vê um botão:

```tsx
// Dentro de ProviderProfile.tsx ou ServicoDetailPage
<button onClick={() => emitirNota(servicoId)} className="btn-gold w-full py-3.5 text-base">
  <FileText className="h-4 w-4" /> Emitir Nota Fiscal
</button>
```

---

## Fluxo Completo

```
1. Cliente contrata prestador (via chat ou diretamente)
       ↓
2. Serviço criado com status "solicitado"
       ↓
3. [Feature: Rastreamento] Prestador inicia → status "em_andamento"
       ↓
4. Prestador conclui → status "concluido"
       ↓
5. Prestador clica "Emitir Nota Fiscal" no serviço concluído
       ↓
6. Backend valida dados do prestador (CNPJ obrigatório)
       ↓
7. Backend chama API externa (NFE.io / SEFIN)
       ↓
8. API retorna NFS-e autorizada → salva no banco
       ↓
9. Nota fica visível para cliente e prestador
       ↓
10. Cliente recebe link do DANFSe (PDF) por e-mail/WhatsApp
```

---

## Segurança e Compliance

- [ ] Prestador **deve ter CNPJ** para emitir NFS-e (MEI, Simples, etc.)
- [ ] Validar CPF/CNPJ do tomador antes de emitir
- [ ] Implementar idempotência na chamada da API (evitar notas duplicadas)
- [ ] Logs completos de todas as requisições fiscais (auditoria)
- [ ] Ambiente de homologação separado para testes
- [ ] Não expor chaves de API no frontend
- [ ] Respeitar LGPD: dados fiscais trafegam criptografados

---

## Sprints de Implementação

### Sprint 1 — Models e API Básica
- [ ] Criar app `billing` (ou adicionar ao `catalog`)
- [ ] Criar models `Servico`, `NotaFiscal`, `NotaFiscalItem`
- [ ] Migrações e admin
- [ ] Serializers e ViewSets básicos (CRUD de serviços)
- [ ] Testes dos models

### Sprint 2 — Integração com API NF
- [ ] Escolher provedor: NFE.io (MVP) ou SEFIN Nacional
- [ ] Criar módulo `billing/nfeio.py` ou `billing/sefim.py`
- [ ] Função `emitir_nfse(servico)` com validações
- [ ] Endpoint `POST /api/servicos/{id}/emitir-nota/`
- [ ] Endpoint `POST /api/notas-fiscais/{id}/cancelar/`
- [ ] Endpoint `GET /api/notas-fiscais/{id}/pdf/`
- [ ] Testes com mock da API externa

### Sprint 3 — Frontend
- [ ] Criar `ServicosPage.tsx` (lista de serviços)
- [ ] Criar `ServicoDetailPage.tsx` (detalhe + botão emitir)
- [ ] Criar `NotasFiscaisPage.tsx` (lista de notas)
- [ ] Criar `NotaFiscalDetailPage.tsx` (detalhe da nota + DANFSe)
- [ ] Adicionar rotas no React Router
- [ ] Adicionar métodos no `api.ts`

### Sprint 4 — Integração com Rastreamento e Agente
- [ ] Conectar com feature de "Serviços em Andamento" (outro agente)
- [ ] Webhook n8n/agente: quando serviço for concluído, notificar prestador para emitir nota
- [ ] Enviar link do DANFSe via WhatsApp/chat do site
- [ ] Dashboard de notas fiscais no admin

---

## Dependências Python (requirements.txt)

```
# Para integrar com NFE.io
requests>=2.31.0  # já existe

# Para integrar com SEFIN Nacional (opcional)
pynfse-nacional>=0.1.0  # https://github.com/roberto-mello/pynfse-nacional
# ou
nfse-nacional>=0.1.0    # https://github.com/UlyssesMatsuyama/nfse_nacional
# ou
brans-nfe>=0.1.0        # https://github.com/badbrans/brans-nfe

# Para PDF do DANFSe
weasyprint>=60.0        # ou reportlab
```

---

## Links de Referência

- [NFE.io API Docs](https://nfe.io/docs/rest-api/)
- [NFE.io Blog — API para Marketplaces com Split](https://nfe.io/blog/integracao/api-de-nota-fiscal-para-marketplaces-como-gerenciar-multiplos-emissores-e-split-de-pagamento/)
- [SEFIN Nacional — Portal NFS-e](https://www.gov.br/nfse)
- [SEFIN Nacional — API Docs](https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional/docs/index)
- [pynfse-nacional (Python SDK)](https://github.com/roberto-mello/pynfse-nacional)
- [nfse_nacional (Python SDK)](https://github.com/UlyssesMatsuyama/nfse_nacional)
- [brans-nfe (Python SDK)](https://github.com/badbrans/brans-nfe)
- [Reforma Tributária 2026 — NT 009](https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nt-009-se-cgnfse-v1-0-1.pdf)
- [Cora — Emissão NFS-e API](https://developers.cora.com.br/reference/emiss%C3%A3o-nota-fiscal-servico)

---

## Anotações do Review (Código Atual)

| Item | Observação |
|------|-----------|
| `Provider` já tem `hourly_rate`, `jobs_done` | Ótimo para compor valor do serviço |
| `Cliente` model tem `cpf`, `email`, `telefone` | Dados mínimos para nota fiscal já existem |
| `UserProfile` tem `cpf`, `cpf_status` | Pode ser usado para validação fiscal |
| `Provider` **não tem CNPJ** | **Necessário adicionar** para emissão de NFS-e |
| `Provider.owner` → `User` → `UserProfile.cpf` | Fluxo de PF está ok, mas PJ exige CNPJ |
| Já existe `agent` com APScheduler | Pode agendar reemissão/consulta de notas |
| Já existe envio WhatsApp (WAHA) | Pode notificar cliente quando nota for emitida |
| Já existe chat no site com WebSocket | Pode enviar link do DANFSe em tempo real |
| Autenticação via cookie httpOnly | Reutilizar para proteger endpoints fiscais |
