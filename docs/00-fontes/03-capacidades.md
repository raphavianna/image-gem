# Capacidades, multi-referência e consistência de personagem

O prompt-mestre marcou esta página como prioridade de E0: consistência de personagem é capacidade central do Nano Banana Pro e o ponto de menor cobertura interna. Extraída explicitamente.

## Capacidades declaradas

Literal `[CB]`, no cabeçalho do notebook:

> These models are really good at:
> * **Maintaining character consistency**: Preserve a subject's appearance across multiple generated images and scenes
> * **Performing intelligent editing**: Enable precise, prompt-based edits like inpainting (adding/changing objects), outpainting, and targeted transformations within an image
> * **Compose and merge images**: Intelligently combine elements from multiple images into a single, photorealistic composite (maximum 3 with flash, 14 with pro)
> * **Leverage multimodal reasoning**: Build features that understand visual context, such as following complex instructions on a hand-drawn diagram

Consistência de personagem aparece como **primeiro item** da lista de capacidades — não é efeito colateral, é característica projetada.

## Limites de multi-referência

Aqui há três números na mesma fonte, e a distinção entre eles é a informação mais útil de toda esta página.

Literal `[CB]`, seção "Mix multiple pictures":

> You can also mix multiple images (up to 3 with nano-banana, 14 with nano-banana-pro, 6 with high fidelity), either because there are multiple characters in your image, or because you want to hightlight a certain product, or set the background.

Literal `[CB]`, seção "Mix up to 14 images!":

> You can now mix up to 6 images in high-fidelity and 14 with minor changes.

Consolidando:

| Regime | Limite | Significado |
|---|---|---|
| `gemini-2.5-flash-image` | 3 imagens | Teto do modelo Flash antigo |
| `gemini-3-pro-image` — **alta fidelidade** | **6 imagens** | As referências são preservadas com fidelidade alta |
| `gemini-3-pro-image` — alterações menores | 14 imagens | Acima de 6, as referências sofrem "minor changes" |

**Esta é a regra operacional que importa para nós.** O limite útil para consistência de personagem hiper-realista não é 14, é **6**. Acima disso a própria documentação admite degradação das referências, e degradação de referência é exatamente a falha que destrói identidade facial. Os templates de E4 que dependem de identidade preservada devem operar dentro do teto de 6.

Nota de divergência: o `[BLOG]` afirma "até 14 imagens de referência" para ambos os modelos, sem mencionar o corte de fidelidade em 6, e sem o limite de 3 para o Flash. Registrado em `05-divergencias-e-lacunas.md`.

Contorno oficial para exceder o limite, literal `[CB]`:

> Tip: Combine multiple images into a single 'collage' first if you need to go beyond the image upload limit.

## Como a consistência de personagem é exercida na prática

O padrão do notebook é: gerar, salvar, e realimentar a imagem salva como referência do turno seguinte `[CB]`:

```python
text_prompt = "Create a side view picture of that cat, in a tropical forest, eating a nano-banana, under the stars"

interaction = client.interactions.create(
    model=MODEL_ID,
    input=[
        text_prompt,
        PIL.Image.open('cat.png')      # a geração anterior vira referência
    ]
)
```

Comentário do autor logo abaixo `[CB]`:

> As you can see, you can clearly recognize the same cat with its peculiar nose and eyes.

Dois pontos a extrair para E1:

1. A referência entra como **elemento da lista de entrada**, ao lado do texto. Não existe um campo dedicado a "imagem de identidade" na Gemini API — o `[SDK]` só expõe `SubjectReferenceConfig` e afins no caminho **Imagen/Vertex**, não em `ImageConfig`. A separação entre "o que é invariante" e "o que varia" é feita **no texto do prompt**, não por parâmetro.
2. O que o autor destaca como prova de consistência são **traços idiossincráticos** (o nariz peculiar, os olhos de cores diferentes). Isso converge com o eixo 3 da doutrina: são as marcas específicas, não a média do rosto, que carregam identidade entre gerações.

