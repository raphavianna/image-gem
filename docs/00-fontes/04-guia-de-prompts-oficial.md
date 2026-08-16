# Guia de prompts oficial

Fonte principal: `[BLOG]` — Google Cloud Blog, *Ultimate prompting guide for Nano Banana*. É a fonte primeiro-parte mais completa que o egress desta sessão permitiu alcançar. O guia de prompts de `ai.google.dev` está bloqueado; o que dele consta aqui está marcado `[WS]` e tem confiança reduzida.

## Regras fundamentais

Literal `[BLOG]`:

1. **Seja específico.** Detalhes concretos sobre assunto, iluminação e composição.
2. **Use formulação positiva.** Descreva o que você quer, não o que não quer — "rua vazia" em vez de "sem carros".
3. **Controle a câmera.** Termos fotográficos e cinematográficos: *low angle*, *aerial view*.
4. **Itere.** Refine de forma conversacional com prompts de acompanhamento.

E a regra que o `[BLOG]` chama de crucial:

> Comece o prompt com um verbo forte que indique a operação primária desejada.

## Os cinco frameworks

### 1. Geração de imagem

**Text-to-image, fórmula literal `[BLOG]`:**

```
[Subject] + [Action] + [Location/context] + [Composition] + [Style]
```

Exemplo literal `[BLOG]`:

> [Subject] A striking fashion model wearing a tailored brown dress, sleek boots, and holding a structured handbag. [Action] Posing with a confident, statuesque stance, slightly turned. [Location/context] A seamless, deep cherry red studio backdrop. [Composition] Medium-full shot, center-framed. [Style] Fashion magazine style editorial, shot on medium-format analog film, pronounced grain, high saturation, cinematic lighting effect.

**Geração multimodal com referências, fórmula literal `[BLOG]`:**

```
[Reference images] + [Relationship instruction] + [New scenario]
```

Exemplo literal `[BLOG]`:

> Using the attached napkin sketch as the structure and the attached fabric sample as the texture [References], transform this into a high-fidelity 3D armchair render [Relationship]. Place it in a sun-drenched, minimalist living room [New Scenario].

O bloco de *relationship instruction* é o que nomeia o **papel** de cada referência. Com múltiplas imagens, sem esse bloco o modelo não sabe qual referência governa estrutura, qual governa textura e qual governa identidade. Entra em E2 como campo obrigatório do schema quando houver mais de uma referência.

### 2. Edição de imagem

Coberto em `03-capacidades.md`. Núcleo: verbos **add, change, make, remove, replace**; *semantic masking*; e a regra de declarar o invariante antes da mudança.

### 3. Informação em tempo real

```
[Search request] + [Analytical task] + [Visual translation]
```

Fora do caminho principal deste repositório.

### 4. Renderização de texto e localização

Regras literais `[BLOG]`:

1. **Use aspas** em torno das palavras a renderizar — `"Happy Birthday"`, `"URBAN EXPLORER"`.
2. **Nomeie a fonte** — `"bold, white, sans-serif font"`, `"Century Gothic 12px font"`.
3. **Traduza e localize** — escreva o prompt num idioma e especifique o idioma-alvo do texto renderizado.
4. **Text-first hack** — converse primeiro com o modelo para gerar o conteúdo textual, depois peça a imagem com esse texto.

Relevância aqui: os nossos prompts em geral **proíbem** texto na imagem (a cauda `AVOID` inclui `text overlay`). A exceção real é fotografia de produto, onde tipografia de rótulo precisa sair legível e correta — o exemplo 4 do prompt-mestre protege explicitamente a tipografia do mostrador. A regra das aspas se aplica nesse caso.

### 5. Prompting como diretor criativo

Este é o framework que mais se aproxima da doutrina de hiper-realismo do repositório. Quatro eixos `[BLOG]`:

**Design da iluminação.** Diga exatamente como a cena é iluminada. Exemplos citados: *"three-point softbox setup"*; *"Chiaroscuro lighting with harsh, high contrast"*; *"Golden hour backlighting creating long shadows"*.

**Câmera, lente e foco.** Terminologia fotográfica específica para controlar profundidade, distorção e perspectiva. Corpos citados como portadores de assinatura visual: GoPro para ação imersiva e distorcida; Fujifilm para ciência de cor autêntica; câmera descartável para estética crua e nostálgica com flash. Lentes: *"low-angle shot with a shallow depth of field (f/1.8)"*, *"wide-angle lens"*, *"macro lens"*.

**Color grading e filme.** *"as if on 1980s color film, slightly grainy"*; *"Cinematic color grading with muted teal tones"*.

**Materialidade e textura.** Literal `[BLOG]`: não peça um "blazer", peça um *"navy blue tweed suit jacket"*; não peça "armadura", peça *"ornate elven plate armor, etched with silver leaf patterns"*.

