# Gramática do prompt e schema canônico

Etapa **E2**. Transforma a doutrina da E1 em contrato executável: a representação intermediária pela qual todo pedido passa, a gramática em que ela é renderizada, e as validações que impedem um prompt fora da doutrina de sair do sistema.

Arquivos desta etapa:

| Arquivo | Conteúdo |
|---|---|
| `schemas/prompt-spec.json` | O schema canônico. Estrutura, cardinalidade, e — no bloco `x-imagegem` — as regras de coerência, o checklist de emissão, os termos proibidos, o orçamento de densidade e os limites de referência |
| `src/imagegem/check.py` | Regras + checklist + `validate(spec)` — implementação canônica (substituiu `schemas/validador.py` na E5) |
| `src/imagegem/render.py` | Renderizadores das quatro modalidades — implementação canônica (substituiu `schemas/validador.py` na E5) |
| `tests/test_pipeline.py` | 18 testes negativos + 3 bases + 5 renderizadores (movido de `schemas/testes.py` na E5) |
| `schemas/exemplos/exemplo-1-retrato-estudio.json` | O exemplo 1 do prompt-mestre instanciado no schema |
| `schemas/exemplos/exemplo-4-produto-estudio.json` | O exemplo 4 instanciado, prova de que a estrutura serve a cena sem pessoa |

---

## 1. A decisão de gramática

Travada no prompt-mestre e não reaberta aqui; o que esta seção faz é registrar o raciocínio e reconciliá-lo com a fonte primária lida na E1.

Três forças em conflito:

1. **A orientação oficial favorece prosa narrativa densa** sobre listas de palavras-chave. `[GAI]`: *"be hyper-specific — the more detail you provide, the more control you have"*, com exemplos que são parágrafos, não etiquetas.
2. **Restrições negativas explícitas têm valor prático** contra os modos de falha conhecidos. Nenhuma formulação positiva substitui `malformed hands`.
3. **Prompts monolíticos são ruins de editar.** O refinamento iterativo é o modo de uso central, e `[GAI]` o recomenda explicitamente: *"use the conversational nature of the model to make small changes"*. Num bloco único de 600 palavras, "mude só a luz" não tem endereço.

A gramática adotada resolve as três: **blocos rotulados em maiúsculas, cada um contendo prosa narrativa densa, seguidos de uma cauda `AVOID` curta.** Os rótulos dão endereçabilidade — "apenas o bloco `LIGHTING` muda" — sem sacrificar a densidade narrativa dentro de cada bloco, que é o que a força 1 exige.

### A reconciliação com prompts negativos semânticos

`[GAI]` recomenda: *"instead of saying 'no cars,' describe the intended scene positively: 'an empty, deserted street with no signs of traffic.'"* Isso parece condenar a cauda `AVOID`. Não condena, e a distinção é o critério de admissão codificado no item 7 do checklist:

| Tipo | Exemplo | Onde vai |
|---|---|---|
| **Conteúdo de cena** | "sem carros", "sem gente ao fundo" | Declarado **positivamente no corpo**. Nunca na cauda |
| **Modo de falha de renderização** | `airbrushed skin`, `malformed hands`, `CGI look`, `deformed typography` | **Cauda `AVOID`.** Não têm formulação positiva equivalente |

A regra é verificável e está implementada: `ck7_avoid_tail` reprova qualquer entrada da cauda que comece com `no`, `without` ou `not` seguido de substantivo.

## 2. Ordem dos blocos

Declarada em `x-imagegem.ordem_dos_blocos`. Duas ordens, porque edição inverte a lógica.

**Geração e composição:**

```
headline · SUBJECT · WARDROBE · OBJECT AND MATERIALS · CAMERA AND OPTICS
· LIGHTING · REFLECTION GEOMETRY · SKIN · COLOUR AND RENDER · FRAME
· CAPTURE REALITY · AVOID
```

Blocos vazios são omitidos: um retrato de estúdio não emite `OBJECT AND MATERIALS`, um produto não emite `SUBJECT` nem `SKIN`. A ordem é fixa, o conjunto é variável.

**Edição:**

```
headline · PRESERVE · REPLACE · RECONCILE LIGHT · GROUND AND INTEGRATE · AVOID
```

