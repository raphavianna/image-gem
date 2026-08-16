# Divergências entre fontes e lacunas

Hierarquia aplicada, conforme o prompt-mestre: `[SDK]` é autoridade para nomes, tipos e valores aceitos de parâmetro; documentação primeiro-parte é autoridade para capacidades, limites e preços; cookbook e notebooks são autoridade apenas para padrões de uso.

> **Revisão de 2026-08-16, antes da E1.** A validação de rede de abertura de sessão mostrou `ai.google.dev` respondendo `200` — o host estava bloqueado durante a E0. A fonte primária foi lida e está extraída em `06-fonte-primaria-ai-google-dev.md`, com etiqueta `[GAI]`. Como `[GAI]` é documentação primeiro-parte, ela **supera `[CB]` e `[BLOG]` em capacidades, limites e preços**. As divergências D1 e D2 e as lacunas L1, L2, L4 e L6 foram revisadas abaixo. Itens marcados **[RESOLVIDA]** ficam registrados em vez de apagados, para que o histórico da decisão continue auditável.

## Divergências

### D1 — Proporções `4:5` e `5:4` ausentes na docstring do SDK — **[RESOLVIDA]**

**Resolução final `[GAI]`.** A tabela de proporções do `gemini-3-pro-image` na documentação primeiro-parte lista `4:5` com dimensões **928×1152 em 1K**, 1856×2304 em 2K e 3712×4608 em 4K. Idêntico ao que `[CB]` afirmava. A docstring do `[SDK]` está desatualizada, como a análise abaixo já concluíra. O exemplo âncora de calibração, que usa `4:5`, está validado por fonte primária. Nenhuma confirmação empírica adicional é necessária.

Registro da análise original, mantido:

| Fonte | Afirma |
|---|---|
| `[SDK]` | `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"9:16"`, `"16:9"`, `"21:9"` — **oito** valores |
| `[CB]` | Tabela com **dez**, incluindo `4:5` e `5:4`, com dimensões exatas em pixel nas quatro resoluções |
| `[BLOG]` | Lista **dez** para o NB Pro, incluindo `4:5` e `5:4` |

**Resolução:** `4:5` e `5:4` são tratados como suportados. O campo `aspect_ratio` é `Optional[str]` no `[SDK]` — texto livre, sem enum e sem validação em tempo de execução —, portanto a docstring é prosa descritiva, não contrato executável. Duas fontes primeiro-parte independentes listam os dez valores, e `[CB]` fornece dimensões em pixel para `4:5` nas quatro resoluções, o que seria implausível para uma proporção inexistente. A docstring do SDK está desatualizada.

**Consequência:** o exemplo âncora de calibração usa `4:5` e permanece válido. O renderizador de E3 aceita os dez valores.

**Confirmação pendente:** uma chamada real com `aspect_ratio="4:5"`, verificando a dimensão retornada contra 928×1152 em 1K. Entra na bateria de validação assim que houver `GEMINI_API_KEY`.

### D2 — Limite de imagens de referência — **[RESOLVIDA, com correção de decisão travada]**

| Fonte | Afirma |
|---|---|
| `[CB]` | 3 no Flash; 14 no Pro; **6 em alta fidelidade** |
| `[BLOG]` | "até 14" para ambos os modelos, sem menção ao corte de fidelidade nem ao limite de 3 |
| **`[GAI]`** | **Três orçamentos por papel no `gemini-3-pro-image`: 6 objetos em alta fidelidade, 5 personagens para consistência, 3 referências de estilo — somando os 14** |

**Resolução final.** Nenhuma das duas fontes anteriores estava errada; as duas estavam incompletas. O "14" nunca foi um teto único e indiferenciado, e o "6" nunca foi o número de personagens. A documentação primeiro-parte decompõe o teto em três orçamentos por papel, e eles somam exatamente 14 (6 + 5 + 3). O `[CB]` viu o orçamento de objetos e o descreveu como "alta fidelidade" genérica.

