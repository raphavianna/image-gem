# Superfície do SDK `google-genai`

Autoridade desta página: `[SDK]` — `googleapis/python-genai`, `google/genai/types.py` em `main`. Onde o `[CB]` mostra o uso real, o trecho de código está reproduzido.

## Pacote

- Nome: `google-genai` `[PYPI]`
- Versão mais recente: **2.18.1** `[PYPI]`
- Python exigido: `>=3.10` `[PYPI]`
- Mínimo para suporte a Nano Banana 2: `>=2.9.0` `[CB]` — literal: `%pip install -U -q "google-genai>=2.9.0"`

## Cliente

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=GEMINI_API_KEY)   # Gemini API  [CB]
```

Para Vertex AI o cliente muda `[VTX-NB]`:

```python
client = genai.Client(enterprise=True, project=PROJECT_ID, location=LOCATION)
```

## As três APIs de chamada

O `[SDK]` expõe três superfícies distintas, todas presentes em `client.py` (`interactions`, `models`, `chats`). O notebook `[CB]` usa predominantemente a primeira.

### 1. `client.interactions.create(...)` — a superfície nova

Classe interna: `GeminiNextGenInteractions` `[SDK]`. Assinatura observada `[CB]`:

```python
interaction = client.interactions.create(
    model=MODEL_ID,
    input=prompt,                       # str, ou lista [str, PIL.Image, ...]
    config=types.GenerateContentConfig(...)
)
```

A resposta é percorrida por **steps**, não por `parts` `[CB]`:

```python
for step in interaction.steps:
    if step.type == "model_output":
        for content in step.content:
            if hasattr(content, 'thought') and content.thought:
                continue                    # pula os pensamentos
            if content.text:
                display(Markdown(content.text))
            elif image := content.as_image():
                image.show()
```

### 2. `client.models.generate_content(...)` — a superfície clássica

Ainda usada no próprio notebook para vídeo-para-imagem `[CB]` e nos exemplos Vertex `[VTX-NB]`. A resposta é percorrida por `response.parts`.

### 3. `client.chats.create(...)` — **recomendada para refinamento iterativo**

Literal `[CB]`, no cabeçalho da seção:

> ## Chat mode (recommended method)
> So far you've used unary calls, but Image-out is actually made to work better with chat mode as it's easier to iterate on an image turn after turn.

```python
chat = client.chats.create(model=MODEL_ID)
response = chat.send_message(message)
```

A configuração pode ser passada por turno, sobrescrevendo a do chat `[CB]`:

```python
response = chat.send_message(
    message,
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9"),
    ),
)
```

Isto é diretamente relevante para a modalidade 4: o loop de refinamento hiper-realista é conversacional, e o modo chat é o suporte nativo dele.

## `types.ImageConfig` — campos exatos

Reprodução fiel do `[SDK]`, incluindo as marcações de disponibilidade:

| Campo | Tipo | Valores | Disponibilidade |
|---|---|---|---|
| `aspect_ratio` | `Optional[str]` | docstring lista `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"9:16"`, `"16:9"`, `"21:9"` | Gemini API e Vertex |
| `image_size` | `Optional[str]` | `1K`, `2K`, `4K`. Default `1K` se omitido | Gemini API e Vertex |
| `person_generation` | `Optional[str]` | `ALLOW_ALL`, `ALLOW_ADULT`, `ALLOW_NONE` | Gemini API e Vertex |
| `prominent_people` | `Optional[ProminentPeople]` | `PROMINENT_PEOPLE_UNSPECIFIED`, `ALLOW_PROMINENT_PEOPLE` | **Não suportado na Gemini API** |
| `output_mime_type` | `Optional[str]` | MIME da imagem gerada | **Não suportado na Gemini API** |
| `output_compression_quality` | `Optional[int]` | só para `image/jpeg` | **Não suportado na Gemini API** |
| `image_output_options` | `Optional[ImageConfigImageOutputOptions]` | `compression_quality`, `mime_type` | **Não suportado na Gemini API** |

Docstring literal de `image_size` `[SDK]`:

> Optional. Specifies the size of generated images. Supported values are `1K`, `2K`, `4K`. If not specified, the model will use default value `1K`.

Docstring literal de `prominent_people` `[SDK]`:

> Optional. Controls whether prominent people (celebrities) generation is allowed. If used with personGeneration, personGeneration enum would take precedence. For instance, if ALLOW_NONE is set, all person generation would be blocked. If this field is unspecified, the default behavior is to allow prominent people. This field is not supported in Gemini API.

**Consequência direta para a política de conteúdo do repositório.** `person_generation` e `prominent_people` são os controles nativos do modelo sobre geração de pessoas e de celebridades. A política definida no prompt-mestre — não gerar pessoas reais identificáveis fora do caso de referência do próprio usuário, e não gerar menores — tem correspondência parcial em API: `ALLOW_ADULT` cobre a regra de menores no nível do modelo. `prominent_people` cobriria celebridades, mas **não existe na Gemini API**, apenas em Vertex. Portanto, na modalidade 4 via Gemini API, a restrição de pessoas públicas precisa ser aplicada na camada da Skill, não delegada ao modelo. Isso entra em E5.

Quatro dos sete campos de `ImageConfig` são exclusivos de Vertex. Um cliente escrito só contra a Gemini API usa três: `aspect_ratio`, `image_size`, `person_generation`.

## `types.GenerateContentConfig` — campos relevantes

| Campo | Tipo | Nota |
|---|---|---|
| `response_modalities` | `Optional[list[str]]` | Valores do enum `Modality` `[SDK]`: `TEXT`, `IMAGE`, `AUDIO`, `VIDEO`, `MODALITY_UNSPECIFIED`. O enum é *case-insensitive* (`_common.CaseInSensitiveEnum`), o que explica o notebook usar tanto `['Text', 'Image']` quanto `["IMAGE"]` |
| `image_config` | `Optional[ImageConfig]` | Validado por `field_validator`; aceita instância ou dict compatível |
| `thinking_config` | `Optional[ThinkingConfig]` | Ver abaixo |
| `tools` | — | `google_search` para grounding |
| `safety_settings` | — | Mutuamente exclusivo com `model_armor_config` |
| `media_resolution` | `Optional[MediaResolution]` | Resolução da mídia **de entrada** |

Sobre `response_modalities`, literal `[CB]`:

> You can set the `response_modalities` to indicate to the model that you are expecting text and images in the output but it's optional as this is expected with this model. If you just want an image and don't need text, you can set `response_modalities=['Image']`.

**Ressalva importante `[CB]`**, no exemplo de grounding: `response_modalities=['Text', 'Image']` com o comentário inline

> `# Image only currently doesn't wortk with grounding`