A inversão é deliberada e tem base em fonte. `[BLOG]`, literal:

> State what must stay identical before you state what changes. This is important because most bad edits come from the model rebuilding something you never asked it to touch.

O modo de falha é nomeado pela própria fonte — o modelo **reconstrói** o que ninguém pediu para tocar. `PRESERVE` antes de `REPLACE` é contramedida, não estilo. E `RECONCILE LIGHT` existe porque a montagem se denuncia quando a luz do ambiente novo não justifica a luz já gravada no sujeito.

## 3. Orçamento de densidade — faixas por regime

Aqui a E2 encontrou uma contradição na própria constituição do projeto, e a resolução mudou o desenho.

O prompt-mestre fixa **350–500 palavras** e ancora dizendo que o exemplo 1 tem "~450". Os três exemplos canônicos, medidos:

| Exemplo | Regime | Corpo | Contra 350–500 |
|---|---|---|---|
| 1 — retrato | geração com pessoa | **597** | 97 acima |
| 3 — edição | edição ancorada | **290** | 60 abaixo |
| 4 — produto | geração sem pessoa | **410** | dentro |

A banda única reprovava dois dos três exemplos que a constituição define como padrão de densidade, e o item 8 é gate rígido — o exemplo âncora de calibração não passaria no próprio checklist.

A causa é estrutural, não descuido: **os três regimes carregam conjuntos diferentes de blocos obrigatórios.** Cena com pessoa tem `SUBJECT`, `WARDROBE` e `SKIN`, que produto não tem simultaneamente; edição não respecifica câmera, luz e revelação porque o quadro de origem já as carrega. Nenhuma faixa única cabe nos três.

**Decisão do autor no gate de E2: faixa por regime.**

| Regime | Faixa | Âncora |
|---|---|---|
| Geração com pessoa | **500–650** | exemplo 1, 597 palavras |
| Geração sem pessoa | **350–560** | exemplo 4, 410 palavras |
| Edição | **250–400** | exemplo 3, 290 palavras |

### Por que o teto de "sem pessoa" é 560 e não 500

Porque o âncora do qual a faixa foi derivada **não satisfaz o item 1 do checklist**. O exemplo 4 declara as fontes em taquigrafia — *"a large white card camera-right holds the ratio at 4:1"* — sem as seis grandezas por fonte que o eixo 2 da doutrina exige, e omite o bloco `FRAME` que o schema torna obrigatório.

Custo medido da conformidade sobre o próprio âncora, bloco a bloco:

| Bloco | Exemplo 4 original | Instância conforme | Delta |
|---|---|---|---|
| `LIGHTING` | 81 | 144 | **+63** — seis grandezas por fonte |
| `FRAME` | ausente | 24 | **+24** — obrigatório no schema |
| demais | 305 | 387 | +82 |

O âncora conforme custa ~497 palavras. O teto de 560 é esse valor com cerca de 12% de folga. Manter 500 exigiria afrouxar o item 1, e afrouxar o item 1 é abrir mão da regra que mais carrega realismo. A derivação está registrada em `x-imagegem.orcamento_densidade.faixas[].derivacao_do_teto`.

**Ordem de sacrifício quando o teto reprova**, inalterada: óptica fina primeiro, depois vestuário, depois detalhes secundários de ambiente. Nunca cortam luz, pele ou materiais, e orçamento de imperfeição — porque cortá-los reprova o prompt em outro item.

## 4. Princípio de granularidade do schema

A decisão de projeto mais consequente desta etapa, porque governa o formato de todos os templates da E4.

> **Um campo existe se alguma regra de coerência ou item do checklist precisa lê-lo isoladamente. O resto é prosa dentro do bloco.**

Quebrar demais engessa os templates e transforma redação em preenchimento de formulário. Quebrar de menos devolve prosa livre, sobre a qual nenhuma regra de coerência consegue operar — e aí o checklist vira honra, não gate.

Por isso `camera.iso` é campo inteiro (a regra C1 compara com o grão) enquanto `subject.description` é texto livre (nenhuma regra o lê). Por isso `lighting.sources[].size_m` e `distance_m` são numéricos (C4 calcula a razão) enquanto `modifier` é texto (C5 só procura substring).

## 5. Regras de coerência

