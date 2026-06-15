# Relatório de Análise de Segurança - HIVEE

> **Data:** 15/06/2026<br>
> **Escopo:** Todo o projeto (backend Django + frontend React)<br>
> **Arquivos .md excluídos da análise**<br>
> **Total de falhas encontradas:** 45

---

## Resumo por Severidade

| Severidade | Quantidade |
|------------|-----------|
| 🔴 CRÍTICO  | 2 |
| 🟠 ALTO     | 8 |
| 🟡 MÉDIO    | 22 |
| 🔵 BAIXO    | 13 |

---

## 🔴 CRÍTICO

### C-01: Live OpenAI API Key exposta em disco

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/.env:3` |
| **Tipo** | Vazamento de credencial |
| **Descrição** | Chave de API da OpenAI ativa e funcional armazenada em texto claro no arquivo `.env` no disco. Qualquer pessoa com acesso à máquina pode utilizar esta chave para chamadas à API OpenAI (GPT-4.1, Whisper, embeddings) gerando custos financeiros. |
| **Chave** | `[REDACTED_OPENAI_API_KEY]` |
| **Remediação** | Revogar a chave imediatamente no dashboard da OpenAI. Gerar nova chave. Garantir que `.env` esteja em `.gitignore` (já está, mas o arquivo existe em disco). |

### C-02: Live Evolution/WAHA API Key exposta em arquivo de workflow

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `message (1).txt:6443` |
| **Tipo** | Vazamento de credencial |
| **Descrição** | Chave de API do Evolution API (WhatsApp) exposta em arquivo texto não versionado (`message (1).txt`). Este arquivo é um export do n8n com 8433 linhas e contém uma chave ativa que concede acesso a uma instância do WhatsApp. O arquivo **não está no `.gitignore`**. |
| **Remediação** | Revogar a chave imediatamente. Adicionar `message (1).txt` ao `.gitignore`. Remover ou criptografar o arquivo. |

---

## 🟠 ALTO

### A-01: CORS permite todas as origens

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/hivee/settings.py:135` |
| **CWE** | CWE-942 - Permissive Cross-domain Policy with Untrusted Domains |
| **Descrição** | `CORS_ALLOW_ALL_ORIGINS = True` permite que qualquer site faça requisições cross-origin à API. Combinado com autenticação baseada em cookie httpOnly, aumenta o risco de ataques CSRF e exfiltração de dados. |
| **Remediação** | Configurar `CORS_ALLOWED_ORIGINS` com lista explícita de origens confiáveis (ex: `https://hivee.vercel.app`). |

### A-02: Webhook WAHA sem autenticação

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/agent/webhooks.py:47` |
| **CWE** | CWE-306 - Missing Authentication for Critical Function |
| **Descrição** | O endpoint `POST /api/agent/webhook/` não possui nenhuma autenticação (sem permission class, sem API key, sem IP whitelist). Qualquer atacante que descubra este endpoint pode enviar mensagens arbitrárias processadas pelo agente de IA, baixar arquivos para o servidor e enviar mensagens WhatsApp. |
| **Remediação** | Adicionar verificação de chave secreta compartilhada (ex: `X-Webhook-Secret`), whitelist de IPs, ou token não adivinhável na URL. |

### A-03: SSRF via download de mídia no WAHA

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/agent/waha.py:86` |
| **CWE** | CWE-918 - Server-Side Request Forgery (SSRF) |
| **Descrição** | A função `baixar_midia()` recebe uma `media_url` diretamente do payload do webhook (controlado pelo usuário/atacante) e faz `requests.get(media_url, ...)` sem qualquer validação. Um atacante pode forçar o servidor a fazer requisições para recursos internos (`http://169.254.169.254/`, `http://localhost:3000/`, etc.). |
| **Remediação** | Validar URL contra uma allowlist de domínios permitidos. Usar apenas caminhos relativos. |

