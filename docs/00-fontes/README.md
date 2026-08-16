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
| `06-fonte-primaria-ai-google-dev.md` | **Extração tardia da fonte primária**, lida depois que o egress abriu: preços, orçamentos de referência por papel, guia de prompts literal, limitações |
| `07-fonte-primaria-higgsfield.md` | **Extração tardia da Higgsfield**, antecipada da E5 para a E3: endpoint `/nano-banana`, credenciais, ciclo assíncrono, tabela de erros, SDKs |
| `fontes.json` | Índice legível por máquina das fontes, com SHA de commit e nível de confiança |

> **Nota de revisão — 2026-08-16.** A E0 foi executada com `ai.google.dev` bloqueado. Na abertura da sessão seguinte o host passou a responder `200`, e a fonte primária foi lida antes da E1 e extraída em `06-fonte-primaria-ai-google-dev.md`. Isso resolveu quatro das seis lacunas e as duas divergências abertas, e **corrigiu uma decisão travada** (teto de referências de identidade: 5, não 6). Os arquivos `01` a `04` não foram reescritos — as correções estão consolidadas em `05` e `06`, que prevalecem em caso de conflito.

## Método e rastreio de origem

Todo item extraído carrega uma etiqueta de origem inline:

| Etiqueta | Fonte | Confiança |
|---|---|---|
| `[GAI]` | `ai.google.dev/gemini-api/docs/image-generation` e `/pricing` — lidos em 2026-08-16 | **Alta. Documentação primeiro-parte.** Autoridade máxima para capacidades, limites e preços |
| `[HF]` | `docs.higgsfield.ai` e o `openapi.json` — lidos em 2026-08-16 | **Alta. Documentação primeiro-parte + contrato executável.** Autoridade máxima para a API Higgsfield |
| `[SDK]` | `googleapis/python-genai`, `google/genai/types.py` — arquivo em `main`, sha256 `2117f4dc3ae39efb…` | Alta. Autoridade para nomes, tipos e valores de parâmetro |
| `[CB]` | `google-gemini/cookbook` @ `c9d1a3bb2fe7a9e11724a134100280f5e14ebd30` (2026-08-13), `quickstarts/Get_Started_Nano_Banana.ipynb` | Alta. Primeiro-parte Google. Autoridade para padrões de uso e tabelas de resolução |
| `[BLOG]` | Google Cloud Blog, *Ultimate prompting guide for Nano Banana* | Alta. Primeiro-parte Google. Autoridade para o guia de prompts e para a tabela de especificações |
| `[VTX-NB]` | `GoogleCloudPlatform/generative-ai`, `gemini/getting-started/intro_gemini_3_image_gen.ipynb` | Alta. Primeiro-parte Google |
| `[PYPI]` | `pypi.org/pypi/google-genai/json` | Alta. Autoridade para versão do pacote |
| `[WS]` | Conteúdo de página bloqueada, recuperado por busca web em vez de leitura direta | **Média.** Paráfrase de terceiro sobre fonte primária. Nunca é autoridade sozinho |

A hierarquia definida no prompt-mestre foi aplicada: **SDK** para nomes, tipos e valores aceitos de parâmetro; **documentação primeiro-parte** para capacidades, limites e preços; **cookbook e notebooks** apenas para padrões de uso.

## Política de rede

**Estado atual — 2026-08-16, sessão de E1.** A política do environment foi alterada para `Custom` com domínios adicionais, e a fonte primária **foi liberada**. Validação:

| Host | Estado | Uso |
|---|---|---|
| `ai.google.dev` | **200 — liberado** | `[GAI]`, fonte primária |
| `docs.cloud.google.com` | **200 — liberado** | Disponível, não necessário após `[GAI]` |
| `clerk.higgsfield.ai`, `oriented-jay-78.clerk.accounts.dev` | 200 | Higgsfield, E5 |
| `fnf-api-gw.higgsfield.ai`, `fnf.higgsfield.ai`, `cdn.higgsfield.ai`, `static.higgsfield.ai` | 404 — **túnel passa** | Higgsfield, E5 |

Qualquer código HTTP significa liberado; `000` significaria CONNECT recusado.

### Estado durante a E0 — registro histórico

A fonte primária pedida — `https://ai.google.dev/gemini-api/docs/image-generation` — estava **bloqueada pela política de egress** (403 no CONNECT do proxy). Não houve tentativa de contorno e a verificação TLS não foi alterada. A E0 inteira foi construída por rotas alternativas sob essa restrição.

| Host | Estado na E0 | Uso |
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

Consequência registrada na época: o bloqueio de `docs.cloud.google.com` derrubou a autoridade prevista para **preços**, o que produziu a lacuna crítica L1. **L1 foi resolvida em 2026-08-16** com a liberação do egress. Ver `05-divergencias-e-lacunas.md` e `06-fonte-primaria-ai-google-dev.md`.
