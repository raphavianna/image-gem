# Fonte primária Higgsfield — extração para a E3

Etiqueta de origem: **`[HF]`**.

A E0 registrou a Higgsfield como bloco `L5`, sem extração possível: todos os hosts respondiam com CONNECT recusado. Em 2026-08-16 a política de rede mudou para `Custom` e `docs.higgsfield.ai` passou a responder `200`. A extração pertencia à E5 pelo plano original, mas foi antecipada para a E3 porque a modalidade 2 (interface Higgsfield) e a modalidade 3 (conector) dependem dela para não virarem stub.

Páginas lidas na íntegra:

| URL | Uso |
|---|---|
| `https://docs.higgsfield.ai/docs/llms.txt` | Índice canônico |
| `https://docs.higgsfield.ai/docs/index.md` | Visão geral |
| `https://docs.higgsfield.ai/docs/quickstart.md` | Ciclo completo submit → poll → completed |
| `https://docs.higgsfield.ai/docs/authentication.md` | Esquema de credencial |
| `https://docs.higgsfield.ai/docs/guides/images.md` | Guia de imagem |
| `https://docs.higgsfield.ai/docs/concepts/requests.md` | Estados terminais |
| `https://docs.higgsfield.ai/docs/concepts/polling.md` | Estratégia de polling |
| `https://docs.higgsfield.ai/docs/concepts/errors.md` | Tabela HTTP → ação |
| `https://docs.higgsfield.ai/docs/concepts/rate-limits.md` | Concorrência |
| `https://docs.higgsfield.ai/docs/concepts/billing-and-retention.md` | Estimativa e retenção |
| `https://docs.higgsfield.ai/docs/concepts/file-uploads.md` | Fluxo presigned URL |
| `https://docs.higgsfield.ai/docs/how-to/sdk.md` | SDKs Python e TypeScript |
| `https://docs.higgsfield.ai/docs/how-to/webhooks.md` | Notificação assíncrona |
| `https://docs.higgsfield.ai/docs/api-reference/overview.md` | Referência |
| `https://docs.higgsfield.ai/docs/openapi.json` | Contrato executável de 50 endpoints |

Pela hierarquia do prompt-mestre, `[HF]` é documentação primeiro-parte e OpenAPI executável — autoridade máxima para os endpoints, parâmetros e limites da Higgsfield.

---

## 1. Correções ao ESTADO

Duas linhas do ESTADO estavam construídas sobre suposição. A extração desfez as duas.

**Credencial não é `refresh_token`.** É par **API key ID + secret** literal `[HF]`:

> Send both values in the `Authorization` header:
>
> `Authorization: Key YOUR_KEY_ID:YOUR_KEY_SECRET`

Legado: os cabeçalhos `hf-api-key` e `hf-secret` ainda são aceitos, mas a documentação diz explicitamente que **integrações novas devem usar `Authorization`**. Consequência: a pendência do ESTADO passa a ser "credenciais Higgsfield (`HF_API_KEY_ID` + `HF_API_KEY_SECRET`)".

**Modelo Nano Banana Pro é acessível na Higgsfield.** O prompt-mestre assumia isso mas não confirmava. O OpenAPI mostra endpoint dedicado `POST /nano-banana`, com aspect ratios idênticos aos da Gemini API. A questão de qual variante (Pro ou Flash) o endpoint mapeia por trás não é respondida por essa documentação — a Higgsfield o expõe como um único `/nano-banana` sem distinção de tier. **Fica como lacuna L7**, resolvível empiricamente com credencial.

## 2. Endpoint Nano Banana — contrato executável

Do OpenAPI, `POST /nano-banana`:

```json
{
  "type": "object",
  "properties": {
    "prompt":       { "type": "string", "title": "Prompt" },
    "num_images":   { "type": "integer", "default": 1, "minimum": 1, "maximum": 4 },
    "aspect_ratio": {
      "type": "string", "default": "4:3",
      "enum": ["auto","1:1","4:3","3:4","3:2","2:3","5:4","4:5","16:9","9:16","21:9"]
    },
    "input_images": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/ImageUrlInputImageSchema" },
      "minItems": 0, "maxItems": 8
    },
    "output_format":{ "type": "string", "enum": ["jpeg","png"], "default": "jpeg" }
  },
  "required": ["prompt"]
}
```

Onde `ImageUrlInputImageSchema` é:

