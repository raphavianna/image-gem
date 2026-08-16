# Aprendizados

Log vivo do loop de retroalimentação (E6). Cada linha responde três perguntas:

1. **O que se aprendeu** — em uma frase.
2. **O que provou** — o registro em `runs/`, o commit ou o arquivo que carrega a evidência. Aprendizado sem prova rastreável não entra.
3. **Onde subiu** — doutrina, template, checklist, cliente, docs. Aprendizado que ficou em conversa é bug operacional.

O formato é apêndice em ordem cronológica reversa, seções por origem (fonte, teste automático, teste empírico, correção de assumption). Nada deste arquivo é escrito por convicção; tudo é apoiado por artefato versionado.

---

## 2026-08-16 · E5 · registro-âncora preenchido

- **O que se aprendeu.** O loop precisa começar com um registro exemplar preenchido para que o formato do metadata seja o padrão de referência dos demais.
- **O que provou.** `runs/EXEMPLO-e6-registro-ancora/metadata.json`, versionado — spec_hash, checklist_signature, defaults_applied_count, review com signals e follow-ups.
- **Onde subiu.** Este arquivo. `docs/06-loop.md` documenta o formato. `schemas/run-record.json` valida qualquer novo metadata.

---

## 2026-08-16 · E4 · faixa de densidade "ancorada em referência"

- **O que se aprendeu.** Composição multi-referência e consistência de personagem rendem legitimamente ~450 palavras — muitos campos apontam para a referência em vez de redeclarar. Cair na faixa 500–650 de "geração com pessoa" reprova prompt fisicamente correto.
- **O que provou.** Ao instanciar `composicao-multi-referencia` e `consistencia-personagem` na E4, `imagegem validate` reprovou os dois no item 8 com corpos de 456 e 453 palavras. Commit `62fd37d`.
- **Onde subiu.** `schemas/prompt-spec.json` `x-imagegem.orcamento_densidade.faixas[]` ganhou entrada `quando: character.references_urls não vazio` (350–560) com prioridade sobre regime. `check.faixa_de_densidade` consulta essa condição primeiro. Documentado em `docs/04-templates.md` seção 3.

## 2026-08-16 · E4 · campos de referência declarados no schema

- **O que se aprendeu.** Os renderizadores das modalidades 3 e 4 já liam `character.references_urls` e `edit.source_urls` desde a E3, mas os campos não estavam declarados no schema. Passou enquanto os exemplos eram só descrição; templates de composição os exigem.
- **O que provou.** `resolve()` do template `composicao-multi-referencia` gerava spec com referências que caíam fora do schema. Commit `62fd37d`.
- **Onde subiu.** `schemas/prompt-spec.json` — dois campos opcionais declarados.

---

## 2026-08-16 · E3 · variante do `/nano-banana` Higgsfield

- **O que se aprendeu.** O endpoint `POST /nano-banana` da Higgsfield não distingue Nano Banana Pro de Nano Banana 2 na URL nem em parâmetro documentado. A promessa das modalidades 2 e 3 de que o modelo alvo é o Pro depende da hipótese de que a Higgsfield roteia para o Pro por padrão.
- **O que provou.** Extração literal do `openapi.json` em `docs/00-fontes/07-fonte-primaria-higgsfield.md`. Único `/nano-banana`, nenhum path `/pro` ou `/flash`.
- **Onde subiu.** L7 aberta em `docs/00-fontes/05-divergencias-e-lacunas.md`. Só resolve empiricamente com credencial — escopo da E7.

## 2026-08-16 · E3 · credencial Higgsfield não é `refresh_token`