### A-04: Upload de avatar sem validação de tipo de arquivo

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/views/api_views.py:641-651` |
| **CWE** | CWE-434 - Unrestricted Upload of File with Dangerous Type |
| **Descrição** | O endpoint de upload de avatar aceita qualquer tipo de arquivo. Não há validação de: tipo MIME real (magic bytes), tamanho máximo, ou extensão permitida. Um atacante pode fazer upload de HTML com JavaScript (XSS persistente), SVG malicioso, ou arquivo muito grande (DoS). |
| **Remediação** | Validar tipo de conteúdo com `python-magic` ou PIL. Restringir a JPEG/PNG/WebP. Limitar tamanho do arquivo. |

### A-05: XSS armazenado via Leaflet divIcon

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `frontend/src/pages/ProviderProfile.tsx:17-23` |
| **CWE** | CWE-79 - Improper Neutralization of Input During Web Page Generation (XSS) |
| **Descrição** | A URL do avatar do prestador é interpolada diretamente em HTML para o `L.divIcon` do Leaflet: `` html: `<div ...><img src="${avatar}" .../></div>` ``. Se um atacante controlar o campo `avatar` (via banco comprometido, SQL injection, etc.), pode injetar HTML/JavaScript arbitrário que executa no navegador de qualquer usuário que visualizar o perfil. |
| **Remediação** | Sanitizar a URL antes de interpolar. Usar `L.icon()` com `iconUrl` próprio em vez de `divIcon`. Escapar HTML com DOMPurify. |

### A-06: Permission default AllowAny

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/hivee/settings.py:106` |
| **CWE** | CWE-862 - Missing Authorization |
| **Descrição** | A configuração global do DRF define `DEFAULT_PERMISSION_CLASSES` como `AllowAny`. Qualquer view que não defina explicitamente uma permission class fica publicamente acessível sem autenticação. |
| **Remediação** | Alterar default para `IsAuthenticated` ou `IsAuthenticatedOrReadOnly`. Definir permissões explicitamente em cada endpoint público. |

### A-07: CPF (PII) exposto em respostas da API

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/serializers.py:269-273` |
| **CWE** | CWE-200 - Exposure of Sensitive Information to an Unauthorized Actor |
| **Descrição** | O CPF (equivalente brasileiro ao SSN) é retornado integralmente nas respostas das APIs `/api/auth/me/`, `/api/auth/login/` e `/api/auth/register/`. CPF é considerado dado pessoal sensível pela LGPD. |
| **Remediação** | Mascarar o CPF (ex: `***.XXX.XXX-**`). Retornar completo apenas em endpoint específico, autenticado e auditado. |

### A-08: Infraestrutura interna exposta em arquivo de workflow

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `message (1).txt:6296,6439,6442,6445` |
| **Tipo** | Exposure of sensitive infrastructure details |
| **Descrição** | O arquivo contém URLs completas de infraestrutura interna: n8n host (`swimmingstingray-n8n.cloudfy.live`), servidor Evolution API (`swimmingstingray-evolution.cloudfy.live`), webhooks, e IDs de credenciais do n8n (Supabase, OpenAI, Postgres, Redis). |
| **Remediação** | Remover ou criptografar o arquivo. Nunca versionar exports de workflow. |

---

## 🟡 MÉDIO

### M-01: DEBUG=True por padrão

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/hivee/settings.py:11` |
| **Descrição** | `DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"` - Se a variável de ambiente não for definida, DEBUG é True. Em produção, páginas de erro detalhadas vazam stack traces, código fonte e variáveis de ambiente. |
| **Remediação** | Remover fallback. Exigir definição explícita em produção (`DJANGO_DEBUG=False`). |

### M-02: Chave secreta Django com fallback hardcoded

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/hivee/settings.py:10` |
| **Descrição** | `SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-hivee-dev-fallback")` - Fallback hardcoded. Permite falsificação de sessão e ataques de assinatura criptográfica se a env var não estiver configurada. |
| **Remediação** | Remover fallback. Exigir configuração via ambiente. |