```json
{ "type": "object", "additionalProperties": false,
  "properties": {
    "type":      { "type": "string", "const": "image_url" },
    "image_url": { "type": "string", "format": "uri" }
  },
  "required": ["type","image_url"]
}
```

### Consequências operacionais para as modalidades 2 e 3

**Aspect ratio `auto` é bônus.** A Higgsfield oferece um valor a mais que a Gemini API — `auto`, que herda do input. Útil para edição a partir de imagem ancorada. Os outros dez valores são os mesmos do `[GAI]`.

**Sem campo `resolution` no `/nano-banana`.** A Gemini API expõe 1K, 2K e 4K explicitamente e cobra diferente por resolução. A Higgsfield abstrai — a resolução é decidida internamente. Consequência dura para nossa doutrina: a **decisão travada de "2K como default"** não é enforceable na modalidade 2 nem na 3, porque o parâmetro simplesmente não existe. Prompts que precisem de 4K auditável devem ir pela modalidade 4.

Nota comparativa: o endpoint `/higgsfield-ai/soul/standard` (o modelo SOUL, próprio da Higgsfield) expõe `resolution: [2K, 4K]`. A omissão em `/nano-banana` é decisão específica desse endpoint, não limitação da API.

**Teto de referências: 8, não 14.** A Higgsfield limita `input_images` a 8, contra 14 do modelo nativo. Fica bem acima do nosso teto operacional de 5 para identidade — a doutrina passa sem alteração. O que muda é que templates de composição multi-referência têm limite mais apertado quando roteados pela Higgsfield.

**No máximo 4 imagens de saída por chamada** (`num_images` máx=4).

**Referências entram como URL, não como bytes.** Uploads locais precisam passar pelo fluxo de presigned URL (`POST /files/generate-upload-url`) antes de virar `input_images[].image_url`. A E5 esconde esse detalhe atrás do cliente; a documentação de E3 registra que existe.

## 3. Modelo assíncrono e ciclo de vida

Fluxo canônico, literal `[HF]`:

```
POST /nano-banana         →  { status: "queued", request_id, status_url, cancel_url }
GET  {status_url}          →  { status: "in_progress", ... }
GET  {status_url}          →  { status: "completed", images: [{ url }] }
```

Estados possíveis do `status`:

| Status | Terminal | Significado |
|---|---|---|
| `queued` | não | Aguardando início; pode ser cancelado |
| `in_progress` | não | Geração iniciada; não pode mais ser cancelado |
| `completed` | sim | URLs em `images[]`, `video`, `audio` etc. conforme o modelo |
| `failed` | sim | Falha na geração; `error` pode explicar |
| `nsfw` | sim | Bloqueio por moderação de conteúdo |
| `canceled` | sim | Cancelado antes do processamento iniciar |

**Estratégia de polling recomendada** `[HF]`: começar com intervalo de 2s, subir gradualmente até 10s, adicionar jitter, parar em estado terminal. Fica implementada assim na modalidade 3.

**Cancelamento.** `POST /requests/{request_id}/cancel` só funciona enquanto o job está `queued`. Depois retorna `400`.

**Retenção.** Literal `[HF]`: *"Output URLs are retained for at least seven days. Copy completed media to your own storage if you need it for longer."* Sete dias é o piso, não o teto. O registro em `runs/` da E6 deve copiar as imagens para o repositório local, não guardar só a URL.

**Webhook opcional.** `?hf_webhook=<url>` no POST substitui polling em produção. Envelope tem `payload` contendo `images[].url`. Duplicatas são possíveis — deduplicar por `(request_id, status)`. Fora do escopo imediato do repositório, registrado por completude.

## 4. Tabela de erros

Literal `[HF]`, do `concepts/errors.md`:

| HTTP | Significado típico | Retry? |
|---|---|---|
| `400` | Parâmetros inválidos, entrada rejeitada, ou concorrência atingida | Após correção ou espera |
| `401` | Credenciais faltando ou inválidas | Não |
| `403` | Créditos insuficientes | Após creditar a conta |
| `404` | Requisição ou modelo não encontrado para esta conta | Não |
| `422` | Falha na validação do corpo | Não |
| `423` | Modelo temporariamente bloqueado | Depois |
| `500` | Erro inesperado | Sim, com backoff |
| `503` | Modelo desabilitado ou não pronto | Depois |