> **Correção de decisão travada.** O ESTADO registrava, entre as decisões não reabríveis: *"teto de 6 imagens de referência para qualquer template que dependa de identidade preservada — não 14"*. A direção estava certa (o teto útil é bem abaixo de 14), o número estava errado. **Para identidade preservada o teto é 5.** O 6 continua válido, mas como orçamento de objetos em alta fidelidade.
>
> A correção **estreita** a regra anterior, então nenhum trabalho a jusante ficou construído sobre suposição mais permissiva. **Aprovada pelo autor no gate de E1, em 2026-08-16.** Aplicada em `docs/01-doutrina-hiper-realismo.md`, seção 5, codificada como validação no schema da E2, e herdada pelos templates da E4.

A prosa de *Limitations* `[GAI]` diz *"gemini-3-pro-image supports 5 images with high fidelity"* onde a tabela diz 6 objetos — leitura conciliadora: o número da prosa é o de personagens, que é o caso que a frase seguinte discute.

**Confirmação pendente:** comparação empírica de preservação de identidade com 5 e com 8 referências, registrada em `runs/`. Deixou de ser necessária para decidir e virou validação de qualidade.

### D3 — `thinking_level` no Nano Banana Pro

O `[CB]` descreve thinking como capacidade de ambos os modelos Gemini 3, mas anota o parâmetro `thinking_level` no código como *"Only for Nano-Banana 2"*, e escreve na prosa: *"**Nano-Banana 2** also introduces **Thinking Levels**"*.

**Resolução:** leitura literal — o NB Pro **pensa**, mas o controle explícito do nível de raciocínio via `thinking_level` foi introduzido pelo NB 2. Isso significa que, no `gemini-3-pro-image`, `include_thoughts=True` deve funcionar para inspeção, enquanto `thinking_level` pode ser ignorado ou rejeitado.

**Consequência:** o cliente de E5 não deve depender de `thinking_level` no caminho do NB Pro. Marcado `[NÃO VERIFICADO]` até teste.

## Lacunas — `[NÃO VERIFICADO]`

### L1 — Preço por imagem — **[RESOLVIDA]**

**Resolução `[GAI]`**, `ai.google.dev/gemini-api/docs/pricing`, `gemini-3-pro-image`, camada Standard:

| Item | Valor |
|---|---|
| Imagem de saída 1K **ou** 2K | **`$0,134`** — 1120 tokens a `$120`/1M |
| Imagem de saída 4K | **`$0,24`** — 2000 tokens |
| Imagem de entrada | `$0,0011` — 560 tokens |
| Texto e thinking, saída | `$12,00`/1M |
| Batch e Flex | metade: `$0,067` (1K/2K) e `$0,12` (4K) |

Três consequências operacionais, detalhadas em `06-fonte-primaria-ai-google-dev.md`: **1K e 2K custam o mesmo**, então o default do sistema é 2K; 4K custa 79% a mais e é reservado a entrega ampliada; Batch corta o custo pela metade e é o caminho para geração de variantes em lote na E4 e na E7.

**Nota de disciplina, deliberadamente preservada.** O texto original desta lacuna registrava que o valor `$0,134` havia aparecido num resultado de busca de terceiro e fora **recusado** por não ser primeiro-parte. O palpite estava correto. A recusa continua tendo sido a decisão certa: acertar por acaso não converte um terceiro em autoridade, e o custo de errar sobre preço é maior que o de declarar uma lacuna. Registro original abaixo.

---

Nenhum valor de preço foi obtido de fonte primeiro-parte. Todas as páginas de preço estão em `ai.google.dev/gemini-api/docs/pricing` e `docs.cloud.google.com`, ambas bloqueadas no egress. O `[CB]` apenas remete a elas por link.