### M-03: Token de API retornado no body da resposta

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/views/api_views.py:445-447` |
| **Descrição** | O token de autenticação é definido como cookie httpOnly (correto) MAS também retornado no corpo da resposta JSON. Isso permite que o token seja logado por proxies, servidores intermediários ou extensões de navegador. |
| **Remediação** | Remover `token` do corpo da resposta. Manter apenas o cookie httpOnly. |

### M-04: CSRF - Autenticação por cookie sem proteção CSRF nas views DRF

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/authentication.py:16-27` |
| **Descrição** | `CookieTokenAuthentication` lê o token de um cookie enviado automaticamente pelo navegador. Views DRF não impõem proteção CSRF (usam token auth, não session auth). Combinado com `CORS_ALLOW_ALL_ORIGINS=True`, um site malicioso pode fazer requisições autenticadas cross-origin. |
| **Remediação** | Implementar proteção CSRF ou usar cabeçalho `Authorization` em vez de cookie para transmitir o token. |

### M-05: IDOR no WebSocket do chat

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/agent/consumers.py:23-24` / `frontend/src/pages/ChatPage.tsx:18` |
| **CWE** | CWE-639 - Authorization Bypass Through User-Controlled Key |
| **Descrição** | O WebSocket usa o ID numérico do usuário na URL (`/ws/chat/site_user_{id}/`). Não há verificação no backend de que o usuário autenticado é dono daquele telefone/chat. Qualquer usuário autenticado pode conectar no chat de outro usuário enumerando IDs. |
| **Remediação** | Verificar no consumer se o `ChatLead` pertence ao usuário autenticado. |

### M-06: Vazamento de mensagem de exceção para o cliente

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/views/api_views.py:625-629` |
| **Descrição** | `return Response({"detail": f"Erro ao carregar cidades: {e}"})` - A mensagem real da exceção Python é retornada ao cliente, vazando detalhes da infraestrutura interna. |
| **Remediação** | Logar a exceção no servidor e retornar mensagem genérica ao cliente. |

### M-07: DoesNotExist não tratado no retrieve

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/views/api_views.py:190` |
| **Descrição** | `Provider.objects.get(slug=slug)` sem `get_object_or_404()` ou try/except. Se o slug não existir, retorna 500 Internal Server Error em vez de 404. |
| **Remediação** | Usar `get_object_or_404()` ou tratar a exceção adequadamente. |

### M-08: Silent exception swallowing no LogoutView

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/views/api_views.py:500-503` |
| **Descrição** | `except Exception: pass` - Todas as exceções na deleção do token são silenciosamente engolidas. O logout parece bem-sucedido mas o token permanece válido. |
| **Remediação** | Logar a exceção ao menos. |

### M-09: Rate limiting fraco em endpoints de autenticação

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/hivee/settings.py:111-118` |
| **Descrição** | Em modo DEBUG, o throttle anônimo é 1000 requisições/hora. Não há throttling específico para login/register (proteção contra brute-force). |
| **Remediação** | Implementar `LoginRateThrottle` (ex: 5 tentativas/minuto por IP). Reduzir limite em produção. |

### M-10: SQLite em produção

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/hivee/settings.py:77-80` |
| **Descrição** | Banco SQLite (`hivee.db`) no diretório do projeto. SQLite não suporta escrita concorrente, não tem controle de acesso por usuário, e o arquivo pode ser exposto se o servidor web estiver mal configurado. |
| **Remediação** | Usar PostgreSQL em produção. |

### M-11: InMemoryChannelLayer para WebSockets

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/hivee/settings.py:70-74` |
| **Descrição** | Canal em memória para Channels não funciona com múltiplos workers e perde todos os dados ao reiniciar o servidor. |
| **Remediação** | Usar Redis como channel layer em produção. |

### M-12: Documentação Swagger/Admin exposta

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/hivee/urls.py:15-17` |
| **Descrição** | `/api/schema/` e `/api/docs/` (Swagger) expõem toda a estrutura da API incluindo todos os endpoints, campos, e requisitos de autenticação sem restrição de IP. |
| **Remediação** | Restringir em produção ou desabilitar `SERVE_INCLUDE_SCHEMA`. |

