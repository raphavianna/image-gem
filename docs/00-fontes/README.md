# E0 — Fontes extraídas

Extração estruturada das fontes técnicas que sustentam todo o resto do repositório. Cada afirmação técnica em `docs/` daqui para frente deve ser rastreável a um item destes arquivos.

Data da extração: **2026-08-16**.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `01-modelos-e-limites.md` | Identificadores de modelo, correspondência nome comercial ↔ ID técnico, janelas de contexto, resoluções, proporções e a tabela de dimensões em pixels |
| `02-parametros-sdk.md` | Superfície exata do SDK `google-genai`: `ImageConfig`, `GenerateContentConfig`, `ThinkingConfig`, tools, e as três APIs de chamada |
| `03-capacidades.md` | Multi-referência, consistência de personagem, edição, grounding, thinking, thought signatures, marca d'água |
| `04-guia-de-prompts-oficial.md` | O guia de prompts primeiro-parte: os cinco frameworks, as fórmulas, e as regras de formulação |
| `05-divergencias-e-lacunas.md` | Divergências entre fontes, itens `[NÃO VERIFICADO]` e o que resolveria cada um |
| `fontes.json` | Índice legível por máquina das fontes, com SHA de commit e nível de confiança |

## Método e rastreio de origem

Todo item extraído carrega uma etiqueta de origem inline:

| Etiqueta | Fonte | Confiança |
|---|---|---|
| `[SDK]` | `googleapis/python-genai`, `google/genai/types.py` — arquivo em `main`, sha256 `2117f4dc3ae39efb…` | Alta. Autoridade para nomes, tipos e valores de parâmetro |
| `[CB]` | `google-gemini/cookbook` @ `c9d1a3bb2fe7a9e11724a134100280f5e14ebd30` (2026-08-13), `quickstarts/Get_Started_Nano_Banana.ipynb` | Alta. Primeiro-parte Google. Autoridade para padrões de uso e tabelas de resolução |
| `[BLOG]` | Google Cloud Blog, *Ultimate prompting guide for Nano Banana* | Alta. Primeiro-parte Google. Autoridade para o guia de prompts e para a tabela de especificações |
| `[VTX-NB]` | `GoogleCloudPlatform/generative-ai`, `gemini/getting-started/intro_gemini_3_image_gen.ipynb` | Alta. Primeiro-parte Google |
| `[PYPI]` | `pypi.org/pypi/google-genai/json` | Alta. Autoridade para versão do pacote |
| `[WS]` | Conteúdo de página bloqueada, recuperado por busca web em vez de leitura direta | **Média.** Paráfrase de terceiro sobre fonte primária. Nunca é autoridade sozinho |

A hierarquia definida no prompt-mestre foi aplicada: **SDK** para nomes, tipos e valores aceitos de parâmetro; **documentação primeiro-parte** para capacidades, limites e preços; **cookbook e notebooks** apenas para padrões de uso.

## Política de rede desta sessão

A fonte primária pedida — `https://ai.google.dev/gemini-api/docs/image-generation` — está **bloqueada pela política de egress** (403 no CONNECT do proxy). Não houve tentativa de contorno e a verificação TLS não foi alterada.

Estado verificado dos hosts em 2026-08-16:

| Host | Estado | Uso |
|---|---|---|
| `ai.google.dev` | **403 bloqueado** | — |
| `docs.cloud.google.com` | **403 bloqueado** | — |
| `cloud.google.com` (raiz e `/blog/`) | 200 | Guia de prompts `[BLOG]` |
| `cloud.google.com/vertex-ai/...` | 301 → `docs.cloud.google.com` | **Inutilizável.** O redirecionamento cai em host bloqueado |
| `developers.googleblog.com` | **bloqueado** | — |
| `blog.google` | **bloqueado** | — |
| `raw.githubusercontent.com` / clone git anônimo | OK | `[SDK]`, `[CB]`, `[VTX-NB]` |
| `pypi.org` | 200 | `[PYPI]` |
| `generativelanguage.googleapis.com` | 404 na raiz — **túnel passa** | Modalidade 4 executável com chave |
| `higgsfield.ai`, `api.higgsfield.ai`, `platform.higgsfield.ai` | **bloqueados** | Pendência de E5 |

Consequência que vale registrar: o bloqueio de `docs.cloud.google.com` derrubou a autoridade prevista para **preços**. Ver `05-divergencias-e-lacunas.md`.
