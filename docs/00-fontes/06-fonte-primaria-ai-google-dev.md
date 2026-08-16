# Fonte primária `ai.google.dev` — extração tardia

Etiqueta de origem: **`[GAI]`**.

A E0 foi executada com `ai.google.dev` bloqueado no egress e reconstruiu o conteúdo equivalente por rotas alternativas. Em **2026-08-16**, na validação de rede de abertura de sessão, o host passou a responder `200`. Esta página é a extração da fonte primária que faltava, feita antes da E1 para que a doutrina fosse derivada da autoridade correta e não da paráfrase.

Páginas lidas na íntegra:

| URL | Código | Conteúdo |
|---|---|---|
| `https://ai.google.dev/gemini-api/docs/image-generation` | 200 | Guia de geração de imagem, limites, guia de prompts, boas práticas, limitações |
| `https://ai.google.dev/gemini-api/docs/pricing` | 200 | Tabela de preços por modelo |

Pela hierarquia do prompt-mestre, `[GAI]` é **documentação primeiro-parte** e portanto autoridade para capacidades, limites e preços — acima de `[CB]` e `[BLOG]` nesses três domínios, e abaixo de `[SDK]` para nomes e tipos de parâmetro.

---

## 1. Os quatro modelos Nano Banana

Literal `[GAI]`:

> Nano Banana refers to four distinct models available in the Gemini API:
>
> - **Nano Banana 2 Lite (Gemini 3.1 Flash Lite Image)** (`gemini-3.1-flash-lite-image`): Our fastest and cheapest Gemini image model, engineered for velocity and scale where speed and cost are the primary operational constraints. Not optimized for multiple reference inputs or multi-turn sequential editing.
> - **Nano Banana 2 (Gemini 3.1 Flash Image)** (`gemini-3.1-flash-image`): Serves as the most versatile model, generalist workhorse model for all tasks. It balances speed with state-of-the-art 4K generation, world knowledge, and reliable text rendering. Excelling at multiple reference image processing and consistency.
> - **Nano Banana Pro (Gemini 3 Pro Image)** (`gemini-3-pro-image`): The premium choice for the most complex visual tasks, offering the highest level of world knowledge, advanced localization, accurate brand consistency, and precision creative control.
> - **Nano Banana (Gemini 2.5 Flash Image)** (`gemini-2.5-flash-image`): The legacy pioneer of the Nano Banana series. While it has been a reliable workhorse, we strongly recommend that customers transition to Nano Banana 2 Lite […]

Isto **fecha a lacuna L6**: `gemini-3.1-flash-lite-image` é o Nano Banana 2 Lite, e a própria documentação o desqualifica para o nosso caminho principal — *"not optimized for multiple reference inputs or multi-turn sequential editing"* são exatamente os dois usos centrais deste repositório.

Confirma também a correspondência de nomes que o prompt-mestre mandou resolver com as fontes: **"Nano Banana Pro" é o nome de produto, `gemini-3-pro-image` é o identificador aceito pela API.**

## 2. Referências por papel — o número que importa

Literal `[GAI]`, seção *"Use up to 14 reference images"*:

> Gemini 3 image models let you to mix up to 14 reference images. These 14 images can include the following:

| | Gemini 3.1 Flash Lite Image | Gemini 3.1 Flash Image | **Gemini 3 Pro Image** |
|---|---|---|---|
| Objetos em alta fidelidade | Up to 14 | Up to 10 | **Up to 6** |
| Personagens para consistência | N/A | Up to 4 | **Up to 5** |
| Referências de estilo | N/A | N/A | **Up to 3** |

Literal `[GAI]`, seção *"Limitations"*:

> `gemini-2.5-flash-image` works best with up to 3 images as input, while `gemini-3-pro-image` supports 5 images with high fidelity, and up to 14 images in total. `gemini-3.1-flash-image` supports character resemblance of up to 4 characters and the fidelity of up to 10 objects in a single workflow.