### M-13: Telefone (PII) exposto na API

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/serializers.py:259-263` |
| **Descrição** | Número de telefone do usuário é retornado nas respostas da API sem necessidade. Telefone é dado pessoal sensível. |
| **Remediação** | Retornar telefone apenas quando explicitamente necessário e com consentimento do usuário. |

### M-14: Payload de requisição logado no banco

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/logs/middleware.py:44` |
| **Descrição** | Parâmetros de query string (GET) são armazenados no banco via `LogEvent`. Se parâmetros sensíveis forem passados via URL, ficarão persistidos. |
| **Remediação** | Sanitizar parâmetros antes de logar. Remover campos que possam conter PII. |

### M-15: Chamada externa à ReceitaWS com CPF do usuário

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/serializers.py:33-36` |
| **Descrição** | CPF do usuário é enviado para `receitaws.com.br` via `urllib.request.urlopen()`. Dado sensível transmitido a terceiro sem consentimento explícito do usuário. |
| **Remediação** | Informar usuário sobre compartilhamento com terceiros. Implementar rate limiting. |

### M-16: Parâmetro UF não validado em chamada à API IBGE

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/views/api_views.py:609-613` |
| **Descrição** | O parâmetro `uf` da URL é interpolado diretamente na URL da API do IBGE sem validação. |
| **Remediação** | Validar `uf` contra lista de estados brasileiros válidos antes de fazer a requisição. |

### M-17: Injeção de URL javascript: no ChatWidget

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `frontend/src/components/ChatWidget.tsx:244` |
| **CWE** | CWE-79 (via href injection) |
| **Descrição** | O link do prestador (`provider.link`) vindo de mensagens WebSocket é usado em `<a href={provider.link}>` sem validação. Um servidor comprometido pode retornar `javascript:alert(document.cookie)` e executar código no clique. |
| **Remediação** | Validar que `provider.link` começa com `https://` antes de renderizar. |

### M-18: CPF exibido sem máscara no frontend

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `frontend/src/pages/MinhaConta.tsx:109` |
| **Descrição** | O CPF do usuário é exibido integralmente na página "Minha Conta". Dado sensível visível para qualquer pessoa com acesso à conta ou à tela. |
| **Remediação** | Mascarar CPF (ex: `***.XXX.XXX-**`). |

### M-19: Detalhes de erro da API expostos ao usuário

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `frontend/src/lib/api.ts:40-48` / `frontend/src/pages/Login.tsx:22` / `frontend/src/pages/Register.tsx:46` |
| **Descrição** | Mensagens de erro cruas da API são passadas diretamente para o usuário. Se o backend retornar stack traces ou detalhes internos, serão exibidos. |
| **Remediação** | Sanitizar mensagens de erro no frontend antes de exibir. |

### M-20: Sem validação client-side de senha mínima

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `frontend/src/pages/Register.tsx:58` |
| **Descrição** | O placeholder menciona "mínimo 6 caracteres" mas não há validação client-side. Usuários podem enviar senhas vazias ou de 1 caractere. |
| **Remediação** | Adicionar validação de tamanho mínimo no frontend. |

### M-21: Proxy Vite expõe arquitetura interna

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `frontend/vite.config.ts:13-17` |
| **Descrição** | Configuração do proxy Vite revela que o backend roda em `http://127.0.0.1:8000`, expondo portas e caminhos internos. |
| **Remediação** | Não crítico para dev, mas documentar que deve ser alterado em produção. |

### M-22: Credenciais de teste hardcoded

| Campo | Detalhe |
|-------|---------|
| **Arquivo** | `backend/catalog/tests.py:46,127,137,146` |
| **Descrição** | Senha `senha123` e email `cliente@hivee.dev` hardcoded nos testes. Também mencionado em README: admin `admin` / `admin12345`. |
| **Remediação** | Usar variáveis de ambiente para credenciais de teste ou gerar dinamicamente. |

---

## 🔵 BAIXO