Estrutura expandida de direção criativa, literal `[BLOG]`:

```
[Subject with materials] + [Action/Pose] + [Location with lighting setup] +
[Camera/Lens specifications] + [Composition] + [Color grading/Film stock] +
[Texture details] + [Style/Mood]
```

**Esta fórmula é o ancestral direto da nossa gramática de blocos.** A correspondência com os rótulos definidos no prompt-mestre:

| Fórmula `[BLOG]` | Bloco da nossa gramática |
|---|---|
| Subject with materials | `SUBJECT` + `WARDROBE` |
| Action/Pose | dentro de `SUBJECT` |
| Location with lighting setup | `LIGHTING` (+ ambiente) |
| Camera/Lens specifications | `CAMERA AND OPTICS` |
| Composition | `FRAME` |
| Color grading/Film stock | `COLOUR AND RENDER` |
| Texture details | `SKIN` ou `MATERIALS` |
| Style/Mood | disperso; a nossa gramática o substitui por `CAPTURE REALITY` |

A nossa gramática **é** a fórmula oficial, com três diferenças deliberadas: rótulos explícitos em vez de concatenação implícita, `CAPTURE REALITY` no lugar de "Style/Mood" (porque estilo declarado é o caminho para aparência sintética, e contexto de captura é o caminho oposto), e a cauda `AVOID`. E2 documenta e justifica as três.

## Template fotorrealista de `ai.google.dev` `[WS]`

**Confiança média.** Recuperado por busca web sobre página bloqueada; não lido diretamente.

Template relatado:

> "A photorealistic [type of shot] of a [subject description] in a [setting description]. [Description of the light]. Shot from a [camera angle] with a [lens type]."

Exemplo relatado:

> "A photorealistic wide-angle shot of a vibrant coral reef teeming with tropical fish. Crystal-clear turquoise water with sunbeams filtering down from the surface, illuminating a sea turtle gliding gracefully over the coral. Shot from a low perspective with a wide-angle lens."

Registrado por fidelidade à fonte, **não adotado**. Duas razões, ambas alinhadas à regra inegociável do repositório: o template abre com a palavra `photorealistic`, que a doutrina classifica como ruído; e sua especificação de luz e óptica é qualitativa ("sunbeams filtering down") onde a nossa é quantitativa. É o piso genérico do modelo, não o padrão de um sistema dedicado a realismo indistinguível.

## Prompts negativos — a tensão com a nossa gramática

Posição oficial `[BLOG]`: usar formulação positiva. Reforçado `[WS]` com o conceito de *semantic negative prompt* — em vez de "sem carros", descrever "uma rua vazia e deserta, sem sinal de tráfego"; e evitar linguagem instrutiva de negação, preferindo `crowds, boats` a `no crowds, no boats`.

A gramática do repositório foi decidida pelo usuário e **não é reaberta**: prosa narrativa positiva nos blocos, com cauda `AVOID` curta e delimitada.

O que E0 registra é a evidência que E2 precisa considerar ao documentar a decisão:

1. A orientação oficial contra negação é sobre **o corpo do prompt**, e nisso a nossa gramática já está conforme — os blocos são integralmente positivos e descritivos.
2. A formulação `[WS]` recomendada para exclusões é **lista de substantivos sem partícula de negação** (`crowds, boats`). A nossa cauda `AVOID` já segue exatamente esse formato: `illustration, 3D render, CGI, digital painting, ...` — substantivos, sem "no" nem "don't". A divergência com a orientação oficial é, portanto, **menor do que parece**: reside no rótulo `AVOID:`, não na formulação dos itens.
3. Nenhuma fonte primeiro-parte encontrada afirma que uma cauda de exclusão prejudique o resultado. A orientação é preferência, não proibição.

Encaminhamento para E2: manter a cauda, documentar que seus itens são substantivos sem negação (conforme à orientação), e registrar em `runs/` a comparação empírica com e sem cauda assim que houver chave de API. É uma hipótese testável, e o loop de E6 existe para isso.

## Iteração

Literal `[BLOG]` e `[WS]`: não esperar a imagem certa na primeira tentativa; usar prompts de acompanhamento para ajustes pontuais — *"Make the lighting warmer"*, *"Change the character's expression to be more serious"*. E a regra de disciplina `[WS]`: **mudar uma variável por vez**.

Isto casa com a decisão de gramática por blocos rotulados: com rótulos, o turno de refinamento pode dizer "apenas o bloco LIGHTING muda", que é a forma mais precisa de mudar uma variável por vez.

## Contexto e intenção

Literal `[WS]`: explicar a finalidade da imagem ajuda o modelo — *"Create a logo for a high-end, minimalist skincare brand"* funciona melhor que *"Create a logo"*. Suporta o campo **uso final da imagem** listado no prompt-mestre entre os campos de pergunta obrigatória da Skill.
