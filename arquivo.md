# Metodos de identificacao e analise dos code smells

Este documento descreve como foram encontrados e analisados os code smells marcados no codigo do projeto HIVEE. A identificacao foi feita por inspecao estatica do codigo, sem aplicar correcoes funcionais.

## 1. Varredura inicial da estrutura do projeto

Primeiro foi feita uma leitura geral da estrutura de pastas para separar codigo-fonte de arquivos gerados ou dependencias externas. Foram priorizadas as pastas:

- `frontend/src`
- `backend/catalog`
- `backend/hivee`

Pastas como `frontend/node_modules`, `frontend/dist`, `__pycache__` e arquivos de build foram ignoradas por nao representarem codigo mantido diretamente pela equipe.

## 2. Busca por pontos de risco e manutencao

Depois foi feita uma busca textual por termos associados a possiveis smells, como:

- configuracoes sensiveis (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`)
- acesso a armazenamento local (`localStorage`)
- chamadas externas e tratamento de erro (`fetch`, `catch`, fallbacks)
- funcoes grandes ou concentradoras de regra (`filter`, `search`, `ordering`, `recommended`)
- coordenadas, pesos e valores numericos fixos

Essa etapa serviu para localizar rapidamente trechos com maior chance de problemas de seguranca, acoplamento, duplicacao de regra ou baixa manutenibilidade.

## 3. Analise de contexto antes da classificacao

Cada trecho encontrado foi lido no contexto do arquivo inteiro ou da funcao ao redor. A analise considerou:

- qual responsabilidade o trecho exerce
- se a regra esta centralizada ou espalhada
- se o valor deveria vir de configuracao, usuario ou dominio
- se o comportamento em caso de erro e claro para o usuario
- se o codigo facilita ou dificulta testes unitarios
- se uma mudanca futura exigiria alterar muitos conceitos no mesmo lugar

So foram marcados trechos onde o problema estava visivel no proprio codigo e causava impacto pratico.

## 4. Criterios usados para classificar os smells

### Configuracao insegura

Arquivo: `backend/hivee/settings.py`

O trecho `ALLOWED_HOSTS = ["*"]` foi identificado como um security smell porque aceita qualquer host. O criterio usado foi verificar configuracoes globais que reduzem protecoes padrao do framework. O problema causado e o aumento da superficie para ataques de Host header, cache poisoning e comportamento inseguro fora do ambiente de desenvolvimento.

### Armazenamento inseguro de credencial

Arquivo: `frontend/src/lib/api.ts`

O uso de `localStorage.getItem(TOKEN_KEY)` foi classificado como security smell porque tokens salvos em `localStorage` podem ser lidos por qualquer script executado na pagina. O criterio usado foi procurar credenciais persistidas no navegador e avaliar o impacto em caso de XSS. O problema causado e facilitar roubo e reutilizacao do token de autenticacao.

### Metodo longo e baixa coesao

Arquivo: `backend/catalog/views/api_views.py`

O metodo `_filtered` foi identificado como long method porque concentra filtragem por categoria, cidade, busca textual, parsing de coordenadas, calculo de distancia e ordenacao. O criterio usado foi observar quantidade de responsabilidades dentro de uma mesma funcao. O problema causado e dificultar testes unitarios, manutencao e reuso de partes isoladas da busca.

### Numeros magicos

Arquivo: `backend/catalog/views/api_views.py`

Na funcao `_score`, valores como `42`, `16`, `10`, `8`, `30` e `24` foram analisados como pesos anonimos da regra de recomendacao. O comentario foi colocado na primeira atribuicao de peso. O criterio usado foi identificar constantes numericas de regra de negocio sem nomes explicativos. O problema causado e dificultar auditoria, calibragem e testes previsiveis da recomendacao.

### Dado hardcoded de localizacao

Arquivo: `frontend/src/pages/Home.tsx`

A constante `SP` com latitude e longitude fixas de Sao Paulo foi identificada como dado hardcoded e primitive obsession de localizacao. O criterio usado foi buscar valores de dominio fixos que deveriam depender de usuario, configuracao ou servico. O problema causado e exibir recomendacoes que parecem personalizadas, mas estao presas a uma cidade especifica.

### Fallback silencioso

Arquivo: `frontend/src/pages/BecomeProvider.tsx`

O valor inicial de latitude e longitude em Sao Paulo antes da tentativa de geocodificacao foi classificado como fallback silencioso. O criterio usado foi analisar fluxos de erro onde a aplicacao continua sem informar o usuario. O problema causado e cadastrar prestadores em localizacao incorreta quando o geocoder falha, tornando o erro dificil de perceber depois.

### Responsabilidades misturadas

Arquivo: `frontend/src/components/ui/cinematic-landing-hero.tsx`

O bloco `INJECTED_STYLES` foi classificado como baixa separacao de preocupacoes e divergent change. O criterio usado foi observar que o mesmo componente concentra CSS extenso, animacoes GSAP e estrutura JSX. O problema causado e aumentar o risco de regressao, pois mudancas visuais e comportamentais passam a acontecer no mesmo arquivo.

## 5. Decisao de nao corrigir os smells

Como a tarefa solicitava apenas comentar os smells, nenhuma solucao foi aplicada. Os comentarios foram adicionados ao lado ou imediatamente junto ao trecho problemático para indicar:

- o tipo do code smell
- a classificacao mais conhecida quando aplicavel
- o motivo pelo qual aquele trecho e um problema
- o impacto esperado na manutencao, seguranca ou experiencia do usuario

## 6. Validacao apos os comentarios

Apos inserir os comentarios, foram feitas validacoes para garantir que a anotacao nao quebrou a sintaxe do projeto:

- `npx tsc --noEmit` no frontend
- `python -m py_compile backend\hivee\settings.py backend\catalog\views\api_views.py`

Essas verificacoes confirmaram que os comentarios adicionados nao introduziram erro sintatico nos arquivos analisados.
