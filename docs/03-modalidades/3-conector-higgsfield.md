# Modalidade 3 — Conector Higgsfield

`POST /nano-banana` da API Higgsfield, com o ciclo assíncrono completo — submissão, polling e recuperação. É a modalidade de produção pelo caminho Higgsfield: batch, cliente próprio, integração de webhook.

> **Aviso — L7 aberta.** `/nano-banana` é endpoint único; a documentação `[HF]` **não** documenta qual variante do Nano Banana ele roteia (Pro vs Flash). Toda menção a "target: gemini-3-pro-image" nesta página é **assumption operacional**, não fato verificado. Se o endpoint estiver roteando para Flash em contas standard, a qualidade entregue por esta modalidade é inferior à prometida. Antes de padronizar a modalidade 3 para produção crítica, execute a validação empírica descrita em `docs/00-fontes/05-divergencias-e-lacunas.md` L7 — uma chamada real via modalidade 3 e outra via modalidade 4 do mesmo spec, comparadas. Sem essa validação, prefira a modalidade 4 para trabalhos onde variante Pro é requisito.

## Envelope da chamada

Contrato executável em `[HF]` (openapi.json). O renderizador devolve exatamente:

```python
{
  "method": "POST",
  "url":    "https://platform.higgsfield.ai/nano-banana",
  "headers": {
    "Authorization": "Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}",
    "Content-Type":  "application/json"
  },
  "body": {
    "prompt":        "<corpo em blocos>\n\nAVOID: ...",
    "num_images":    1,
    "aspect_ratio":  "4:5",
    "output_format": "jpeg",
    "input_images":  [ { "type": "image_url", "image_url": "https://..." } ]
  }
}
```

## Autenticação

Correção que caiu do ESTADO na E3: a credencial **não é `refresh_token`**. É par **API key ID + secret**, enviado como:

```
Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}
```

`[HF]`, `authentication.md`, literal:

> Do not call the API directly from browser or mobile application code. Anyone who can inspect the application can extract its API secret and use your account.

O conector opera apenas server-side e lê as duas variáveis do ambiente. Se qualquer uma faltar, falha na hora, sem chamar a rede.

## Ciclo assíncrono

`[HF]`, `concepts/requests.md`:

```
POST /nano-banana         →  { status: "queued", request_id, status_url, cancel_url }
GET  {status_url}          →  { status: "in_progress", ... }
GET  {status_url}          →  { status: "completed", images: [{ url }] }
```

Estados terminais: `completed`, `failed`, `nsfw`, `canceled`.

**Estratégia de polling recomendada** `[HF]`: intervalo inicial de 2s, aumentando gradualmente até 10s, com jitter. O cliente da E5 vai implementar exatamente essa curva.

**Sem chave de idempotência para POST.** `[HF]`, literal: *"Do not automatically repeat a generation POST after an ambiguous timeout because submissions do not currently accept an idempotency key."* Consequência dura: **grave o `request_id` antes de qualquer possibilidade de perda de conexão**. Retry cego de POST cobra crédito duplicado. Retry de GET status é seguro.

## Tabela de erros

`[HF]`, `concepts/errors.md`:

| HTTP | Significado | Retry? |
|---|---|---|
| `400` | Parâmetros inválidos ou concorrência atingida | Após correção ou espera |
| `401` | Credenciais faltando ou inválidas | Não |
| `403` | Créditos insuficientes | Após creditar a conta |
| `404` | Requisição ou modelo não encontrado | Não |
| `422` | Falha na validação do corpo | Não |
| `423` | Modelo temporariamente bloqueado | Depois |
| `500` | Erro inesperado | Sim, com backoff |
| `503` | Modelo desabilitado ou não pronto | Depois |

Todo response inclui `X-Correlation-ID`. O registro de execução em `runs/` (E6) guarda esse header junto com `request_id` — pareado, é a chave de suporte.

## Concorrência

Limite primário é **concorrência de conta**, não RPS. `[HF]`, `rate-limits.md`: *"The API does not currently publish standard rate-limit response headers or Retry-After."* O cliente da modalidade 3 usa semáforo local em vez de reagir a cabeçalhos que não existem.

Erro típico ao exceder:

```json
{ "detail": "Maximum number of concurrent requests (4) has been reached" }
```

## Estimativa de custo

`POST /estimate/nano-banana` com os **mesmos parâmetros** da geração. Devolve:

```json
{ "credits": "1.500", "usd": "0.094" }
```

O cliente expõe `estimate(spec)` como operação separada de `submit(spec)`. A Skill da E5 pode usar o valor para pedir confirmação do usuário antes de gastar créditos.

## Referências: presigned URL para arquivos locais

`input_images[].image_url` exige **URL pública**. Se a referência é um arquivo no disco:

1. `POST /files/generate-upload-url` com `{ "content_type": "image/jpeg" }` — devolve `{ upload_url, public_url, upload_headers }`.
2. `PUT {upload_url}` com o corpo do arquivo e todos os `upload_headers`. **Não envie a credencial Higgsfield para essa URL** — é presigned para storage terceiro.
3. Use `public_url` como `image_url`.

`upload_url` expira em 1 hora. Formatos aceitos: JPEG, PNG, WEBP, GIF, WAV, MP4.

O cliente esconde esse fluxo em três chamadas de conveniência: `upload_image`, `upload_file`, `upload`.

## Exemplo ponta a ponta

Instância: `schemas/exemplos/exemplo-1-retrato-estudio.json`.
Payload renderizado: `exemplos/exemplo-1-retrato-estudio-mod3.json`.

Chamada equivalente em `curl`:

```bash
export HF_API_KEY_ID="..."
export HF_API_KEY_SECRET="..."

curl --silent --show-error --fail-with-body \
  --request POST \
  --url https://platform.higgsfield.ai/nano-banana \
  --header "Authorization: Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}" \
  --header "Content-Type: application/json" \
  --data @exemplos/exemplo-1-retrato-estudio-mod3-body.json | jq
```

Onde o `body` do payload contém `prompt` (corpo + cauda), `aspect_ratio: "4:5"`, `num_images: 1`, `output_format: "jpeg"`. **Sem `resolution`** — o endpoint não expõe.

## Webhook — nota de escopo

`?hf_webhook=<url>` no POST substitui polling em produção. O envelope tem `payload.images[].url`. Duplicatas são possíveis — deduplicar por `(request_id, status)`. **Fora do escopo do conector base** desta modalidade; entra na E5 como caminho opcional para clientes que rodam servidor HTTP próprio.

## Retenção

`Output URLs are retained for at least seven days` `[HF]`. O registro de execução em `runs/` da E6 **copia** as imagens para o repositório local — a URL sozinha não é acervo.

## Limites operacionais herdados da Higgsfield

- **8 referências** por chamada (não 14 do Gemini nativo). Passa folgado sobre o teto de 5 para identidade.
- **4 imagens** de saída por chamada (`num_images` máx=4).
- **Sem controle de `resolution`** em `/nano-banana`. A resolução é decidida pela plataforma. Auditoria fina de 4K só pela modalidade 4.
- **Variante do Nano Banana ainda não confirmada** (L7). O endpoint não distingue Pro vs Flash; validação empírica na E7.