Declaradas em `x-imagegem.regras_de_coerencia`, com `check` apontando para a implementação. **Moram no schema de propósito:** a E3 e a E5 leem de lá em vez de reimplementar, o que impede as modalidades de divergirem em rigor.

| ID | Eixo | Regra | Aplica quando |
|---|---|---|---|
| C1 | 7 | Grão corresponde à faixa de ISO, e cita o ISO declarado | sempre |
| C2 | 1 | Abertura larga exige queda de foco declarada; fechada não admite | sempre |
| C3 | 1 | Velocidade e arrasto de movimento concordam | sempre |
| C4 | 2 | Penumbra corresponde à razão tamanho/distância da key | estúdio |
| C5 | 2 | Forma do catchlight corresponde ao modificador da key | há pessoa |
| C6 | 2 | Uma e só uma direção de sombra projetada | sempre |
| C7 | 1 | Veiling flare exige fonte no quadro ou em ângulo de incidência | flare declarado |
| C9 | 5 | Tecido nomeado exige caimento correspondente | há vestuário |
| C10 | 6 | Exterior exige geometria solar e preenchimento de céu | exterior |
| C11 | 3 | Referências de identidade não excedem 5 | há personagem |
| C12 | 6 | Reflexo não implica fonte ausente de `lighting.sources` | há superfície polida |
| C13 | 3 | `has_person` exige `subject` e `skin` | há pessoa |
| C14 | — | Regime `edit` exige o bloco `edit` | edição |

Não há C8: a numeração segue os eixos da doutrina, e o eixo 8 (orçamento de imperfeição) é verificado pela cardinalidade do schema mais o item 5 do checklist, sem precisar de regra própria.

**C4 é guarda grosseira, não modelo fotométrico**, e o código diz isso. A largura real da penumbra depende também da distância entre o objeto e a superfície que recebe a sombra, que o schema não modela. Os limiares pegam a contradição franca — luz dura com penumbra de softbox e vice-versa — e deixam passar a faixa intermediária. Preferir um falso negativo a um falso positivo aqui é deliberado: uma regra que reprova prompts corretos seria desligada na primeira semana.

**Duas metades para C10 e C13.** A parte estrutural (o bloco existe, os campos existem) é imposta declarativamente pelo `allOf` do schema e falha antes das regras rodarem. O que sobra para a regra é a parte semântica — em C10, a divergência de temperatura entre sol e cúpula do céu. Isso é fail-fast intencional, e os testes negativos foram escritos para exercitar a metade que sobra.

## 6. Checklist de emissão codificado

Os oito itens da E1, agora executáveis. `4a` e `4b` são avaliados independentemente — cena com pessoa segurando produto passa pelos dois, conforme a regra de desempate da doutrina.

| Item | Implementação | Falha típica que pega |
|---|---|---|
| 1 | `ck1_light_sources_complete` | Fonte sem temperatura de cor ou sem azimute |
| 2 | delega a C1, C2 e C3 | ISO 3200 com grão "fine" |
| 3 | delega a C6 | Duas direções de sombra |
| 4a | `ck4a_skin` | Falta assimetria específica ou marca preservada |
| 4b | `ck4b_materials` | Superfície nomeada sem resposta especular |
| 5 | `ck5_imperfection_budget` + cardinalidade | "some imperfections are present" |
| 6 | `ck6_forbidden_terms` | `photorealistic` em qualquer campo, detectado no **prompt renderizado** |
| 7 | `ck7_avoid_tail` | `no cars in the background` na cauda |
| 8 | `ck8_density_budget` | Corpo fora da faixa do regime |

O item 6 roda sobre o texto final, não sobre os campos: um termo proibido montado pela concatenação de dois campos limpos seria invisível numa checagem campo a campo.

## 7. Teste de ida — exemplo 1 → schema

`schemas/exemplos/exemplo-1-retrato-estudio.json` instancia o exemplo 1 e valida sem erro estrutural. Nenhuma informação relevante se perdeu: os três marcadores de identidade, as duas assimetrias, as quatro fontes de luz com suas seis grandezas cada, a razão 3:1, a penumbra de 3–4cm, o catchlight octogonal às dez horas, o plano focal com olho próximo e distante, as três imperfeições ópticas, o perfil Portra 400 com ponto de preto em 8%, e as duas imperfeições do orçamento.

