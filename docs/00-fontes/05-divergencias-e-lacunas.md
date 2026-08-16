# Divergências entre fontes e lacunas

Hierarquia aplicada, conforme o prompt-mestre: `[SDK]` é autoridade para nomes, tipos e valores aceitos de parâmetro; documentação primeiro-parte é autoridade para capacidades, limites e preços; cookbook e notebooks são autoridade apenas para padrões de uso.

## Divergências

### D1 — Proporções `4:5` e `5:4` ausentes na docstring do SDK

| Fonte | Afirma |
|---|---|
| `[SDK]` | `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"9:16"`, `"16:9"`, `"21:9"` — **oito** valores |
| `[CB]` | Tabela com **dez**, incluindo `4:5` e `5:4`, com dimensões exatas em pixel nas quatro resoluções |
| `[BLOG]` | Lista **dez** para o NB Pro, incluindo `4:5` e `5:4` |

**Resolução:** `4:5` e `5:4` são tratados como suportados. O campo `aspect_ratio` é `Optional[str]` no `[SDK]` — texto livre, sem enum e sem validação em tempo de execução —, portanto a docstring é prosa descritiva, não contrato executável. Duas fontes primeiro-parte independentes listam os dez valores, e `[CB]` fornece dimensões em pixel para `4:5` nas quatro resoluções, o que seria implausível para uma proporção inexistente. A docstring do SDK está desatualizada.

**Consequência:** o exemplo âncora de calibração usa `4:5` e permanece válido. O renderizador de E3 aceita os dez valores.

**Confirmação pendente:** uma chamada real com `aspect_ratio="4:5"`, verificando a dimensão retornada contra 928×1152 em 1K. Entra na bateria de validação assim que houver `GEMINI_API_KEY`.

### D2 — Limite de imagens de referência

| Fonte | Afirma |
|---|---|
| `[CB]` | 3 no Flash; 14 no Pro; **6 em alta fidelidade** |
| `[BLOG]` | "até 14" para ambos os modelos, sem menção ao corte de fidelidade nem ao limite de 3 |

**Resolução:** o `[CB]` prevalece por ser mais específico e por afirmar o corte de fidelidade duas vezes, em seções diferentes. A regra operacional adotada é **6 imagens** como teto para qualquer template que dependa de identidade preservada, e 14 como teto absoluto para composições tolerantes a alteração. O `[BLOG]` não contradiz o corte de 6 — apenas não o menciona.

**Confirmação pendente:** comparação empírica de preservação de identidade com 6 e com 8 referências, registrada em `runs/`.

### D3 — `thinking_level` no Nano Banana Pro

O `[CB]` descreve thinking como capacidade de ambos os modelos Gemini 3, mas anota o parâmetro `thinking_level` no código como *"Only for Nano-Banana 2"*, e escreve na prosa: *"**Nano-Banana 2** also introduces **Thinking Levels**"*.

**Resolução:** leitura literal — o NB Pro **pensa**, mas o controle explícito do nível de raciocínio via `thinking_level` foi introduzido pelo NB 2. Isso significa que, no `gemini-3-pro-image`, `include_thoughts=True` deve funcionar para inspeção, enquanto `thinking_level` pode ser ignorado ou rejeitado.

**Consequência:** o cliente de E5 não deve depender de `thinking_level` no caminho do NB Pro. Marcado `[NÃO VERIFICADO]` até teste.

## Lacunas — `[NÃO VERIFICADO]`

### L1 — Preço por imagem — **lacuna crítica**

Nenhum valor de preço foi obtido de fonte primeiro-parte. Todas as páginas de preço estão em `ai.google.dev/gemini-api/docs/pricing` e `docs.cloud.google.com`, ambas bloqueadas no egress. O `[CB]` apenas remete a elas por link.

O prompt-mestre listava a documentação em `cloud.google.com` como autoridade para preços; na prática, todo caminho `cloud.google.com/vertex-ai/...` responde 301 para `docs.cloud.google.com`, que é bloqueado. **A autoridade prevista para preços não existe nesta sessão.**

Um valor de US$ 0,134 por imagem circulou em resultado de busca de terceiro durante a coleta. **Não é fonte primeiro-parte e não foi adotado.** Está registrado aqui apenas para que ninguém o reintroduza depois julgando ser dado verificado.

