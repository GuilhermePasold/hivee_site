# Sistema de Logs — Super Agente HIVEE

## Arquitetura

Cada módulo do app `agent` possui seu próprio logger via `logging.getLogger(__name__)`.

### Formato

```
[HH:MM:SS] agent.core.processar_mensagem:42  INFO  Mensagem processada para 5511999999999
```

### Níveis usados

| Nível | Quando usar |
|---|---|
| `DEBUG` | Fluxo detalhado: push no buffer, flush, cada bloco enviado, cada tool call executada |
| `INFO` | Eventos importantes: início/fim de processamento, lead criado, webhook recebido, prestador encontrado |
| `WARNING` | Recuperável: lead não encontrado, provider slug inexistente, fallback de bloco usado |
| `ERROR` | Erro recuperável: falha na WAHA (WhatsApp HTTP API), falha no RAG |
| `CRITICAL` | — (reservado para falhas de inicialização) |
| `exception()` | Sempre usar em `except` para capturar stacktrace completo |

---

## Módulos e o que cada um loga

### `backend/agent/buffer.py`

```
DEBUG  Buffer[5511999999999] acumulou 3 mensagens | flush em 12s
DEBUG  Buffer[5511999999999] flush vazio, ignorando
INFO   Buffer[5511999999999] flush com 2 msgs únicas | total=3 | conteudo=quero um eletricista...
```

### `backend/agent/core.py` (coração do agente)

```
INFO   processar_mensagem[5511999999999] inicio | msg=preciso de um eletricista em sp
DEBUG  RAG contexto: <primeiros 120 chars do contexto>
INFO   Tool call buscar_prestadores args={'query': 'eletricista', 'cidade': 'são paulo'}
INFO   Tool result: 3 prestadores encontrados
WARNING  OpenAI retornou resposta vazia para 5511999999999
INFO   Provider recomendado: joao-eletricista
INFO   processar_mensagem[5511999999999] concluido com sucesso
ERROR  processar_mensagem[5511999999999] ERRO nao tratado
        (stacktrace completo)
```

### `backend/agent/webhooks.py`

```
WARNING  Webhook ignorado: sem remoteJid | payload={...}
DEBUG  Webhook ignorado: grupo 5511999999999@s.whatsapp.net
INFO   Webhook[5511999999999] type=conversation | conteudo=preciso de um eletricista
```

### `backend/agent/formatador.py`

```
INFO   formatar_e_enviar[5511999999999] inicio | 450 chars
INFO   Resposta dividida em 3 blocos
DEBUG  Enviando bloco 1/3: Recomendo o João, ele é um ótimo eletricista...
DEBUG  Aguardando 6s antes do prox bloco...
INFO   formatar_e_enviar[5511999999999] concluido
WARNING  Falha ao dividir blocos via GPT, fallback para paragrafos
```

### `backend/agent/waha.py`

```
ERROR  Falha ao enviar WhatsApp para 5511999999999: ConnectionError
```

### `backend/agent/rag.py`

```
ERROR  Falha na consulta RAG: <erro>
```

### `backend/agent/audio.py` / `vision.py`

```
ERROR  Falha ao transcrever áudio: <erro>
ERROR  Falha ao analisar imagem: <erro>
```

---

## Setup inicial

Em `backend/agent/logging_config.py`:

```python
import logging
import sys

def setup_logging():
    logger = logging.getLogger("agent")
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s.%(funcName)s:%(lineno)d  %(levelname)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
```

Chamado uma vez no `apps.py` ou no `ready()`.

---

## Como usar para debugar

### Acompanhar o fluxo completo de uma mensagem

```bash
python manage.py simulate_message --telefone=5511999999999 --mensagem="preciso de eletricista"
```

A saída mostrará, em ordem:

1. `Buffer[5511999999999] acumulou 1 mensagens | flush em 12s` ← push no buffer
2. `Buffer[5511999999999] flush com 1 msgs únicas` ← após 12s
3. `processar_mensagem[5511999999999] inicio` ← core começa
4. `RAG contexto: ...` ← contexto do Supabase
5. `Tool call buscar_prestadores args=...` ← chamada da ferramenta
6. `Tool result: 3 prestadores encontrados` ← resultado
7. `formatar_e_enviar[5511999999999] inicio | 450 chars` ← formatador começa
8. `Enviando bloco 1/3: Recomendo o João...` ← cada bloco
9. `Aguardando 6s antes do prox bloco...` ← delay entre blocos
10. `formatar_e_enviar[5511999999999] concluido` ← pronto

### Erro comum

| Log | Provável causa |
|---|---|
| `Webhook ignorado: sem from` | Payload da WAHA veio vazio ou formato inesperado |
| `OpenAI retornou resposta vazia` | Tool call não retornou conteúdo ou GPT falhou |
| `Lead nao encontrado` | Mensagem chegou mas lead não foi criado (webhook bugou) |
| `Falha ao dividir blocos via GPT` | GPT-4o-mini retornou JSON inválido |
| `Provider slug X nao encontrado no banco` | GPT alucinou um slug que não existe |

---

## Regras para o agente de código

1. TODO novo arquivo .py deve começar com `import logging` e `logger = logging.getLogger(__name__)`
2. TODO `except` deve ter `logger.exception(...)` ou `logger.error(...)`
3. NUNCA `print()` — sempre `logger.info()` ou `logger.debug()`
4. Logs de erro DEVEM incluir contexto suficiente para reproduzir o problema (telefone, args, etc.)
