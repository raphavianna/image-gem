# Modalidades

Etapa **E3**. Cada modalidade é um **renderizador sobre o schema canônico** definido na E2. A doutrina e o checklist são compartilhados; o que muda é onde a proporção e a resolução vão, como as referências entram, e qual é o envelope da chamada.

## Panorama

| # | Nome | Destino | Refs entram como | Proporção e resolução | Modelo alvo |
|---|---|---|---|---|---|
| 1 | Interface Gemini | `gemini.google.com` (chat) | verbalizadas na prosa | verbalizadas no texto | `gemini-3-pro-image` |
| 2 | Interface Higgsfield | painel `cloud.higgsfield.ai` | upload no painel | controles do painel; **sem `resolution`** | `/nano-banana` (variante `[L7]`) |
| 3 | Conector Higgsfield | `POST /nano-banana` | `input_images[].image_url` (até 8) | `aspect_ratio` no payload; **sem `resolution`** | `/nano-banana` — variante **assumida** Pro, ver `[L7]` |
| 4 | API Gemini | `google-genai` SDK | itens da lista `contents` (até 14) | `ImageConfig.aspect_ratio` e `image_size` | `gemini-3-pro-image` |

## O que é compartilhado, o que é próprio

**Compartilhado** — as quatro modalidades leem o mesmo schema, aplicam as mesmas regras de coerência (C1–C14), executam o mesmo checklist de emissão (itens 1–8) e emitem o mesmo corpo textual em blocos rotulados.

**Próprio de cada modalidade** — o envelope. A modalidade 1 devolve texto puro; a 2 devolve texto e um mapeamento de controles; a 3 devolve um payload REST assinado; a 4 devolve `contents` + `ImageConfig` prontos para `client.models.generate_content(...)`.

**Base compartilhada em código:** `schemas/validador.py` implementa as quatro funções `renderiza_modalidade_N`. Todas chamam a mesma `renderiza_modalidade_1(spec, incluir_output_no_texto=...)` para o corpo, e diferem apenas no envelope. Isso é o que impede as modalidades de divergirem em rigor.

## Regras que se apagam em regime `edit`

Duas regras da doutrina não se aplicam ao regime `edit`, e essa exceção está codificada em `x-imagegem.regras_de_coerencia` do schema:

- **`C5` (catchlight vs modificador)** — a luz do sujeito já está gravada no quadro de origem. Redeclarar seria contradizer a instrução de preservação. Basta a cauda proibir "second light direction on the face", como no exemplo âncora.
- **Item 1 do checklist (fontes completas)** — pela mesma razão. A gramática de edição substitui `LIGHTING` por `RECONCILE LIGHT`, que descreve como o novo ambiente **justifica** a luz existente, sem redeclarar.

Isto é intencional: se a doutrina se aplicasse ao pé da letra à edição, teríamos que redeclarar toda a cadeia física e o modelo trataria isso como pedido de re-renderizar o sujeito — que é o modo de falha nomeado por `[BLOG]`.

## Escolha de modalidade — quando usar cada uma

- **Modalidade 1** — exploração rápida, iteração conversacional, um único usuário.
- **Modalidade 2** — o usuário já opera no painel Higgsfield e quer manter o fluxo.
- **Modalidade 3** — produção em escala pelo caminho Higgsfield: batch, cliente próprio, webhook.
- **Modalidade 4** — produção pelo caminho Gemini nativo: controle fino de `image_size` (inclusive 4K), `include_thoughts` para diagnóstico, chat multi-turno com *thought signatures* preservadas, mais 14 vs 8 referências.

**Regra prática:** se o prompt exige 4K auditável, use 4. Se quer usar 8+ referências para composição, use 4. Para tudo o mais, 3 ou 2 servem — a escolha entre elas é operacional, não de qualidade.

## Escopo desta etapa

Uma página por modalidade neste diretório:

- `1-interface-gemini.md`
- `2-interface-higgsfield.md`
- `3-conector-higgsfield.md`
- `4-api-gemini.md`

Cada página traz o **renderizador do schema canônico** para aquele destino e um **exemplo completo ponta a ponta que passa o checklist**. Os exemplos são gerados a partir das instâncias em `schemas/exemplos/` — nenhuma prosa fabricada à mão.
