# Dicas de Gamificação — HIVEE

> Estratégias baseadas em pesquisas e cases reais (Uber, Zomato, FoodPanda, Duolingo, GetNinjas) para aumentar retenção, engajamento e recorrência no marketplace de serviços.

---

## Índice

1. [O que já existe na HIVEE (proto-gamificação)](#1-o-que-já-existe-na-hivee-proto-gamificação)
2. [Para o USUÁRIO (cliente contratante)](#2-para-o-usuário-cliente-contratante)
3. [Para o PRESTADOR (profissional)](#3-para-o-prestador-profissional)
4. [Mecânicas transversais (ambos os lados)](#4-mecânicas-transversais-ambos-os-lados)
5. [Erros comuns ao gamificar um marketplace](#5-erros-comuns-ao-gamificar-um-marketplace)
6. [Referências e benchmarks](#6-referências-e-benchmarks)

---

## 1. O que já existe na HIVEE (proto-gamificação)

A HIVEE já tem algumas mecânicas de engajamento que podem ser expandidas:

| Mecânica existente | Descrição | Potencial de evolução |
|---|---|---|
| **Swipe deck ("Para Você")** | Tinder de prestadores com limite diário de 5 | Adicionar streaks, recompensa por usar todos os swipes |
| **Match score + match_reason** | Score 0–99 calculado por rating, distância, preço | Tornar visível em tempo real, explicar como subir |
| **Favoritos** | Coração salva prestador | Transformar em "lista de desejos" com compartilhamento |
| **Profile completeness** | 0–100% (avatar, headline, bio, tags, slots, imagens, lat/lng) | Vincular a badges e benefícios reais |
| **Recomendação personalizada** | Baseada em buscas anteriores (LogEvent) | Adicionar "desafios de descoberta" (ex: "Explore 3 categorias diferentes") |
| **Daily deck limit (5/dia)** | Escassez que gera expectativa | Virar "energia" recarregável com ações |

---

## 2. Para o USUÁRIO (cliente contratante)

### 2.1 Sistema de Níveis do Cliente

Criar níveis progressivos baseados em **contratações concluídas**:

| Nível | Contratações | Benefícios |
|---|---|---|
| 🔵 Novo (Bronze) | 0 | Acesso básico |
| 🟡 Explorador (Prata) | 3 | Badge especial, 1 match extra/dia |
| 🟢 Confiável (Ouro) | 10 | Badge, 3 matches extras/dia, prioridade em orçamentos |
| 🟣 VIP (Diamante) | 25 | Suporte prioritário, tags de "cliente verificado" para prestadores |

**Referência:** FoodPanda Panda League usa 5 tiers (Bronze → Diamond) com benefícios crescentes e renovações trimestrais.

### 2.2 Streaks (Sequências Diárias)

- **Check-in diário:** ao abrir o app, ganha 1 ponto de "energia" (acumulável até 7)
- **Streak de buscas:** 3 dias seguidos buscando → ganha match extra no deck
- **Streak de contratações:** contratar 1x por semana durante 4 semanas → desbloqueia um "impulsionador" gratuito para um prestador favorito
- **Break the streak:** se perder a sequência, oferecer "recuperação" com uma ação simples (ex: favoritar 3 prestadores)

**Referência:** Duolingo aumentou retenção em 34% só com streaks + notificações de alerta.

### 2.3 Desafios & Missões

Missões curtas (diárias/semanais) que transformam navegação passiva em ativa:

| Missão | Recompensa |
|---|---|
| "Busque por 3 categorias diferentes hoje" | +2 swipes no deck |
| "Salve 5 prestadores nos favoritos" | Badge "Curador" + destaque em perfil |
| "Peça 2 orçamentos esta semana" | Desconto de R$ 20 na próxima contratação |
| "Avalie um serviço que você contratou" | Moeda virtual HIVEE |
| "Compartilhe um perfil com um amigo" | 1 dia de swipes ilimitados |

**Referência:** Zomato Food Pass — desafios diários ("Peça um café 3x esta semana") + recompensas progressivas por nível.

### 2.4 Moeda Virtual ("Hivee Coins" ou "Favo")

Moeda não-monetária que o usuário acumula e gasta dentro da plataforma:

**Como ganhar:**
- Completar missões diárias (+5 coins)
- Avaliar serviço (+10 coins)
- Bater streak de 7 dias (+50 coins)
- Indicar amigo (+100 coins)
- Aniversário (+30 coins)

**Como gastar:**
- "Destacar" seu pedido de orçamento na fila do prestador (20 coins)
- Acessar match extra no deck (10 coins cada)
- Comprar badge especial no perfil (50 coins)
- Trocar por vale-desconto real em parceiros (100+ coins)

### 2.5 Badges Visíveis

Badges que aparecem no perfil do usuário ao lado do nome:

- 🏆 **Primeira Contratação**
- 🔥 **Em Chamas** (streak de 7+ dias)
- 🧭 **Explorador** (contratou 5+ categorias diferentes)
- 💎 **Cliente VIP** (nível Diamante)
- 🤝 **Indicador** (trouxe 3+ amigos)
- 📝 **Crítico** (escreveu 10+ avaliações)

**Insight:** badges ativam o motivador psicológico de *status* e *reconhecimento social* — especialmente importantes em marketplaces onde confiança é moeda.

### 2.6 Gamificação do Swipe Deck (expansão)

O swipe deck estilo Tinder já existe, mas pode ser turbinado:

- **Super Like:** 1 por dia (grátis) → envia notificação push para o prestador dizendo que alguém "super curtiu" ele
- **Boost:** usar coins para "acelerar" o deck e ver prestadores antes
- **Resumo semanal:** "Você curtiu 12 prestadores esta semana, seu top categoria foi Reformas 🔨"
- **Modo "Sorte"**: botão que dá um match aleatório surpresa escondendo o perfil até o swipe

---

## 3. Para o PRESTADOR (profissional)

### 3.1 Níveis de Reputação do Prestador

Diferente do rating (0–5), o nível de reputação é **cumulativo e progressivo**:

| Nível | Requisitos | Benefícios |
|---|---|---|
| ⭐ Iniciante | Perfil aprovado | Acesso básico |
| ⭐⭐ Profissional | 5 serviços + 4.5+ rating | Badge "Recomendado" aparece na busca |
| ⭐⭐⭐ Expert | 20 serviços + 4.5+ rating + 80% perfil completo | Prioridade nas recomendações, selo "Top Profissional" |
| ⭐⭐⭐⭐⭐ Mestre | 50 serviços + 4.8+ rating + 100% perfil + fotos | Destaque na home, badge exclusivo "Mestre HIVEE" |

**Referência:** FoodPanda Panda League motiva entregadores a subir de Bronze → Diamond com prêmios trimestrais (motocas, gadgets).

### 3.2 Metas e Conquistas Semanais

| Meta | Recompensa |
|---|---|
| Responder 100% dos contatos em até 1h | +1 posição no ranking de busca da categoria |
| Atualizar fotos do portfólio esta semana | Badge "Portfólio Atualizado" (aparece na busca) |
| Fechar 3 serviços esta semana | 7 dias com destaque no topo da categoria |
| Receber 5 avaliações 5 estrelas no mês | Moedas virtuais (trocáveis por impulsionamento grátis) |

### 3.3 Barra de Progresso do Perfil

Já existe `profile_completeness` no backend (0–100%). Expandir:

- **100% = selo "Perfil Diamante"** que aparece nos resultados de busca
- Sugestões acionáveis: "Adicione 3 fotos para chegar a 80%", "Adicione mais 2 horários disponíveis"
- Ao completar marcos (50%, 80%, 100%), notificação push comemorativa + recompensa

**Segundo a BRAME:** barras de progresso são uma das mecânicas mais eficazes para onboarding porque tornam o progresso visível e criam *commitment escalation*.

### 3.4 Leaderboard por Categoria

Ranking semanal dos prestadores mais bem avaliados em cada categoria:

- **Top 3 da semana** ganham destaque automático na página inicial
- Visível apenas para prestadores (evita competição tóxica pública, mas mantém motivação)
- Critérios: rating + número de serviços + tempo de resposta + completeza do perfil

**Cuidado:** leaderboards podem desmotivar quem está no final. Sempre combinar com metas de progresso pessoal (ex: "Você subiu 2 posições esta semana!").

### 3.5 Selos e Badges para Prestador

Sistema de conquistas de carreira:

- 🛠️ **Mão na Massa** — primeiro serviço concluído
- ⚡ **Relâmpago** — respondeu 10 contatos em <5 min
- 📸 **Fotógrafo** — adicionou 10+ fotos ao portfólio
- 🏅 **Querido** — 50 avaliações 5 estrelas
- 🗺️ **Cobertura Nacional** — atendeu clientes em 5+ estados
- 🔄 **Recorrência** — 10 clientes que contrataram mais de 1 vez

### 3.6 Indicador de "Falta Pouco"

Notificações inteligentes que criam urgência positiva:

- "Faltam 2 serviços para você alcançar o nível Expert! ⭐⭐⭐"
- "Você está a 3 avaliações de 5 estrelas do badge 'Querido' 🏅"
- "Seu perfil está com 70% completo. Complete para aparecer mais nas buscas"

---

## 4. Mecânicas transversais (ambos os lados)

### 4.1 Programa de Indicação (Referral) Gamificado

- **Quem indica:** ganha coins + badge "Indicador" + 1 mês de benefício especial
- **Quem é indicado:** ganha bônus de boas-vindas (ex: 5 swipes extras)
- **Ranking de indicadores:** leaderboard privado "Os mais conectados" com prêmio mensal para o top 5

**Referência:** Uber cresce 60% YoY no Uber One com cross-service referrals; marketplace guide mostra 15–30% lift em aquisição com referral gamificado.

### 4.2 Ciclo de Feedback Gamificado

Transformar a avaliação pós-serviço em um momento recompensador:

- **Prompt interativo:** "Como foi o serviço?" com sliders/emojis em vez de estrelas frias
- **Avaliação dupla:** cliente avalia prestador E prestador avalia cliente
- **Recompensa por avaliar:** ambos ganham coins ao completar a avaliação
- **Badge "Cliente Nota 10":** para clientes que sempre avaliam com educação

### 4.3 Calendário de Eventos Sazonais

Desafios temáticos ao longo do ano que movimentam ambos os lados:

| Evento | Mecânica |
|---|---|
| **Janeiro: Reforma Total** | Prestadores de reforma ganham destaque; clientes ganham coins por pedir orçamento |
| **Abril: Limpeza & Organização** | Desafio de agendar 2 serviços de limpeza no mês → badge + desconto |
| **Junho: HIVEE Fest** | "Aniversário da plataforma" — todos os níveis viram rewards em dobro |
| **Outubro: Mês do Profissional** | Clientes podem enviar "gorjeta virtual" (coins) para prestadores favoritos |

### 4.4 Feedbacks em Tempo Real com Confetes

Micro-animações e celebrações para ações importantes:

- Ao completar o perfil 100% 🎉
- Ao subir de nível 🚀
- Ao bater streak de 7 dias 🔥
- Ao fechar o primeiro serviço 🏆
- Ao ser indicado por um amigo 🤝

**Por que funciona:** feedback instantâneo ativa o circuito de recompensa do cérebro (dopamina), criando associação positiva com a plataforma.

### 4.5 Personalização via IA (2026+)

Tendência forte do mercado: usar dados comportamentais para adaptar desafios:

- Cliente que só contrata eletricista → recebe missão "Explore outras categorias"
- Prestador com fotos fracas → missão "Tire 3 novas fotos do seu trabalho"
- Usuário que não abre há 7 dias → notificação "Você perdeu seu streak 💔, mas pode recuperar com 1 busca"

---

## 5. Erros comuns ao gamificar um marketplace

| Erro | Por que acontece | Como evitar |
|---|---|---|
| **Sistema muito complexo** | Tentar implementar tudo de uma vez | Começar com 2–3 mecânicas (ex: níveis + streaks) e iterar |
| **Recompensas irrelevantes** | Não conectar com o que o usuário realmente valoriza | Pesquisar com usuários reais; testar A/B |
| **Competição tóxica** | Leaderboard público sem progresso pessoal | Sempre mostrar progresso individual + ranking opcional |
| **Foco só no curto prazo** | Desafios diários sem jornada de longo prazo | Combinar daily loops (streaks) com aspiration loops (níveis) |
| **Ignorar o prestador** | Gamificar só para o lado do cliente | Ambos os lados precisam de engajamento (two-sided marketplace) |
| **Sem medição** | Não trackear impacto real (retenção D7/D30, LTV) | Definir KPIs antes de implementar; medir cohorts |

**Fonte:** insights compilados de BRAME, Marketplace Guide, Minders, Mind Inventory.

---

## 6. Referências e benchmarks

### Cases internacionais

| Empresa | Mecânica | Resultado |
|---|---|---|
| **Uber** | Cross-service ecosystem (rides + delivery) + Uber One tiers | 35% maior retenção em multi-serviço; 60% YoY Uber One |
| **Duolingo** | Streaks + notificações + ranking de ligas | 34% aumento em retenção |
| **Zomato** | Food Pass: níveis + desafios diários + moeda virtual | Maior frequência de pedidos e LTV |
| **FoodPanda** | Panda League: 5 tiers + prêmios trimestrais + Rider Shop | Redução de churn de entregadores |
| **Starbucks** | Stars + challenges + birthday reward | 30–50% maior frequência de membros vs não-membros |

### Estudos

- McKinsey / Forrester: clientes em programas de fidelidade gamificados têm **30–50% maior frequência de compra**
- Gartner: gamificação pode elevar engajamento em **até 60%**
- Snipp: fidelidade +22%, engajamento +47% com gamificação bem implementada
- Adjust (2023): retenção cai de 20% para <10% no primeiro mês sem gamificação

### Benchmark direto (marketplaces de serviço BR)

- **GetNinjas:** lead pago por orçamento — sem gamificação significativa (oportunidade!)
- **99Freelas / Workana:** sistema de níveis por projetos concluídos + testes de habilidade
- **MadeiraMadeira / Via (Casas Bahia):** "Missão Via Performance" — game educativo para lojistas com termômetro de energia e prêmios

> A HIVEE tem a oportunidade de ser pioneira em gamificação profunda em marketplace de serviços no Brasil. O swipe deck e o match score já são um excelente ponto de partida.