A regra prática de separação invariante × variável será derivada em E1. A base textual vem do `[BLOG]`, seção de edição:

> State what must stay identical before you state what changes. This is important because most bad edits come from the model rebuilding something you never asked it to touch.

Esta frase valida diretamente a gramática de edição do exemplo 3 do prompt-mestre — bloco `PRESERVE` antes do bloco `REPLACE`.

## Edição

Verbos de operação, `[BLOG]`: **add, change, make, remove, replace**. A recomendação é começar o prompt com um verbo forte que declare a operação primária.

Técnica nomeada `[BLOG]`: **semantic masking** (inpainting). Define-se por texto uma "máscara" da região a editar, deixando o resto intacto. Não há parâmetro de máscara na Gemini API — a máscara é semântica, expressa em linguagem.

Fórmulas `[BLOG]`:

- Edição conversacional, sem novas referências: descrição da alteração, com explicitação do que se mantém.
- Composição e transferência de estilo, com novas referências: imagem base + imagem de objeto, com instrução de combinação.

Capacidades de edição confirmadas por exemplo executável `[CB]`: troca de cenário, mudança de época ("as if they were living in the 1980s"), restauração e colorização de foto histórica de 1932, mudança de ponto de vista, transferência de estilo, e composição multi-imagem.

## Thinking

Ambos os modelos Gemini 3 pensam antes de responder `[CB]`. Para o Nano Banana Pro isso significa que o modelo elabora a cena antes de gerá-la — relevante para prompts físicos densos como os nossos, porque há uma etapa de reconciliação interna.

Os pensamentos são inspecionáveis quando `include_thoughts=True` `[CB]`:

```python
for part in response.parts:
  if part.thought:
    if part.text:
      display(Markdown(part.text))
```

**Isso é um instrumento de diagnóstico direto para o loop de E6.** Quando uma imagem sai com aparência sintética, os pensamentos mostram como o modelo interpretou a especificação física — permitindo distinguir "o prompt estava ambíguo" de "o modelo ignorou a instrução". O registro de execução em `runs/` deve prever campo para os pensamentos.

## Thought signatures

Literal `[CB]`:

> The output part of Gemini 3 models always contain `though_signatures`. If you are using the SDK since it's entirely managed by the SDKs.

> This signature is used by the model when you want to do chat/multi-turn discussions. It helps the model not only remember what was said before, but also what it thought before or what it got from its tools and function calls.

Gerenciado pelo SDK, sem ação necessária. A consequência é que **o modo chat carrega mais estado do que apenas as mensagens** — o refinamento iterativo em `client.chats` preserva o raciocínio anterior, não só o texto. Mais um argumento para o loop de refinamento usar chat em vez de chamadas unárias independentes.

## Grounding com Google Search

Disponível no NB Pro e no NB 2 `[CB]`. Restrições já registradas em `02-parametros-sdk.md`: só ancora em resultados de texto no NB Pro; `response_modalities` precisa incluir `TEXT`; busca de imagens é exclusiva do NB 2 e não busca imagens de pessoas.

Relevância para este repositório: **baixa a moderada.** Grounding serve a diagramas, infográficos e dados factuais — não a retrato hiper-realista. A exceção é locação real: ancorar em um lugar específico pode melhorar plausibilidade de ambiente. Fica documentado como recurso opcional, fora do caminho principal.

## Múltiplas imagens por chamada

O modelo pode devolver várias imagens numa resposta `[CB]` — usado para sequências narrativas e tutoriais passo a passo. O código de leitura da resposta precisa iterar sobre todas as partes, não parar na primeira `[CB]`:

> You'll also have to take into account that there could be multiple images so you cannot stop at the first one.

## Vídeo para imagem

Exclusivo do `gemini-3.1-flash-image` `[CB]`. Aceita URL pública do YouTube ou upload via Files API; analisa os frames até o limite de 131.072 tokens de entrada; `video_metadata=types.VideoMetadata(fps=0.5)` reduz consumo. **Não disponível no `gemini-3-pro-image`** — fora do escopo deste repositório, registrado por completude.