O prompt-mestre listava a documentação em `cloud.google.com` como autoridade para preços; na prática, todo caminho `cloud.google.com/vertex-ai/...` responde 301 para `docs.cloud.google.com`, que é bloqueado. **A autoridade prevista para preços não existe nesta sessão.**

Um valor de US$ 0,134 por imagem circulou em resultado de busca de terceiro durante a coleta. **Não é fonte primeiro-parte e não foi adotado.** Está registrado aqui apenas para que ninguém o reintroduza depois julgando ser dado verificado.

O que se sabe com base primeiro-parte:
- Geração de imagem exige faturamento ativo; é pay-as-you-go `[CB]`.
- Tokens dependem de modelo e resolução, **não** da proporção `[CB]`.
- 4K custa mais que 1K `[CB]`: *"4K images are more expensive so only do it when needed"*.
- Tokens de pensamento são cobrados como tokens de saída; imagens dentro dos pensamentos não são `[CB]`.

**O que resolveria:** liberar `ai.google.dev` ou `docs.cloud.google.com` no egress; ou o usuário colar a tabela de preços; ou uma chamada real com leitura de `usage_metadata`, que dá contagem de tokens — não preço, mas a metade que falta para calcular.

### L2 — Marca d'água não configurável nos modelos Gemini de imagem — **[RESOLVIDA em substância]**

**Resolução `[GAI]`.** Afirmação literal, repetida duas vezes na página de geração de imagem — no cabeçalho dos modelos e na lista de limitações:

> All generated images include a SynthID watermark.

Afirmação universal, sem cláusula de configuração, numa página que documenta exaustivamente os parâmetros configuráveis. Somada à ausência de campo de marca d'água em `ImageConfig` `[SDK]`, a leitura de que a marca é automática deixa de ser inferência e passa a ter citação direta.

**Resíduo:** nenhuma fonte afirma nem nega explicitamente a **impossibilidade formal de desativação**. Impacto prático nulo — não há parâmetro para tentar. Registro original abaixo.

---

`add_watermark` existe no `[SDK]` apenas no caminho Imagen, não em `ImageConfig`. O `[BLOG]` lista C2PA + SynthID como característica dos modelos Nano Banana. A conclusão de que a marca d'água é **automática e não desativável** é inferência coerente com as duas fontes, mas não há citação que a afirme.

### L3 — Comportamento de `person_generation` na Gemini API

Os três valores estão no `[SDK]` sem marcação de indisponibilidade, logo valem para a Gemini API. Não foi encontrada documentação de qual é o **default** quando o campo é omitido, nem do comportamento exato de `ALLOW_ADULT` (bloqueio duro, recusa suave, ou filtragem posterior).

Importa porque a política de conteúdo do repositório depende disso. **O que resolveria:** a documentação bloqueada, ou teste empírico.

### L4 — Guia de prompts de `ai.google.dev` não lido diretamente — **[RESOLVIDA]**

**Resolução `[GAI]`.** A página foi lida na íntegra. O guia de prompts, as seis boas práticas, os templates (fotorrealista, preservação de detalhe em alta fidelidade, consistência de personagem em 360°) e a lista de limitações estão transcritos literalmente em `06-fonte-primaria-ai-google-dev.md`, seções 6 e 7. O material `[WS]` era coerente com o original.

A avaliação original se confirma: o template fotorrealista oficial **é rejeitado** pela doutrina do repositório, agora contra o texto literal em vez de paráfrase — ele abre com o termo proibido `photorealistic` e seus slots de luz e óptica são texto livre sem exigência de grandeza física. Justificativa completa em `docs/01-doutrina-hiper-realismo.md`, seção 1.

Registro original abaixo.

---

O material marcado `[WS]` em `04-guia-de-prompts-oficial.md` — template fotorrealista, prompts negativos semânticos, contexto e intenção — vem de paráfrase de busca sobre página bloqueada. O conteúdo é coerente com o `[BLOG]`, que é primeiro-parte e foi lido na íntegra, mas as citações literais não foram verificadas.