### B-01: Tamanho mínimo de senha 6 caracteres (settings.py:84)
- NIST recomenda mínimo 8. Senhas de 6 caracteres são mais fáceis de quebrar.

### B-02: Throttle anônimo muito alto em DEBUG (settings.py:116)
- `1000/hour` em DEBUG permite ataques de força bruta.

### B-03: Cookie de sessão sem flags de segurança explícitas (settings.py)
- `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE` não configurados explicitamente.

### B-04: Views MTV (Django templates) sem verificação CSRF explícita (catalog/views/auth_views.py:9-38)
- Formulários dependem do template `{% csrf_token %}` sem verificação adicional.

### B-05: Código morto - ProviderUpdateSerializer nunca usado (catalog/serializers.py:194-241)
- Serializer definido mas nunca importado por nenhuma view. Se um dia for conectado, precisa de verificação de ownership.

### B-06: Navegador expõe parte do email na navbar (frontend/src/components/Navbar.tsx:61)
- `user.email.split("@")[0]` exibe parte do email quando `first_name` não está definido.

### B-07: Campos de senha sem atributo autocomplete (Login.tsx, Register.tsx)
- Pode causar autofill indesejado em computadores compartilhados.

### B-08: Upload de avatar sem validação client-side (BecomeProvider.tsx:97-102)
- Placeholder menciona "Max 5MB" mas não há validação real de tamanho/tipo.

### B-09: Coordenadas de São Paulo hardcoded (Recommended.tsx:6)
- A página sempre mostra prestadores próximos a São Paulo independente da localização real do usuário.

### B-10: Query de busca não sanitizada (Search.tsx:88-89)
- Input do usuário passado como parâmetro URL sem sanitização.

### B-11: Erros silenciosamente engolidos (múltiplos arquivos)
- `.catch(() => undefined)` mascara erros de API.

### B-12: WebSocket usa ws:// em modo dev (ChatWidget.tsx:49)
- Depende do protocolo da página. Correto em produção com HTTPS, mas vulnerável em dev.

### B-13: GSAP innerHTML animation (cinematic-landing-hero.tsx:90)
- `.to(".counter-val", { innerHTML: metricValue, ... })` - atualmente seguro pois `metricValue` é numérico, mas padrão perigoso se o valor mudar para input do usuário.

---

## Estatísticas por Categoria

| Categoria | Qtd |
|-----------|-----|
| **Vazamento de credenciais/secrets** | 5 |
| **Autenticação/Autorização quebrada** | 7 |
| **Cross-Site Scripting (XSS)** | 2 |
| **Server-Side Request Forgery (SSRF)** | 1 |
| **Cross-Origin Resource Sharing (CORS)** | 1 |
| **Exposição de dados sensíveis (PII)** | 5 |
| **CSRF** | 2 |
| **Upload de arquivo inseguro** | 2 |
| **Rate limiting insuficiente** | 2 |
| **Má configuração de segurança** | 6 |
| **Vazamento de informação** | 5 |
| **Error handling inadequado** | 3 |
| **Código morto / boas práticas** | 4 |

---

## Recomendações Prioritárias

1. **🔥 IMEDIATO:** Revogar chave OpenAI e Evolution API expostas localmente
2. **🔴 ALTA:** Corrigir XSS no Leaflet `divIcon` - sanitizar URL do avatar
3. **🔴 ALTA:** Adicionar autenticação no webhook WAHA
4. **🔴 ALTA:** Validar tipo de arquivo no upload de avatar
5. **🔴 ALTA:** Restringir CORS para origens específicas
6. **🔴 ALTA:** Remover CPF integral das respostas da API
7. **🟡 MÉDIA:** Corrigir IDOR no WebSocket do chat
8. **🟡 MÉDIA:** Adicionar proteção CSRF para autenticação por cookie
9. **🟡 MÉDIA:** Validar URL de mídia no WAHA para prevenir SSRF
10. **🟡 MÉDIA:** Adicionar LoginRateThrottle para proteção contra brute-force