**Leitura.** Os três orçamentos somam exatamente o teto declarado: 6 + 5 + 3 = 14. O "14" nunca foi um teto único e indiferenciado — é a soma de três orçamentos com papéis distintos. A prosa de *Limitations* diz "5 images with high fidelity" onde a tabela diz 6 objetos; a leitura conciliadora é que o número citado na prosa é o de personagens, que é o caso de uso que a frase seguinte discute.

**Consequência direta para este repositório.** O teto para consistência de identidade é **5**, não 6. O 6 é o orçamento de objetos. Isso corrige a decisão travada no ESTADO, que fixou 6 para identidade com base em `[CB]`. Ver `05-divergencias-e-lacunas.md`, D2.

## 3. Preço — lacuna crítica L1 resolvida

Literal `[GAI]`, tabela de `gemini-3-pro-image`, camada **Standard**, por 1M de tokens em USD:

| Item | Valor |
|---|---|
| Input | `$2.00` (texto/imagem) — equivalente a `$0.0011` por imagem de entrada |
| Output — texto e thinking | `$12.00` |
| Output — imagens | `$120.00` |
| **Equivalente por imagem 1K/2K** | **`$0.134`** |
| **Equivalente por imagem 4K** | **`$0.24`** |

Notas de rodapé literais `[GAI]`:

> \* Image input is set at 560 tokens or $0.0011 per image.
>
> \*\* Image output is priced at $120 per 1,000,000 tokens. Output images from 1024x1024px (1K) and up to 2048x2048px (2K) consume 1120 tokens and are equivalent to $0.134 per image. Output images up to 4096x4096px (4K) consume 2000 tokens and are equivalent to $0.24 per image.

Demais camadas de serviço:

| Camada | Imagem 1K/2K | Imagem 4K | Input | Output texto |
|---|---|---|---|---|
| Standard | `$0.134` | `$0.24` | `$2.00` | `$12.00` |
| Batch | `$0.067` | `$0.12` | `$1.00` texto / `$0.0006` imagem | `$6.00` |
| Flex | `$0.067` | `$0.12` | `$1.00` texto / `$0.0006` imagem | `$6.00` |
| Priority | — (`$216.00`/1M) | — | `$3.60` | `$21.60` |

**Três consequências operacionais.**

1. **1K e 2K custam o mesmo.** Ambas consomem 1120 tokens. Não existe economia em pedir 1K: a resolução padrão do sistema deve ser **2K**, e 1K só se houver restrição de banda ou armazenamento a jusante. Registrar em E3 como default do renderizador.
2. **4K custa 79% a mais** (`$0.24` contra `$0.134`) e consome 2000 tokens. Reservado a entregas que realmente ampliam — impressão, banner de grande formato.
3. **Batch e Flex cortam o custo pela metade.** Geração em lote de variantes de template — o caso típico da E4 e da bateria de validação da E7 — deve usar Batch.

**Nota de disciplina.** A E0 registrou que o valor `$0,134` havia circulado num resultado de busca de terceiro e o **recusou** por não ser primeiro-parte. O valor estava correto. A recusa continua tendo sido a decisão certa: o acerto de um palpite não o transforma retroativamente em fonte, e o custo de estar errado sobre preço é maior que o custo de declarar uma lacuna.

## 4. Dimensões em pixel do `gemini-3-pro-image`

Literal `[GAI]`, extrato da tabela do modelo Pro:

| Proporção | 1K | tokens | 2K | tokens | 4K | tokens |
|---|---|---|---|---|---|---|
| `1:1` | 1024×1024 | 1120 | 2048×2048 | 1120 | 4096×4096 | 2000 |
| `4:5` | **928×1152** | 1120 | 1856×2304 | 1120 | 3712×4608 | 2000 |
| `5:4` | 1152×928 | 1120 | 2304×1856 | 1120 | 4608×3712 | 2000 |
| `16:9` | 1376×768 | 1120 | 2752×1536 | 1120 | 5504×3072 | 2000 |

**Fecha a divergência D1.** `4:5` é suportado e rende 928×1152 em 1K — exatamente o valor que `[CB]` afirmava e que a docstring do `[SDK]` omitia. O exemplo âncora de calibração do prompt-mestre, que usa `4:5`, está validado por fonte primária.

