# HIVEE — REGRAS E STATUS (LER SEMPRE ANTES DE MEXER)

> Este arquivo existe porque eu (assistente) perdi requisitos por causa da janela de
> contexto. **Reler no início de cada rodada** e **atualizar o status** a cada mudança.

## REGRAS DURAS (NUNCA QUEBRAR)
1. **Proibido `—` (travessão/em-dash).** Usar vírgula, ponto ou dois-pontos.
2. **Proibido "eyebrow"/títulos pequenos** (ex.: "RECOMENDADO PRA VOCÊ") e o **ícone Sparkles (estrelinha)**.
3. **Proibido card/pílula preguiçoso com círculo/borda ao redor** de rótulos. Texto solto > chip. (Ex.: "Role para descobrir" = SÓ texto.)
4. **Usar os componentes reais** das referências (`componentsui.md`, `components.md`) via registry 21st.dev (`https://21st.dev/r/<autor>/<nome>`). Nunca recriar do zero.
5. **Todo clique = tela real** (React Router). Nada de SPA de uma página só.
6. **Tipografia: UMA fonte só = Inter** (a do começo/cinematic, que o usuário amou). Smooth/arredondada. NUNCA Space Grotesk "quadrada".
7. **Fundo ÚNICO: preto contínuo**, sem emendas entre seções, **sem fundo colorido**. As "luzes" ficam **nos elementos** (glass com brilho), não no fundo.
8. **Liquid glass de verdade**, visível, em VÁRIOS lugares.
9. **Animações smooth e performáticas, SEM lag.** Nunca animar `blur`/`backdrop-filter`; só `transform`/`opacity`.
10. **Sem espaçamento gigante** entre seções. Site COESO, não abas desconexas.
11. **Cinematic curta** (scroll rápido pra passar). A **primeira tela** (só texto, minimalista) é a referência boa, PRESERVAR.
12. **"Role para descobrir"**: só texto (sem chip), presente até o fim da cinematic, cor legível sobre o card.
13. **Celular do hero INTERATIVO de verdade**: busca funcional, botões funcionam (mesma busca do site). NÃO é hover.
14. **Backend com lógica real**: cidade filtra de verdade, cadastro/auth, dados no banco.
15. Stack/portas: frontend Vite **:5200**, backend Django **:8000** (proxy /api). NÃO matar dev servers de outros projetos do usuário (CBLOL_LIFE, Documents\HIVEE).

## DIREÇÃO VISUAL
- Cores: preto (#09090b) + dourado (#facc15 / #eab308 / #ca8a04).
- Fonte: **Inter** (única).
- Glass: frosted translúcido, borda especular brilhante, brilho suave no elemento.
- Ferramenta de verificação: screenshots via `frontend/_shot.mjs` (Playwright + Edge). SEMPRE olhar antes de dizer que terminou.

## STATUS
### Feito (verificado por screenshot)
- [x] Backend Django+DRF: cidade filtra (city=), auth (register/login/me), /cities, criar prestador, 180 seed.
- [x] App de páginas reais (Home, /buscar, /prestador/:slug, /recomendados, /entrar, /cadastrar, /sou-prestador).
- [x] Componentes reais do 21st.dev integrados (cinematic, minimalist-hero, nav-header, section-mockup, stacked-cards).
- [x] Removidos eyebrows + Sparkles. Em-dash removido das copies.
- [x] Dropdown de cidade custom (GlassSelect) opaco no lugar do <select> nativo.
- [x] **Cinematic restaurada** (fonte Inter de volta, visual original). Scroll curto (end +=750). Cue "Role para descobrir" = SÓ texto, dourado, persiste até o fim.
- [x] **Liquid glass real** (bevel interno brilhante, baseado nos refs do 21st.dev) no header E em todos os cards. Glass visível.
- [x] Ícones Phosphor duotone (premium) restaurados nas categorias.
- [x] Hover 3D nos cards (Tilt3D, baseado no aceternity 3d-card).
- [x] Espaçamento reduzido + removidos ícones sociais "perdidos" + header/footer vazios do hero. Fluxo coeso (hero->categorias).
- [x] Fundo único preto (sem bg-background opaco nas seções; mesh = preto + luz dourada fraca).

- [x] **Celular do hero INTERATIVO** (PhoneApp): input de busca + botão Buscar + chips de categoria que navegam pra /buscar de verdade.
- [x] **Liquid glass real** com refração (filtro SVG `#glass-distortion` do suraj-xd) + bevel luminoso + luz dourada por trás (mesh) pro vidro difundir.

### Lista "problemas" (do arquivo do usuário) — status
- [x] 1. "Role para descobrir" vai até o fim da cinematic (só fade no final).
- [x] 2. Seção "Do problema ao profissional certo" removida -> virou "Como funciona em 3 passos".
- [x] 3. Dropdown de cidades não corta mais (portal fixed no body, acima de tudo). [feito junto c/ usuário]
- [x] 4. Busca só mostra prestadores depois de escolher a cidade ("Escolha sua cidade"). [feito junto c/ usuário]
- [x] 5. Menu = Início / Buscar / Meu Perfil. Página /minha-conta difere prestador (vê perfil público) x cliente (vira profissional).
- [x] 6. Lag: cards sem backdrop-filter (só chrome tem), blur removido da cinematic. [usuário otimizou]
- [x] Vazio gigante da cinematic resolvido (conteúdo fica visível, sem cauda preta).
- [x] Glass luminoso: bevel claro + luz dourada contida por card (mais perto da ref).

### PENDENTE
- [ ] Repaginação total de Categorias (já melhor; não é redesenho do zero).
- [ ] Comparar glass lado a lado com a ref e calibrar brilho se preciso.
- [ ] Revisão visual final de todas as telas ao vivo.