**Sem chave de idempotência para POST.** Literal `[HF]`: *"Do not automatically repeat a generation POST after an ambiguous timeout because submissions do not currently accept an idempotency key."* Consequência: o cliente da modalidade 3 registra o `request_id` **antes** de qualquer possibilidade de perda de conexão, e não faz retry cego de POST.

**Todo response traz `X-Correlation-ID`.** Guardar junto com `request_id` no registro de execução da E6.

## 5. Rate limits e concorrência

Literal `[HF]`:

> The primary generation limit is concurrency: the number of requests that may be queued or processing at the same time.

Quando atinge:

```json
{ "detail": "Maximum number of concurrent requests (4) has been reached" }
```

**A API não publica cabeçalhos padrão de rate limit nem `Retry-After`.** Os limites são visíveis apenas no dashboard da conta. A E3 registra isso como razão para o cliente da modalidade 3 usar semáforo local em vez de reagir a cabeçalhos.

## 6. Estimativa de custo

`POST /estimate/{model_path}` com os mesmos parâmetros do POST de geração. Retorna:

```json
{ "credits": "1.500", "usd": "0.094" }
```

Consequência útil: o cliente da modalidade 3 pode expor `estimate(spec)` sem cobrar créditos, e a Skill pode devolver o custo antes de disparar a geração. Aciona a política de aprovação de gasto que a E6 pode incorporar.

Créditos expiram um ano depois de comprados. Registrado por completude.

## 7. SDKs oficiais

**Python:** `pip install higgsfield-client`. API top-level `higgsfield_client.subscribe(model_path, arguments=...)`, síncrona ou assíncrona. Também expõe `submit`, `status`, `result`, `cancel`, `upload`, `upload_file`, `upload_image`.

**TypeScript / Node:** `npm install @higgsfield/client`. `higgsfield.subscribe(model_path, { input, withPolling: true })`. **Bloqueia uso em navegador** para prevenir exposição de credencial.

Ambos leem credencial de variável de ambiente: `HF_KEY` (Python) ou `HF_CREDENTIALS` (Node), no formato `id:secret`.

A modalidade 3 do repositório usa `higgsfield-client` no caminho síncrono, com escape para o caminho REST cru quando precisa de webhook ou controle explícito de estado. Justificado em `docs/03-modalidades/3-conector-higgsfield.md`.

## 8. Fluxo de upload

Quando a referência é arquivo local, e não URL pública:

1. `POST /files/generate-upload-url` com `{"content_type": "image/jpeg"}`  → `{ public_url, upload_url, upload_headers }`.
2. `PUT {upload_url}` com todos os `upload_headers` e o corpo do arquivo. **Não enviar credenciais Higgsfield para essa URL** — a URL é presigned para storage terceiro.
3. Passar `public_url` como `image_url` no `input_images` do POST de geração.

`upload_url` expira em 1 hora. Formatos aceitos: JPEG, JPG, PNG, WEBP, GIF, WAV, MP4.

## 9. Endpoints além de imagem

Registrado por completude — o repositório usa apenas `/nano-banana` na E3. O OpenAPI expõe 50 endpoints, cobrindo Seedance, Sora 2, Veo 3.1, Kling 2.5, Wan 2.5, Hailuo, Reve, Flux Pro Kontext, e a família própria da Higgsfield (SOUL, DoP, Popcorn). Nenhum entra na doutrina de hiper-realismo estático deste repositório.

## 10. Nova lacuna aberta pela extração

### L7 — Variante do Nano Banana exposta por `/nano-banana`

O endpoint da Higgsfield é único, sem distinção `pro` × `flash` na URL nem parâmetro que a selecione. O OpenAPI não documenta qual modelo Gemini está por trás. Duas hipóteses plausíveis, nenhuma verificada:

1. Higgsfield roteia sempre para `gemini-3-pro-image` (Nano Banana Pro).
2. Higgsfield roteia por conta ou por parâmetro interno não documentado.

**Impacto:** a promessa da modalidade 2 (interface Higgsfield) e da modalidade 3 (conector) de que o modelo alvo é o Pro depende da hipótese 1 estar correta. Se estiver errada, o comportamento cai para o Flash — que é bom, mas não é o padrão que a doutrina especifica.

**O que resolve:** uma chamada real com credencial, comparando latência e comportamento contra a chamada equivalente pela modalidade 4. Entra na bateria de validação da E7.
