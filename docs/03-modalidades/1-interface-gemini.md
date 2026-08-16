# Modalidade 1 — Interface Gemini

Prompt colável para a interface do Gemini em `gemini.google.com`. É a modalidade de exploração e iteração conversacional: sem parâmetros estruturados, um único usuário, texto puro.

## O que muda em relação ao schema

Como não há campos de chamada, **proporção e resolução são verbalizadas no cabeçalho**:

```
Editorial studio portrait, single subject, waist-up, vertical 4:5 frame.
```

O resto do prompt segue a ordem canônica de blocos de `x-imagegem.ordem_dos_blocos.generation`:

```
headline · SUBJECT · WARDROBE · OBJECT AND MATERIALS · CAMERA AND OPTICS
· LIGHTING · REFLECTION GEOMETRY · SKIN · COLOUR AND RENDER · FRAME
· CAPTURE REALITY · AVOID
```

Blocos vazios são omitidos. Um retrato não emite `OBJECT AND MATERIALS`. Um produto não emite `SUBJECT` nem `SKIN`. A ordem é fixa; o conjunto é variável.

## Renderizador

Implementação em `schemas/validador.py`:

```python
def renderiza_modalidade_1(spec, incluir_output_no_texto=True): ...
```

Assinatura mínima porque este é o modo base — as outras modalidades chamam a mesma função com `incluir_output_no_texto=False` para tirar a proporção do texto.

## Fluxo de uso

1. Cole o prompt na caixa de conversa.
2. Aguarde a primeira imagem.
3. Refinamento iterativo, endereçando um bloco por turno — a razão de blocos rotulados existirem. `[GAI]`: *"use the conversational nature of the model to make small changes"*.
4. Para variantes de composição, cole o mesmo prompt e mude só o bloco que precisa mudar. O modelo Gemini 3 preserva *thought signatures* no chat, o que reduz deriva entre turnos `[CB]`.

## Exemplo ponta a ponta — retrato de estúdio

Instância: `schemas/exemplos/exemplo-1-retrato-estudio.json`.
Prompt renderizado: `exemplos/exemplo-1-retrato-estudio-mod1.txt`.

Métricas de validação, reprodutíveis com `python3 schemas/validador.py schemas/exemplos/exemplo-1-retrato-estudio.json`:

| Métrica | Valor |
|---|---|
| Regras de coerência aplicáveis e aprovadas | 8 de 13 |
| Itens do checklist aprovados | 9 de 9 |
| Corpo | 620 palavras |
| Faixa do regime (geração com pessoa) | 500–650 |
| Cauda `AVOID` | 28 palavras |

Abertura e fecho do prompt:

```
Editorial studio portrait, single subject, waist-up, vertical 4:5 frame.

SUBJECT. A 34-year-old woman with warm olive skin, dark brown eyes and
shoulder-length black hair worn loose with a natural side part. Her facial
structure is specifically asymmetric: the left eyebrow sits marginally higher
than the right, and the left corner of the mouth lifts slightly more.
[...]

CAPTURE REALITY. One strand of hair has fallen across the forehead and has
not been styled back. One shoulder seam sits a few millimetres off square.
This is a single working frame from a commercial session.

AVOID: illustration, 3D render, CGI, digital painting, airbrushed or waxy
skin, uniform poreless texture, perfect facial symmetry, glowing teeth,
oversaturated colour, HDR halos, watermark, text overlay, malformed hands.
```

## Turnos de refinamento — como endereçar um bloco

A gramática de blocos rotulados foi escolhida para dar endereço nos turnos seguintes. Os padrões que funcionam:

```
Keep everything the same, but change the LIGHTING block: replace the
gridded strip box behind and camera-right with a bare 300W tungsten head
at 3200K, at the same position. Update the mixed_temperature note.
```

```
Same prompt, but change only the CAPTURE REALITY block: instead of the
stray strand of hair, add a light diffusion breath fogging the corner of
the frame from the near shoulder.
```

`[GAI]` valida esse padrão literal: *"That's great, but can you make the lighting a bit warmer?" or "Keep everything the same, but change the character's expression to be more serious."*

## Limites da modalidade

- **Sem parâmetros estruturados** — a chance de o modelo obedecer à proporção declarada em texto é alta, mas não é gate. Se a proporção precisa ser auditável, use a modalidade 4.
- **Sem `include_thoughts`** — não dá para inspecionar o raciocínio do modelo, o que a modalidade 4 permite. Para diagnóstico de "por que a pele saiu assim", use a modalidade 4.
- **Não há como configurar `person_generation`** — a lacuna L3 é herdada, mas irrelevante aqui: a política de conteúdo é aplicada pelo comportamento default do serviço.

## Marca d'água

Independente da modalidade, toda imagem sai com SynthID (`[GAI]`, seção 5 de `06-fonte-primaria-ai-google-dev.md`). A modalidade 1 não a menciona no prompt porque não há como desativar; documentar aqui só para que ninguém coloque `no watermark` na cauda `AVOID` — o item 7 do checklist reprovaria.