- **O que se aprendeu.** É par `API key ID + secret`, enviado como `Authorization: Key ID:SECRET`. O ESTADO listava `refresh_token` por assumption; a documentação primeiro-parte da Higgsfield desfez.
- **O que provou.** `docs.higgsfield.ai/docs/authentication.md`, literal: *"Authorization: Key YOUR_KEY_ID:YOUR_KEY_SECRET"*. Extraído em `docs/00-fontes/07-fonte-primaria-higgsfield.md`.
- **Onde subiu.** `docs/ESTADO.md` linha de pendências externas atualizada. `src/imagegem/clients/higgsfield.py` implementa o cabeçalho correto. Commit `4f95674`.

## 2026-08-16 · E3 · `/nano-banana` não expõe `resolution`

- **O que se aprendeu.** A Higgsfield abstrai a resolução — não há campo. A decisão travada de "2K como default do sistema" só é *enforceable* na modalidade 4. Modalidade 3 herda o que a plataforma decidir; 4K auditável só pela modalidade 4.
- **O que provou.** `openapi.json` do endpoint `/nano-banana` — `properties` não contém `resolution`, enquanto `/higgsfield-ai/soul/standard` expõe `resolution: [2K, 4K]`.
- **Onde subiu.** `docs/03-modalidades/2-interface-higgsfield.md` e `.../3-conector-higgsfield.md` documentam a ausência. `render.renderiza_modalidade_2` inclui nota de resolução nos controles.

## 2026-08-16 · E3 · regras que se apagam em `edit`

- **O que se aprendeu.** `C5` (catchlight vs modificador) e o item 1 do checklist (fontes completas) não se aplicam à edição: a gramática de edição substitui `LIGHTING` por `RECONCILE LIGHT`, e redeclarar contradiz a instrução de preservação.
- **O que provou.** O primeiro teste do exemplo 3 de edição reprovou em C5 e item 1 com um spec fisicamente correto. Commit `4f95674`.
- **Onde subiu.** `schemas/prompt-spec.json` marcou as duas regras como `aplica_quando: scene.regime != edit`. `check.aplica` reconhece as duas novas condições. Documentado em `docs/03-modalidades/README.md`.

---

## 2026-08-16 · E2 · orçamento de densidade por regime

- **O que se aprendeu.** A faixa única 350–500 do prompt-mestre reprova dois dos três exemplos âncora. Os três regimes carregam conjuntos diferentes de blocos obrigatórios, então uma banda única não cabe.
- **O que provou.** Medição direta dos três exemplos: 597, 290 e 410 palavras. O "~450" atribuído ao exemplo 1 no prompt-mestre erra por ~150 palavras.
- **Onde subiu.** Faixa por regime travada no `ESTADO.md` decisões travadas. `schemas/prompt-spec.json` `x-imagegem.orcamento_densidade.faixas[]` com três entradas + a quarta ancorada em referência acrescida na E4. Documentado em `docs/02-gramatica-do-prompt.md` seção 3. Commit `ea52f57`.

## 2026-08-16 · E2 · defeito de duplicação de reflexo

- **O que se aprendeu.** Repetir `reflects` dentro de cada material e de novo consolidado no bloco `REFLECTION GEOMETRY` inflava o corpo em 44%. Teste de volta pegou.
- **O que provou.** Primeira renderização do exemplo 4 rendeu 583 palavras contra 410 do original.
- **Onde subiu.** Schema separou `materials[].specular_response` (como responde) de `materials[].reflects` (o que reflete), com o segundo consolidado em `REFLECTION GEOMETRY` na renderização. `docs/02-gramatica-do-prompt.md` seção 8.

## 2026-08-16 · E2 · flag preto tratado como fonte de luz

- **O que se aprendeu.** Flag subtrativo estava em `lighting.sources[]` no exemplo 4, com temperatura de cor declarada — errado, flag absorve luz, não emite. Teste de volta pegou por overhead de palavras no bloco `LIGHTING`.
- **O que provou.** Bloco `LIGHTING` do exemplo 4 rendia 148 palavras contra 81 do original; ao remover o flag da lista de fontes, caiu para 144 (delta remanescente era a conformidade com o item 1 do checklist).
- **Onde subiu.** Instância corrigida. Flag ficou apenas no campo `background_treatment`. Commit `ea52f57`.