O que se sabe com base primeiro-parte:
- Geração de imagem exige faturamento ativo; é pay-as-you-go `[CB]`.
- Tokens dependem de modelo e resolução, **não** da proporção `[CB]`.
- 4K custa mais que 1K `[CB]`: *"4K images are more expensive so only do it when needed"*.
- Tokens de pensamento são cobrados como tokens de saída; imagens dentro dos pensamentos não são `[CB]`.

**O que resolveria:** liberar `ai.google.dev` ou `docs.cloud.google.com` no egress; ou o usuário colar a tabela de preços; ou uma chamada real com leitura de `usage_metadata`, que dá contagem de tokens — não preço, mas a metade que falta para calcular.

### L2 — Marca d'água não configurável nos modelos Gemini de imagem

`add_watermark` existe no `[SDK]` apenas no caminho Imagen, não em `ImageConfig`. O `[BLOG]` lista C2PA + SynthID como característica dos modelos Nano Banana. A conclusão de que a marca d'água é **automática e não desativável** é inferência coerente com as duas fontes, mas não há citação que a afirme.

**O que resolveria:** a página de imagem de `ai.google.dev`, ou inspeção dos metadados de uma imagem gerada de verdade.

### L3 — Comportamento de `person_generation` na Gemini API

Os três valores estão no `[SDK]` sem marcação de indisponibilidade, logo valem para a Gemini API. Não foi encontrada documentação de qual é o **default** quando o campo é omitido, nem do comportamento exato de `ALLOW_ADULT` (bloqueio duro, recusa suave, ou filtragem posterior).

Importa porque a política de conteúdo do repositório depende disso. **O que resolveria:** a documentação bloqueada, ou teste empírico.

### L4 — Guia de prompts de `ai.google.dev` não lido diretamente

O material marcado `[WS]` em `04-guia-de-prompts-oficial.md` — template fotorrealista, prompts negativos semânticos, contexto e intenção — vem de paráfrase de busca sobre página bloqueada. O conteúdo é coerente com o `[BLOG]`, que é primeiro-parte e foi lido na íntegra, mas as citações literais não foram verificadas.

**Impacto real: baixo.** O template fotorrealista relatado foi analisado e **rejeitado** por conflitar com a doutrina do repositório, e o `[BLOG]` cobre com muito mais profundidade o mesmo terreno.

### L5 — Documentação da API Higgsfield

Todos os hosts da Higgsfield estão bloqueados. Nada foi extraído. A pendência é do usuário, conforme o gate condicional de E5 já previsto no prompt-mestre.

**O que resolveria:** URL base e versão, esquema de autenticação, endpoints de geração e edição com corpo de requisição e resposta, identificadores de modelo (incluindo como o Nano Banana Pro é nomeado lá), parâmetros de imagem suportados, e o modelo de polling ou webhook. Ou a exportação das páginas de documentação para `docs/00-fontes/higgsfield/`.

### L6 — `gemini-3.1-flash-lite-image`

Aparece na lista de seleção de modelos do `[CB]` sem qualquer descrição, e em nenhuma outra fonte. Não se sabe se suporta geração de imagem com as mesmas capacidades, quais resoluções aceita, nem se é adequado a qualquer uso deste repositório.

**Impacto: nenhum no caminho principal.** Registrado por completude.

## Resumo do estado de verificação

| Categoria | Estado |
|---|---|
| Identificadores de modelo | **Verificado** — três fontes primeiro-parte |
| Parâmetros do SDK | **Verificado** — leitura direta do fonte |
| Proporções e dimensões em pixel | **Verificado**, com D1 anotada |
| Limites de multi-referência | **Verificado**, com D2 resolvida a favor do valor mais conservador |
| Capacidades de edição e consistência | **Verificado** |
| Guia de prompts | **Verificado** via `[BLOG]`; complemento `[WS]` de confiança média |
| Grounding, thinking, thought signatures | **Verificado**, com D3 aberta |
| **Preço** | **`[NÃO VERIFICADO]` — lacuna crítica** |
| Marca d'água | **`[NÃO VERIFICADO]`** — inferência |
| Default de `person_generation` | **`[NÃO VERIFICADO]`** |
| Higgsfield | **Nada extraído** |