## 5. Marca d'água

Literal `[GAI]`, afirmado duas vezes na página — no cabeçalho dos modelos e na lista de limitações:

> All generated images include a SynthID watermark.

Afirmação universal e sem cláusula de configuração, numa página que documenta exaustivamente os parâmetros configuráveis. Combinado com a ausência de campo de marca d'água em `ImageConfig` `[SDK]`, **a lacuna L2 passa de inferência a apoiada por citação direta**. Permanece sem confirmação apenas a impossibilidade formal de desativação, que nenhuma fonte afirma nem nega.

## 6. Guia de prompts oficial — texto literal

Fecha a **lacuna L4**: o material que a E0 marcou `[WS]` (paráfrase de busca) agora é citação verificada.

### Template fotorrealista, literal `[GAI]`

> A photorealistic [type of shot] of a [subject description] in a [setting description]. [Description of the light]. Shot from a [camera angle] with a [lens type].

Prompt de exemplo literal `[GAI]`:

> A photorealistic wide-angle shot of a vibrant coral reef teeming with tropical fish. Crystal-clear turquoise water with sunbeams filtering down from the surface, illuminating a sea turtle gliding gracefully over the coral. Shot from a low perspective with a wide-angle lens. Aspect ratio 16:9.

**A E0 rejeitou este template e a rejeição se mantém, agora contra o texto literal em vez de paráfrase.** O template abre com o termo `photorealistic`, que o prompt-mestre proíbe, e sua especificação de luz e óptica é um slot de texto livre — *"[Description of the light]"*, *"[lens type]"* — sem exigir tamanho de fonte, distância, azimute, temperatura de cor ou trio de exposição coerente. É um template de entrada, adequado ao usuário genérico. A doutrina deste repositório é um superconjunto estrito dele: tudo que ele pede, mais a cadeia física fechada. Ver a justificativa completa em `docs/01-doutrina-hiper-realismo.md`, seção "Por que o adjetivo não funciona".

### Preservação de detalhe em alta fidelidade, literal `[GAI]`

> Using the provided images, place [element from image 2] onto [element from image 1]. Ensure that the features of [element from image 1] remain completely unchanged. The added element should [description of how the element should integrate].

Este template **valida a gramática de edição do exemplo 3 do prompt-mestre**: declaração do que permanece inalterado antes da alteração, e instrução explícita de integração.

### Consistência de personagem, literal `[GAI]`

> **7. Character consistency: 360 view**
>
> You can generate 360-degree views of a character by iteratively prompting for different angles. For best results, include previously generated images in subsequent prompts to maintain consistency. For complex poses, include a reference image of the selected pose.

Confirma em fonte primária o padrão que `[CB]` demonstrava por código: **realimentar a geração anterior como referência do turno seguinte**.

### Boas práticas, literal `[GAI]`

> - **Be hyper-specific**: The more detail you provide, the more control you have. Instead of "fantasy armor," describe it: "ornate elven plate armor, etched with silver leaf patterns, with a high collar and pauldrons shaped like falcon wings."
> - **Provide context and intent**: Explain the purpose of the image. The model's understanding of context will influence the final output.
> - **Iterate and refine**: Don't expect a perfect image on the first try. Use the conversational nature of the model to make small changes.
> - **Use step-by-step instructions**: For complex scenes with many elements, break your prompt into steps.
> - **Use "semantic negative prompts"**: Instead of saying "no cars," describe the intended scene positively: "an empty, deserted street with no signs of traffic."
> - **Control the camera**: Use photographic and cinematic language to control the composition. Terms like `wide-angle shot`, `macro shot`, `low-angle perspective`.

Duas dessas colidem em aparência com decisões já travadas, e a resolução vai na doutrina:

- *"Provide context and intent"* justifica em fonte primária a linha `CAPTURE REALITY` dos exemplos âncora ("this is a single working frame from a commercial session"), que declara intenção em vez de descrever pixels.
- *"Use semantic negative prompts"* parece condenar a cauda `AVOID`. Não condena: a recomendação é sobre **conteúdo de cena** ("no cars"), que de fato deve ser formulado positivamente. A cauda `AVOID` do repositório não lista conteúdo de cena, lista **modos de falha de renderização** (CGI, pele aerografada, mãos malformadas), que não têm formulação positiva equivalente. A regra fica registrada na doutrina como critério de admissão à cauda.

## 7. Limitações declaradas

Literal `[GAI]`:

> - For best performance, use the following languages: EN, ar-EG, de-DE, es-MX, fr-FR, hi-IN, id-ID, it-IT, ja-JP, ko-KR, **pt-BR**, ru-RU, ua-UA, vi-VN, zh-CN.
> - Image generation does not support audio inputs. Video inputs are only supported for Gemini 3.1 Flash Image.
> - The model won't always follow the exact number of image outputs that the user explicitly asks for.
> - When generating text for an image, Gemini works best if you first generate the text and then ask for an image with the text.
> - `gemini-3.1-flash-image` Grounding with Google Search does not support using real-world images of people from web search at this time.
> - All generated images include a SynthID watermark.

Dois itens com consequência de projeto:

1. **`pt-BR` está na lista de idiomas suportados.** A decisão travada de emitir prompts em inglês não é, portanto, uma exigência do modelo — é escolha de consistência com as fontes e com o vocabulário técnico de fotografia. A decisão permanece; o que muda é que agora ela é justificada por conveniência, não por necessidade, e isso deve ser dito honestamente na documentação.
2. **Texto antes de imagem.** Para templates com tipografia legível — o mostrador do relógio do exemplo 4, rótulos de embalagem — a ordem recomendada é gerar o texto primeiro e depois pedir a imagem que o contém. Entra como nota de implementação nos templates de produto da E4.

## 8. Superfície de chamada e defaults

Literal `[GAI]`, sobre proporção e tamanho:

> By default, the model matches the output image size to that of your input image, or otherwise generates 1:1 squares. You can control the aspect ratio and the size of the output image using the `aspect_ratio` and `image_size` fields under `response_format` when `type` is set to `"image"`.

Forma literal `[GAI]` na API de Interactions:

```python
response_format = {"type": "image", "aspect_ratio": "16:9", "image_size": "2K"}
```

**Dois defaults que precisam ser tratados explicitamente pelo código da E5:**

- Em **edição** a partir de imagem ancorada, o tamanho de saída herda o da entrada. É o comportamento desejado no exemplo 3 do prompt-mestre — troca de fundo preservando o enquadramento — mas precisa ser default consciente, não acidente.
- Em **geração** sem referência, o default é `1:1`. Nenhum template hiper-realista deste repositório deve aceitar esse default por omissão; proporção é campo de pergunta obrigatória pela regra de pedidos subespecificados.

Nota de reconciliação para E3/E5: `[GAI]` documenta os parâmetros de imagem sob `response_format` na superfície `client.interactions.create`, enquanto `[SDK]` os documenta em `types.ImageConfig` sob `client.models.generate_content`. As duas superfícies já estavam registradas em `02-parametros-sdk.md`. Não há divergência de valor — há duas superfícies com nomenclatura própria, e o cliente da E5 precisa escolher uma e documentar a escolha.

## 9. O que continua em aberto

| Item | Estado após esta extração |
|---|---|
| L1 — preço | **Resolvida.** Fonte primária, valores acima |
| L2 — marca d'água | **Resolvida em substância.** Citação direta e universal; só a impossibilidade formal de desativação segue sem afirmação |
| L3 — default de `person_generation` | **Aberta.** Não documentado nesta página. Só resolve por teste empírico |
| L4 — guia de prompts | **Resolvida.** Texto literal acima |
| L5 — Higgsfield | **Aberta, mas destravada.** Hosts respondem desde 2026-08-16. Extração pertence à E5 |
| L6 — `gemini-3.1-flash-lite-image` | **Resolvida.** Nano Banana 2 Lite, desqualificado para o caminho principal |
