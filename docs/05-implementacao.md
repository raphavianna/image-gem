# Implementação — pacote, CLI, Skill e MCP

Etapa **E5**. Consolida em código executável tudo que as etapas anteriores definiram como contrato: schema canônico, resolver de templates, quatro renderizadores de modalidade, regras de coerência, checklist de emissão, política de conteúdo, clientes Gemini e Higgsfield, registro versionado em `runs/`.

## Layout do repositório após E5

```
image-gem/
├── pyproject.toml
├── src/imagegem/
│   ├── __init__.py          # re-exports do pacote
│   ├── schema.py            # load do prompt-spec.json, caminhos e cache
│   ├── resolver.py          # template + answers → spec
│   ├── render.py            # 4 renderizadores de modalidade
│   ├── check.py             # regras C1–C14 + checklist ck1–ck8 + validate()
│   ├── policy.py            # política de conteúdo (recusa curta)
│   ├── runs.py              # registro versionado para a E6
│   ├── cli.py               # entry point `imagegem`
│   └── clients/
│       ├── gemini.py        # google-genai + modo simulação
│       └── higgsfield.py    # httpx + ciclo assíncrono + modo simulação
├── mcp_server/
│   └── server.py            # servidor MCP com 5 ferramentas
├── .claude/skills/imagegem/
│   └── SKILL.md             # Skill do Claude Code
├── schemas/
│   ├── prompt-spec.json     # schema canônico (fonte única de verdade)
│   └── exemplos/            # 3 instâncias âncora
├── templates/               # 8 templates
├── tests/
│   └── test_pipeline.py     # 18 negativos + 3 bases + 5 renderizadores
└── docs/                    # documentação viva do sistema
```

O arquivo `schemas/validador.py` que a E2 introduziu como validador de referência foi **removido** — sua lógica está em `src/imagegem/check.py` e `src/imagegem/render.py`. `templates/_resolver.py` também: virou `src/imagegem/resolver.py`. `schemas/testes.py` virou `tests/test_pipeline.py` com imports do pacote. **As regras não se moveram** — continuam declaradas em `schemas/prompt-spec.json` sob `x-imagegem`, e o código as lê de lá.

## Instalação

```bash
pip install -e .                          # pacote + CLI + jsonschema + httpx
pip install -e '.[gemini]'                # + google-genai (modalidade 4 real)
pip install -e '.[mcp]'                   # + mcp (servidor MCP)
pip install -e '.[gemini,mcp,dev]'        # tudo
```

Sem `google-genai` instalado, a modalidade 4 opera em simulação. Sem `mcp`, o servidor não sobe.

## CLI — `imagegem`

Seis subcomandos, cada um coberto pelo próprio `--help`:

| Comando | Uso |
|---|---|
| `imagegem templates` | Lista os 8 templates com regime e descrição |
| `imagegem resolve TPL [--answers J] [--out F]` | Resolve template + respostas em spec; usa `example_answers` se `--answers` for omitido |
| `imagegem validate SPEC` | Schema + coerência + checklist |
| `imagegem render SPEC [--modality N]` | Envelope da modalidade N |
| `imagegem submit SPEC --modality {3,4} [--thoughts]` | Chama o cliente, salva em `runs/` |
| `imagegem estimate SPEC` | Custo Higgsfield sem consumir créditos |

**Fluxo típico ponta a ponta**, em simulação (sem credencial):

```bash
imagegem resolve retrato-estudio --out /tmp/spec.json
imagegem validate /tmp/spec.json         # OK — corpo 620p, faixa 500–650
imagegem submit /tmp/spec.json --modality 4
# [gemini:simulacao] payload que iria para google-genai:
#   model: gemini-3-pro-image
#   image: aspect_ratio=4:5, image_size=2K
#   prompt: 645 palavras
# registro salvo em runs/20260816-.../retrato-estudio
```

Com `GEMINI_API_KEY` no ambiente, o mesmo comando chama a rede.

## Clientes — decisão de arquitetura

Os dois clientes seguem o mesmo padrão:

1. `credenciais_disponiveis()` — checa o ambiente.
2. `submit(spec, …)` — devolve `Resultado` (dataclass) com `modo`, `imagens`, `raw`, `error`, e demais campos do respectivo API.
3. Sem credencial, imprime resumo do payload no stderr e devolve resultado sintético com o mesmo formato. Sem `if` no chamador.

**Gemini (`clients/gemini.py`).** Usa `client.models.generate_content` com `types.ImageConfig` — a superfície do `[SDK]` explicitamente documentada. Se `include_thoughts=True`, passa `types.ThinkingConfig` e coleta partes com `thought=True` no resultado. Itera **todas** as partes da resposta, não para na primeira imagem, conforme `[CB]`.