**Impacto real: baixo.** O template fotorrealista relatado foi analisado e **rejeitado** por conflitar com a doutrina do repositório, e o `[BLOG]` cobre com muito mais profundidade o mesmo terreno.

### L5 — Documentação da API Higgsfield — **aberta, mas destravada**

**Atualização de 2026-08-16.** Os hosts da Higgsfield **deixaram de estar bloqueados**: `clerk.higgsfield.ai` e `oriented-jay-78.clerk.accounts.dev` respondem `200`, e `fnf-api-gw.higgsfield.ai`, `fnf.higgsfield.ai`, `cdn.higgsfield.ai` e `static.higgsfield.ai` respondem `404` — qualquer código HTTP significa que o túnel CONNECT passa. Nenhuma extração foi feita: a Higgsfield pertence à E5, e esta revisão foi feita durante a E1 apenas no que a E1 consome.

O que continua pendente do usuário é a **credencial** (`refresh_token`), não o acesso de rede.

Registro original abaixo.

---

Todos os hosts da Higgsfield estão bloqueados. Nada foi extraído. A pendência é do usuário, conforme o gate condicional de E5 já previsto no prompt-mestre.

**O que resolveria:** URL base e versão, esquema de autenticação, endpoints de geração e edição com corpo de requisição e resposta, identificadores de modelo (incluindo como o Nano Banana Pro é nomeado lá), parâmetros de imagem suportados, e o modelo de polling ou webhook. Ou a exportação das páginas de documentação para `docs/00-fontes/higgsfield/`.

### L6 — `gemini-3.1-flash-lite-image` — **[RESOLVIDA]**

**Resolução `[GAI]`.** É o **Nano Banana 2 Lite**. Literal: *"Our fastest and cheapest Gemini image model, engineered for velocity and scale where speed and cost are the primary operational constraints. **Not optimized for multiple reference inputs or multi-turn sequential editing.**"*

A própria documentação o desqualifica para o caminho principal deste repositório: multi-referência e edição sequencial em múltiplos turnos são exatamente os dois usos centrais aqui. Permanece fora de escopo, agora por razão documentada em vez de por desconhecimento.

Registro original abaixo.

---

Aparece na lista de seleção de modelos do `[CB]` sem qualquer descrição, e em nenhuma outra fonte. Não se sabe se suporta geração de imagem com as mesmas capacidades, quais resoluções aceita, nem se é adequado a qualquer uso deste repositório.

## Resumo do estado de verificação

Atualizado em 2026-08-16, após a leitura da fonte primária `[GAI]`.

| Categoria | Estado |
|---|---|
| Identificadores de modelo | **Verificado** — quatro fontes primeiro-parte, os quatro modelos nomeados |
| Parâmetros do SDK | **Verificado** — leitura direta do fonte |
| Proporções e dimensões em pixel | **Verificado** — D1 **resolvida** por `[GAI]` |
| Limites de multi-referência | **Verificado** — D2 **resolvida** por `[GAI]`, com correção de 6 para 5 em identidade |
| Capacidades de edição e consistência | **Verificado** |
| Guia de prompts | **Verificado** — L4 **resolvida**, texto literal lido |
| Grounding, thinking, thought signatures | **Verificado**, com D3 aberta |
| **Preço** | **Verificado** — L1 **resolvida**: `$0,134` por imagem 1K/2K, `$0,24` em 4K |
| Marca d'água | **Verificado em substância** — citação universal direta |
| Default de `person_generation` | **`[NÃO VERIFICADO]`** — única lacuna de conteúdo restante |
| Higgsfield | **Nada extraído** — rede destravada, credencial pendente, escopo da E5 |

**Lacunas abertas ao fim da E1:** L3 (`person_generation`) e L5 (Higgsfield). Nenhuma das duas bloqueia E2, E3 ou E4.