Ou seja: ao usar Google Search, `IMAGE` sozinho não funciona — é preciso `['Text', 'Image']`. O cliente de E5 precisa aplicar essa regra automaticamente quando grounding estiver ligado, senão a chamada falha silenciosamente em produzir imagem.

## `types.ThinkingConfig`

Enum `ThinkingLevel` `[SDK]`, valores exatos:

`THINKING_LEVEL_UNSPECIFIED`, `MINIMAL`, `LOW`, `MEDIUM`, `HIGH`

```python
thinking_config=types.ThinkingConfig(
    thinking_level="High",
    include_thoughts=True   # necessário para inspecionar os pensamentos depois
)
```

Literal `[CB]` sobre custo:

> Note that you are paying for the thought token (but not the images in them) as output tokens (cf. pricing).

O notebook anota `thinking_level` como *"Only for Nano-Banana 2"* no exemplo, embora descreva o thinking como capacidade de ambos os modelos Gemini 3. Divergência interna à fonte, registrada em `05-divergencias-e-lacunas.md`.

## Tools — grounding

Forma curta `[CB]`:

```python
tools=[{"google_search": {}}]
```

Forma tipada, com busca de imagens (exclusiva do NB 2) `[CB]`:

```python
tools=[
    types.Tool(google_search=types.GoogleSearch(
        search_types=types.SearchTypes(
            web_search=types.WebSearch(),
            image_search=types.ImageSearch()
        )
    ))
]
```

Literal `[CB]`, duas restrições que importam para este repositório:

> Note that it only ground using the text results and not the images that could be found using Google Search.

> Note that you can't look for people images.

A segunda é uma barreira nativa contra a busca de imagens de pessoas reais e reforça a política de conteúdo.

## Marca d'água

O campo `add_watermark` existe no `[SDK]`, mas em `GenerateImagesConfig` e nas configs de referência — isto é, no caminho **Imagen**, não em `ImageConfig`. Docstring literal `[SDK]`: *"Whether to add a SynthID watermark to the generated images."*

Não há campo de marca d'água em `ImageConfig`. Combinado com o `[BLOG]`, que lista *"C2PA Content Credentials + SynthID watermark"* como característica dos modelos Nano Banana, a leitura é que nos modelos Gemini de imagem a marca d'água é **aplicada automaticamente e não configurável**. Essa leitura é inferência, não citação: marcada `[NÃO VERIFICADO]` em `05-divergencias-e-lacunas.md`.