**Higgsfield (`clients/higgsfield.py`).** Implementa o ciclo assíncrono `POST → poll → completed` com backoff de 2s → 10s + jitter (`[HF]` `concepts/polling.md`). Grava `request_id` **antes** de qualquer retry ambíguo, porque `[HF]` diz explicitamente que POST não aceita chave de idempotência. `X-Correlation-ID` é lido de todo response e propagado para o registro em `runs/`. `upload_image` implementa o fluxo presigned URL. `estimate` chama `POST /estimate/nano-banana` — devolve custo sem consumir créditos.

## Política de conteúdo (`policy.py`)

Herdada pela Skill, CLI e MCP. Recusa curta em três frentes:

- **Menores** — regex de termos + regex de idade numérica (`< 18`).
- **Documentos/jornalismo simulado** — regex de termos (passaporte, RG, recibo, evidência, imagem jornalística, etc.).
- **Pessoas reais identificáveis** — dois nomes próprios em sequência, **exceto** quando o usuário anexou referência dele mesmo (`tem_referencia=True`).

É **heurística conservadora, não classificador**: falsos negativos vão passar; falsos positivos são o custo aceito para não gerar conteúdo vetado. A Skill duplica essa checagem antes de rotear qualquer template.

## Registro em `runs/`

Cada `submit` (real ou simulado) escreve uma pasta em `runs/{YYYYmmdd-HHMMSS}-{slug}/`:

```
spec.json         # spec canônico usado, com meta.defaults_applied
prompt.txt        # corpo + cauda que foram para o modelo
envelope.json     # payload da modalidade
response.json     # resposta do cliente (bruto)
metadata.json     # template, modalidade, cliente, duração, correlation_id
image_00.jpg …    # imagens salvas pelo cliente (modalidade 4 real)
```

`meta.defaults_applied[]` é o que a **E6** usa para correlacionar aparência de saída com escolha de default do template — sem esse rastreio, o loop de aprendizado não tem chave.

## Servidor MCP (`mcp_server/server.py`)

Cinco ferramentas para qualquer cliente Claude (Claude Code, Claude Desktop, extensões IDE):

| Tool | Uso |
|---|---|
| `list_templates` | Metadados dos 8 templates |
| `render_prompt` | Resolve + renderiza sem submeter (barato, seguro) |
| `generate_image` | Submete (modalidade 3 ou 4), salva em `runs/` |
| `validate_spec` | Roda o checklist sobre um spec JSON cru |
| `check_content_policy` | Valida pedido em linguagem natural antes de rodar |

Todas passam pela política de conteúdo antes de qualquer chamada externa. Rodar:

```bash
python -m mcp_server.server   # stdio, para o cliente MCP conectar
```

## Skill do Claude Code (`.claude/skills/imagegem/SKILL.md`)

Pipeline documentado como frontmatter + prompt:

1. Rotear para um template pelos `aliases`.
2. Aplicar política de conteúdo.
3. Coletar respostas do `ask_before[]` — nunca inventar valor.
4. `resolve` → `validate` → escolher modalidade → `submit` ou `render_prompt`.
5. Registrar em `runs/` (feito pelo pipeline).
6. Responder ao usuário mostrando template, defaults aplicados e modalidade escolhida.

A regra dura: **nunca use os termos proibidos** (`photorealistic`, `hyper-realistic`, `8k`, `ultra detailed`, `award winning`, `masterpiece`). O checklist reprova se aparecerem.

## Definição de pronto — status

| Item | Status |
|---|---|
| CLI executa ponta a ponta em modo simulação | **Cumprido** — pipeline resolve → validate → submit → registro roda sem credencial |
| MCP expõe geração e edição | **Cumprido** — 5 ferramentas, incluindo `generate_image` cobrindo edição via o template `edicao-troca-fundo` |
| Skill implementa a regra de pedidos subespecificados | **Cumprido** — resolver levanta `ValueError` se falta resposta, Skill nunca inventa |
| Skill implementa a política de conteúdo | **Cumprido** — `policy.check_pedido` chamado pela Skill, CLI e MCP antes de resolver |
| Gate condicional Higgsfield | **Superado** — a extração `[HF]` na E3 removeu o stub; cliente real implementado, cai em simulação sem credencial |

## O que fica para as etapas seguintes

- **E6** define o esquema formal do registro em `runs/` (o atual é *ad hoc*, funciona mas não tem versão), consome `meta.defaults_applied[]` para gerar `docs/04-aprendizados.md`, e escreve a regra operacional que obriga toda geração avaliada a virar registro.
- **E7** executa a bateria de validação com credenciais reais: os 8 templates via modalidade 3 e via modalidade 4, comparando latência e comportamento, fechando L3 (`person_generation`) e L7 (variante do `/nano-banana`).

## Regressão

```bash
python3 tests/test_pipeline.py
# Bases: 3 aprovadas
# 5 renderizadores: OK
# 18 testes negativos passaram
```