---

## 2026-08-16 · E1 · teto de referências de identidade — 5, não 6

- **O que se aprendeu.** A documentação primeiro-parte do Google decompõe o teto de 14 do `gemini-3-pro-image` em três orçamentos por papel: **5 personagens, 6 objetos, 3 estilo**. O ESTADO travava 6 para identidade por leitura do cookbook, que descrevia como "alta fidelidade" genérica — na verdade era o orçamento de objetos.
- **O que provou.** Tabela literal em `docs/00-fontes/06-fonte-primaria-ai-google-dev.md` seção 2. Também confirmado na prosa de *Limitations*: *"gemini-3-pro-image supports 5 images with high fidelity"*.
- **Onde subiu.** Decisão travada no `ESTADO.md` corrigida para 5, marcada com data e aprovação do autor. `schemas/prompt-spec.json` `character.identity_reference_count.maximum = 5`. C11 verifica o teto. Documentado em `docs/01-doutrina-hiper-realismo.md` seção 5 e em `docs/00-fontes/05-divergencias-e-lacunas.md` D2. Commit `d0a4136`.

## 2026-08-16 · E1 · preço por imagem — lacuna crítica resolvida

- **O que se aprendeu.** Nano Banana Pro custa `$0,134` por imagem 1K/2K e `$0,24` por imagem 4K. 1K e 2K consomem os mesmos 1120 tokens, então **custam o mesmo** — pedir 1K é pagar 2K e receber metade.
- **O que provou.** Página primária de preços em `ai.google.dev/gemini-api/docs/pricing`, extraída em `docs/00-fontes/06-fonte-primaria-ai-google-dev.md` seção 3.
- **Onde subiu.** Default do sistema fixado em 2K. Documentado no `ESTADO.md` decisões travadas. `docs/03-modalidades/4-api-gemini.md` seção "Resolução". Batch e Flex documentados como caminho para lote (metade do custo). L1 fechada em `docs/00-fontes/05-divergencias-e-lacunas.md`. Commit `310c503`.

## 2026-08-16 · E1 · valor de terceiro coincide com fato — recusa segue correta

- **O que se aprendeu.** Durante a E0, o valor `$0,134` circulou num resultado de busca de terceiro e foi **recusado** por não ser primeiro-parte. Quando a fonte primária abriu na E1, o valor estava correto. O acerto do palpite não converte um terceiro em autoridade.
- **O que provou.** Registro preservado em `docs/00-fontes/05-divergencias-e-lacunas.md` L1: *"o palpite estava correto. A recusa continua tendo sido a decisão certa: acertar por acaso não converte um terceiro em autoridade."*
- **Onde subiu.** Nada muda operacionalmente — a política de "recusar palpite mesmo quando batia por acaso" fica registrada como precedente para futuras situações análogas.

---

## Regra operacional

Herdada pela Skill, pelo pipeline e pelo autor:

1. **Toda geração que recebe avaliação vira registro em `runs/`.** `imagegem submit` grava sem opção de opt-out — só o autor decide se o registro é retido além do padrão de 30 dias que a E7 pode fixar.
2. **Toda correção que aparece duas vezes vira issue de doutrina, template ou checklist.** `imagegem runs --pending` lista follow-ups não promovidos. Dois follow-ups com o mesmo `target` são um sinal para agir; três, um bug de processo.
3. **Nenhum aprendizado morre em conversa.** Se a correção fica só no chat, ela vai regredir. O caminho é `imagegem review` → follow-up → commit que absorve → `promoted_to` preenchido → linha neste arquivo.
4. **Aprendizado sem prova rastreável não entra neste arquivo.** Cada linha aponta para um registro em `runs/`, um commit, ou um arquivo versionado que carrega a evidência.

Ver `docs/06-loop.md` para o fluxo completo e `.claude/skills/imagegem/SKILL.md` para o resumo herdado pela Skill.
