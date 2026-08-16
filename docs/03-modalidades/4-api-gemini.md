# Modalidade 4 — API Gemini

`client.models.generate_content(...)` do `google-genai`, com `ImageConfig` para proporção e resolução, `include_thoughts` para diagnóstico, e chat multi-turno para consistência de personagem. É a modalidade de produção pelo caminho Gemini nativo, e a única que atinge 4K com auditoria e 14 referências.

## Envelope da chamada

Contrato do SDK em `[SDK]` (`googleapis/python-genai`, `google/genai/types.py`) e da API em `[GAI]`. O renderizador devolve:

```python
{
  "sdk":   "google-genai",
  "model": "gemini-3-pro-image",
  "contents": "<corpo em blocos>\n\nAVOID: ...",
  "config": {
    "response_modalities": ["IMAGE"],
    "image_config": {
      "aspect_ratio": "4:5",
      "image_size":   "2K"
    }
  }
}
```

Executado em Python:

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-pro-image",
    contents="<corpo em blocos>\n\nAVOID: ...",
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="4:5",
            image_size="2K",
        ),
    ),
)
```

## Autenticação

`GEMINI_API_KEY` no ambiente. O `Client()` lê a variável automaticamente. Nenhuma outra credencial é necessária para geração de imagem básica.

## `ImageConfig` — os campos que interessam nesta modalidade

`[SDK]`, `types.py`:

| Campo | Tipo | Uso |
|---|---|---|
| `aspect_ratio` | `Optional[str]` | Dez valores em `[GAI]`; docstring do SDK lista oito e está desatualizada — D1 |
| `image_size` | `Optional[str]` | `"1K"`, `"2K"`, `"4K"`. **Default do sistema: `"2K"`** — decisão travada, ver `06-fonte-primaria-ai-google-dev.md`, seção 3 |
| `person_generation` | `Optional[str]` | `"allow_all"`, `"allow_adult"`, `"dont_allow"`. Default e comportamento exatos são lacuna L3 |

Os demais campos de `ImageConfig` são exclusivos do caminho Imagen/Vertex e não usados aqui — ver `02-parametros-sdk.md`.

## Resolução — o único caminho para 4K auditável

`[GAI]`, tabela de preços do `gemini-3-pro-image`:

| Resolução | Tokens | USD por imagem |
|---|---|---|
| 1K | 1120 | $0,134 |
| **2K** | **1120** | **$0,134** |
| 4K | 2000 | $0,24 |

**1K e 2K custam o mesmo.** Pedir 1K é pagar 2K e receber metade — o sistema nunca faz. 4K custa 79% a mais e é reservado a entregas que realmente ampliam.

**Batch e Flex cortam o custo pela metade** ($0,067 em 1K/2K, $0,12 em 4K). Geração de variantes em lote — bateria de validação da E7, sweeps de doutrina da E6 — deve usar o caminho Batch.

## Referências — 14 por chamada, 5 de identidade

O `[SDK]` **não expõe campo de identidade** em `ImageConfig`. As referências entram como itens da lista `contents`, ao lado do texto:

```python
import PIL.Image

response = client.models.generate_content(
    model="gemini-3-pro-image",
    contents=[
        "<corpo em blocos>\n\nAVOID: ...",
        PIL.Image.open("ref-1.jpg"),
        PIL.Image.open("ref-2.jpg"),
    ],
    config=...
)
```

Orçamentos por papel `[GAI]`, para `gemini-3-pro-image`:

| Papel | Teto |
|---|---|
| Personagens (identidade) | **5** — decisão travada no ESTADO |
| Objetos alta fidelidade | 6 |
| Estilo | 3 |
| Total por chamada | 14 |

A **separação entre invariante e variável fica na prosa do prompt**, não em parâmetro — porque não há parâmetro. É a razão de existir a seção 5 da doutrina.

## Diagnóstico — `include_thoughts` e o loop da E6

O Gemini 3 pensa antes de gerar `[CB]`. Os pensamentos são inspecionáveis:

```python
config = types.GenerateContentConfig(
    response_modalities=["IMAGE"],
    image_config=types.ImageConfig(aspect_ratio="4:5", image_size="2K"),
    thinking_config=types.ThinkingConfig(include_thoughts=True),
)

