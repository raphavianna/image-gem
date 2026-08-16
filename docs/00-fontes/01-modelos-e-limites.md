# Modelos, limites e geometria de saída

## Correspondência nome comercial ↔ identificador de API

O prompt-mestre pediu que esta correspondência fosse resolvida por fonte, não por memória. Resolvida `[CB]`, com o notebook oficial listando os três nomes lado a lado:

| Nome comercial | Identificador aceito pela API | Família | Origem |
|---|---|---|---|
| **Nano Banana Pro** | `gemini-3-pro-image` | Gemini 3 Pro | `[CB]`, `[VTX-NB]`, `[BLOG]` |
| Nano Banana 2 | `gemini-3.1-flash-image` | Gemini 3.1 Flash | `[CB]`, `[BLOG]` |
| Nano Banana | `gemini-2.5-flash-image` | Gemini 2.5 Flash | `[CB]` |
| — (sem nome comercial documentado) | `gemini-3.1-flash-lite-image` | Gemini 3.1 Flash Lite | `[CB]` — aparece apenas na lista de seleção do notebook, sem descrição |

Citação literal `[CB]`:

> * `gemini-2.5-flash-image` aka. "nano-banana": Cheap and fast yet powerful. This should be your default choice.
> * `gemini-3-pro-image` aka "nano-banana-pro": More powerful thanks to its **thinking** capabilities and its access to real-wold data using **Google Search**. It really shines at creating diagrams and grounded images. And cherry on top, it can create 2K and 4K images!
> * `gemini-3.1-flash-image` aka. "nano-banana-2": The best balance between speed and quality, with new capabilities like **Search Grounding**, **Thinking**, and a new **512p** resolution.

**Modelo alvo deste repositório: `gemini-3-pro-image`.** É o único dos três que o usuário nomeou, e o `[BLOG]` o posiciona como o de maior capacidade de raciocínio. `gemini-3.1-flash-image` fica documentado como alternativa de custo e latência.

## Especificações por modelo

Fonte `[BLOG]`, tabela de especificações. Onde `[CB]` confirma, está anotado.

| Aspecto | `gemini-3-pro-image` (NB Pro) | `gemini-3.1-flash-image` (NB 2) |
|---|---|---|
| Janela de contexto | 65.536 tokens | 131.072 tokens |
| Tokens de saída | 32.768 | 32.768 |
| Resoluções | 1K, 2K, 4K — confirmado `[CB]` | 512px, 1K, 2K, 4K — confirmado `[CB]` |
| Proporções | 10 valores (tabela abaixo) | as 10 + `1:4`, `4:1`, `1:8`, `8:1` |
| Imagens de referência | até 14 | até 14 |
| Formatos de entrada | PNG, JPEG, WebP, HEIC, HEIF | idem |
| Tamanho de documento | 50 MB via API/Cloud Storage; 7 MB em upload direto | idem |
| Corte de conhecimento | Janeiro 2025 | Janeiro 2025 |
| Google Search | Sim | Sim, incluindo busca de imagens |
| Procedência | C2PA Content Credentials + marca d'água SynthID | idem |

Nota sobre a janela de contexto: o NB Pro tem **metade** da janela do NB 2 (65.536 contra 131.072). Isso é contraintuitivo e tem consequência direta no orçamento de densidade de E2 — prompts muito longos combinados com várias imagens de referência em alta resolução consomem essa janela. Vale medir na prática antes de tratar como irrelevante.

## Proporções e dimensões exatas em pixels

Tabela literal `[CB]`. É a fonte mais precisa encontrada: dá o pixel exato por combinação proporção × resolução, o que nenhuma outra fonte fornece.

| Proporção | 512px | 1K | 2K | 4K |
|---|---|---|---|---|
| **1:1** | 512×512 | 1024×1024 | 2048×2048 | 4096×4096 |
| **2:3** | 424×632 | 848×1264 | 1696×2528 | 3392×5056 |
| **3:2** | 632×424 | 1264×848 | 2528×1696 | 5056×3392 |
| **3:4** | 448×600 | 896×1200 | 1792×2400 | 3584×4800 |
| **4:3** | 600×448 | 1200×896 | 2400×1792 | 4800×3584 |
| **4:5** | 464×576 | 928×1152 | 1856×2304 | 3712×4608 |
| **5:4** | 576×464 | 1152×928 | 2304×1856 | 4608×3712 |
| **9:16** | 384×688 | 768×1376 | 1536×2752 | 3072×5504 |
| **16:9** | 688×384 | 1376×768 | 2752×1536 | 5504×3072 |
| **21:9** | 792×336 | 1584×672 | 3168×1344 | 6336×2688 |
| `1:4` (NB2) | 256×1024 | 512×2048 | 1024×4096 | 2048×8192 |
| `4:1` (NB2) | 1024×256 | 2048×512 | 4096×1024 | 8192×2048 |
| `1:8` (NB2) | 192×1536 | 384×3072 | 768×6144 | 1536×12288 |
| `8:1` (NB2) | 1536×192 | 3072×384 | 6144×768 | 12288×1536 |

As quatro últimas linhas são exclusivas do NB 2. As dez primeiras valem para o NB Pro.

**Custo em tokens é independente da proporção** — depende apenas do modelo e da resolução `[CB]`, afirmado duas vezes no notebook:

> Note that the number of tokens stays the same for all aspect ratio and depends only on the model and the resolution.

Consequência prática: escolher `21:9` em vez de `1:1` não custa mais caro. Escolher 4K em vez de 1K custa.

## Comportamento padrão da proporção

Literal `[CB]`:

> The model's primary behavior is to match the size of your input images; otherwise, it defaults to generating square (1:1) images.

Isso importa para a modalidade de edição: ao passar uma imagem de referência **sem** declarar `aspect_ratio`, a saída herda a proporção da entrada. Em geração pura sem referência, o default é `1:1` — que quase nunca é o desejado em retrato. O renderizador de E3 deve sempre declarar a proporção explicitamente em vez de confiar no default.

## Uma nota sobre 4:5

`4:5` e `5:4` aparecem na tabela de dimensões `[CB]` e na lista de proporções `[BLOG]`, mas **estão ausentes** da docstring do campo `aspect_ratio` no `[SDK]`. Divergência registrada em `05-divergencias-e-lacunas.md`. Relevante porque o exemplo âncora de calibração do prompt-mestre usa `4:5`.