O que **não** virou campo, por decisão consciente: nada. As frases do exemplo 1 que não têm campo próprio estão dentro de campos de prosa (`subject.description`, `lighting.background_treatment`), que é onde o princípio de granularidade manda que fiquem.

## 8. Teste de volta — schema → prompt

`renderiza_modalidade_1` reconstitui o prompt a partir do schema. Resultado:

| Exemplo | Original | Renderizado | Overhead |
|---|---|---|---|
| 1 — retrato | 597 palavras | **620** | +3,9% |
| 4 — produto | 410 palavras | **555** | +35,4% |

**O overhead do exemplo 1 é de junção** — conectivos que a prosa manual não precisa ("Key is a…", "The catchlight in each eye is…"). Quatro por cento é fidelidade boa para reconstituição automática.

**O overhead do exemplo 4 não é overhead**, é conformidade: 87 das 145 palavras extras são o bloco `LIGHTING` completo e o `FRAME` obrigatório, que o original não tem. O prompt renderizado é mais rigoroso que o âncora, não mais gordo.

Dois defeitos estruturais foram encontrados **pelo próprio teste de volta** e corrigidos:

1. **Geometria de reflexo duplicada.** A primeira instância do exemplo 4 repetia o conteúdo do reflexo dentro de cada material e de novo no bloco consolidado, inflando o corpo em 44%. O schema passou a separar `materials[].specular_response` (como a superfície responde) de `materials[].reflects` (o que ela reflete), com o segundo consolidado em `REFLECTION GEOMETRY` na renderização. Foi a comparação com o âncora que expôs isso.
2. **Flag tratado como fonte de luz.** O flag preto subtrativo estava em `lighting.sources` e de novo em `background_treatment`. Um flag não emite luz. Removido das fontes.

Ambos são exatamente o tipo de erro que o teste de volta existe para pegar: invisíveis no schema, óbvios no texto emitido.

## 9. Os testes negativos

Um validador que aprova os dois âncoras não prova nada — um que sempre devolve "aprovado" faz o mesmo. `tests/test_pipeline.py` parte de uma instância válida, introduz **uma violação por vez**, e exige que a regra correspondente dispare. Cada caso declara o fragmento que precisa aparecer na mensagem, de modo que passar por acidente — porque outra regra disparou — conta como falha.

```
17 testes negativos passaram, e as duas bases seguem aprovadas.
```

Cobertura: C1, C2, C3, C4, C5, C6, C7, C9, C10, C11, C12, C13, e os itens 1, 5, 6, 7 e 8 do checklist.

## 10. Como rodar

```bash
pip install -e .                  # instala o pacote imagegem e a CLI

imagegem validate schemas/exemplos/exemplo-1-retrato-estudio.json
imagegem render   schemas/exemplos/exemplo-1-retrato-estudio.json --modality 1
python3 tests/test_pipeline.py    # 18 testes negativos + 3 bases + 5 renderizadores
```

## 11. O que fica para as etapas seguintes

- **E3** escreve os renderizadores das modalidades 2, 3 e 4 sobre este mesmo schema, e move `output.aspect_ratio` e `output.resolution` do corpo do texto para os parâmetros estruturados nas modalidades 3 e 4.
- **E4** instancia templates, cada um declarando defaults campo a campo sobre este schema, e usa `meta.defaults_applied` para tornar auditável a diferença entre o que o usuário pediu e o que o template decidiu.
- **E5** substituiu `schemas/validador.py` pela implementação em `src/imagegem/`. **As regras não se moveram** — continuam em `x-imagegem`, e o código de produção lê de lá. O arquivo antigo foi removido.

### Pendências abertas nesta etapa

- **`C14` e o regime de edição não têm instância de exemplo.** O exemplo 3 do prompt-mestre não foi instanciado, porque a gramática de edição só é exercitada de ponta a ponta na E3, onde os renderizadores por modalidade existem. A regra está implementada e o schema tem o bloco `edit`; falta o teste de ida e volta desse regime. Fica registrado como dívida da E3, não desta etapa.
- **`composition` herda as faixas de densidade de `generation`.** Assumido, não medido: não há exemplo âncora de composição multi-referência no prompt-mestre. Premissa declarada; a E4 mede quando tiver o primeiro template de composição.