for part in response.parts:
    if part.thought:
        print("[THOUGHT]", part.text)
    elif part.inline_data:
        # bytes da imagem
        ...
```

**Isso é instrumento direto para o loop da E6.** Quando uma imagem sai com aparência sintética, os pensamentos revelam como o modelo interpretou a especificação física — permitindo separar "o prompt estava ambíguo" de "o modelo ignorou a instrução".

`thinking_level` foi introduzido pelo Nano Banana 2 (D3, ver `05-divergencias-e-lacunas.md`) e **não** deve ser usado no caminho Pro. `include_thoughts` funciona nos dois.

## Chat multi-turno — consistência de personagem

`client.chats` preserva *thought signatures* entre turnos `[CB]`, o que carrega mais estado que uma sequência de chamadas unárias:

```python
chat = client.chats.create(model="gemini-3-pro-image")

r1 = chat.send_message([text_prompt_turno_1])
salvar_imagem(r1, "gen-1.png")

r2 = chat.send_message([
    "Same subject, three-quarter turn to camera-right",
    PIL.Image.open("gen-1.png"),   # realimenta a geração anterior
])
```

Padrão canônico `[GAI]`, seção "Character consistency: 360 view": **realimentar a saída aprovada do turno anterior como referência do turno seguinte**. Não regenerar cada quadro a partir da referência original — a deriva se acumula.

Regra derivada em `docs/01-doutrina-hiper-realismo.md`, seção 5.

## Marca d'água

Toda imagem sai com SynthID e não é configurável, literal `[GAI]`: *"All generated images include a SynthID watermark."* Confirmado duas vezes na página primária. Se aparecer `no watermark` na cauda `AVOID`, o item 7 do checklist reprova — a cauda existe para modos de falha de renderização, e SynthID não é modo de falha.

## Exemplo ponta a ponta

Instância: `schemas/exemplos/exemplo-1-retrato-estudio.json`.
Payload renderizado: `exemplos/exemplo-1-retrato-estudio-mod4.json`.

Chamada completa executável (modo simulação — não requer `GEMINI_API_KEY`):

```python
# schemas/exemplos/exemplo-1-retrato-estudio-mod4.json contém:
# {
#   "sdk":   "google-genai",
#   "model": "gemini-3-pro-image",
#   "contents": "Editorial studio portrait, single subject, waist-up.\n\nSUBJECT. ...\n\nAVOID: ...",
#   "config": {
#     "response_modalities": ["IMAGE"],
#     "image_config": { "aspect_ratio": "4:5", "image_size": "2K" }
#   }
# }
```

## Limites que só esta modalidade toca

- **4K auditável** — `image_size="4K"` no `ImageConfig`. As demais modalidades ou verbalizam ou não expõem.
- **14 referências totais** — teto absoluto do modelo. Modalidade 3 limita a 8 pelo endpoint da Higgsfield.
- **Pensamentos inspecionáveis** — `include_thoughts=True`. Só aqui.
- **Estado de chat multi-turno** — *thought signatures* preservadas entre turnos. Só aqui.
- **Preço declarado por resolução** — 1K/2K a $0,134, 4K a $0,24 (Batch: $0,067 e $0,12). Auditoria fina de custo só pelo caminho Gemini.

## O que fica para a E5

Esta página descreve o **envelope da chamada**. A E5 constrói o **cliente**: retries com backoff exponencial, `include_thoughts` opcional, modo simulação sem `GEMINI_API_KEY` (imprime o payload), leitura de resposta que trata múltiplas imagens (`[CB]`: *"there could be multiple images so you cannot stop at the first one"*), e o registro em `runs/` que a E6 consome.
