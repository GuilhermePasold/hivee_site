# Exercicio Django MTV - HIVEE

## Parte 1 - O Retrato

INSERIR AQUI O PRINT SCREEN DA BARRA LATERAL DO VS CODE COM A ARVORE EXPANDIDA.

## Parte 2 - O Porque

### Modularizacao das views

- O arquivo `views.py` unico foi removido porque concentraria responsabilidades demais em um modulo so.
- `views/provider_views.py` cuida da listagem e do detalhe dos prestadores.
- `views/auth_views.py` cuida do cadastro, login e logout da camada MTV.
- `views/perfil_views.py` cuida da edicao de perfil e da delecao logica do cliente.
- `views/api_views.py` preserva a API REST existente em `/api/`.
- Essa divisao melhora manutencao, leitura, testes e crescimento futuro do projeto.

### Padrao MTV

- Models ficam em `catalog/models.py` e representam regras e estrutura do banco: `Category`, `Provider`, `ProviderImage` e `Cliente`.
- Templates ficam em `base/templates` e `catalog/templates/catalog`, representando a interface HTML renderizada pelo Django.
- Views ficam em `catalog/views/` e conectam requisicoes, models, formularios e templates.
- Forms ficam em `catalog/forms.py` e validam a entrada do usuario antes de salvar no banco.

### Static vs templates

- `templates/` guarda HTML renderizado pelo Django, com variaveis, blocos, extends, includes, forms e CSRF.
- `static/` guarda assets publicos como CSS, JS, imagens fixas, icones e scripts.
- Templates mudam conforme contexto e dados do banco; static normalmente e arquivo publico estatico.

### Rotas

- `hivee/urls.py` e a porta de entrada global do projeto.
- `catalog/urls.py` concentra as rotas do app `catalog`.
- Separar URLs do projeto e URLs do app evita um arquivo principal gigante.
- Essa separacao facilita manutencao, reuso do app e organizacao por responsabilidade.
- A API e a camada MTV coexistem sem misturar tudo no `urls.py` global.
