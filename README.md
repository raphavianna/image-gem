# image-gem

Sistema para gerar prompts hiper-realistas para **Nano Banana Pro** (`gemini-3-pro-image`) e executá-los pela API Gemini ou pela API Higgsfield, com o mesmo pipeline atendendo interface de chat, painel e código.

O critério de aceitação de todo prompt emitido pelo sistema é único: **a imagem gerada deve ser indistinguível de uma fotografia real capturada por um profissional**. A doutrina de como isso é obtido — cadeia física completa e coerente entre câmera, luz, superfície, sensor e revelação — está em [`docs/01-doutrina-hiper-realismo.md`](docs/01-doutrina-hiper-realismo.md).

## Instalação

Requer Python 3.10+.

```bash
git clone https://github.com/raphavianna/image-gem
cd image-gem
pip install -e .                          # pacote + CLI (jsonschema, httpx)
pip install -e '.[gemini]'                # + google-genai (modalidade 4 real)
pip install -e '.[mcp]'                   # + mcp (servidor MCP)
pip install -e '.[gemini,mcp,dev]'        # tudo
```

## Credenciais

Nenhuma é obrigatória. Sem credencial no ambiente, o pipeline roda em **modo simulação** ponta a ponta: `imagegem submit` imprime o payload que iria à rede e grava o registro em `runs/`.

Com credencial, o mesmo comando chama a API real:

```bash
export GEMINI_API_KEY=...                 # modalidade 4 real
export HF_API_KEY_ID=... HF_API_KEY_SECRET=...   # modalidade 3 real
```

## Uso — as quatro modalidades

O mesmo spec canônico serve as quatro modalidades. Todas leem o mesmo schema, aplicam as mesmas 13 regras de coerência e o mesmo checklist de emissão. O que muda é o envelope.

| # | Nome | Destino | Quando |
|---|---|---|---|
| **1** | Interface Gemini | texto colável em `gemini.google.com` | exploração, iteração conversacional |
| **2** | Interface Higgsfield | texto + controles do painel `cloud.higgsfield.ai` | fluxo no painel Higgsfield |
| **3** | Conector Higgsfield | `POST /nano-banana` via HTTP | produção pelo caminho Higgsfield |
| **4** | API Gemini | `google-genai` SDK | produção pelo caminho Gemini nativo; único caminho para **4K auditável**, `include_thoughts`, chat multi-turno e 14 referências |

Fluxo típico:

```bash
imagegem templates                                # lista os 8 templates
imagegem resolve retrato-estudio --out spec.json  # template → spec (usa example_answers se não passar --answers)
imagegem validate spec.json                       # schema + coerência + checklist
imagegem render   spec.json --modality 4          # envelope da modalidade
imagegem submit   spec.json --modality 4          # chama o cliente; grava em runs/
imagegem review   RUN_ID --verdict mixed --rating 4 \
                  --signal "..." --follow-up "doctrine|..."   # loop da E6
imagegem runs --pending                           # follow-ups ainda não promovidos
```

Detalhes de cada modalidade em [`docs/03-modalidades/`](docs/03-modalidades/).

## Templates disponíveis

Oito, cobrindo o piso pedido pelo prompt-mestre mais dois:

| ID | Regime | Pessoa? | Uso |
|---|---|---|---|
| `retrato-estudio` | generation | sim | Perfil corporativo, capa editorial |
| `retrato-ceu-aberto` | generation | sim | Editorial em locação, contraluz |
| `corpo-inteiro-locacao` | generation | sim | Editorial de moda em rua |
| `produto-estudio` | generation | não | E-commerce premium, hero |
| `still-moda` | generation | não | Catálogo, look book |
| `edicao-troca-fundo` | edit | sim | Mover retrato para locação plausível |
| `composicao-multi-referencia` | composition | sim | Combinar sujeito + objeto + estilo |
| `consistencia-personagem` | generation | sim | Mesma identidade, nova pose ou ambiente |

Cada template declara defaults campo a campo e uma lista `ask_before[]` do que a Skill precisa perguntar antes de gerar. Ver [`docs/04-templates.md`](docs/04-templates.md).

## Política de conteúdo

Herdada pela Skill, CLI e servidor MCP. Aplicada antes de qualquer chamada externa:

- **Não gera** imagens fotorrealistas de **pessoas reais identificáveis**, exceto quando a própria pessoa fornece a imagem de referência.
- **Não gera** imagens de **menores** (idade < 18, ou termos como "criança", "adolescente").
- **Não produz** simulação de **documento oficial**, recibo, evidência ou imagem jornalística.

Implementação em [`src/imagegem/policy.py`](src/imagegem/policy.py). É heurística conservadora — falsos positivos são preferíveis a falsos negativos.

## Skill do Claude Code e servidor MCP

- **Skill:** [`.claude/skills/imagegem/SKILL.md`](.claude/skills/imagegem/SKILL.md) — pipeline de rotear pedido em linguagem natural para template, aplicar política, coletar respostas, resolver, validar, escolher modalidade, submeter. Herdando a regra operacional do loop da E6.

- **MCP:** [`mcp_server/server.py`](mcp_server/server.py) — cinco ferramentas para qualquer cliente Claude:
  - `list_templates`
  - `render_prompt` (barato, sem chamar rede)
  - `generate_image` (real ou simulação)
  - `validate_spec`
  - `check_content_policy`

  ```bash
  python -m mcp_server.server   # stdio, para o cliente MCP conectar
  ```

## Doutrina em uma frase

`photorealistic`, `hyper-realistic`, `8k`, `ultra detailed`, `award winning`, `masterpiece` são **proibidos** no prompt. Modelos modernos tratam esses termos como marcadores de estilo de renderização digital e frequentemente pioram o resultado. O realismo vem da **cadeia causal fechada** — câmera → óptica → luz → superfície → sensor → revelação — com cada elo declarado e coerente com os outros. Doutrina completa em [`docs/01-doutrina-hiper-realismo.md`](docs/01-doutrina-hiper-realismo.md).

## Loop de aprendizado

Toda geração que recebe avaliação vira registro versionado em `runs/`. Toda correção que aparece duas vezes vira issue de doutrina, template ou checklist. Nenhum aprendizado morre em conversa. Ver [`docs/06-loop.md`](docs/06-loop.md) e o registro-âncora em [`runs/EXEMPLO-e6-registro-ancora/`](runs/EXEMPLO-e6-registro-ancora/).

## Arquivos

```
image-gem/
├── docs/                    # documentação viva, em ordem de leitura
│   ├── ESTADO.md            # onde parou o trabalho, decisões travadas
│   ├── PROMPT-MESTRE.md     # constituição do projeto
│   ├── 00-fontes/           # E0: fontes técnicas extraídas
│   ├── 01-doutrina-hiper-realismo.md
│   ├── 02-gramatica-do-prompt.md
│   ├── 03-modalidades/
│   ├── 04-templates.md
│   ├── 04-aprendizados.md   # E6: log vivo do loop
│   ├── 05-implementacao.md
│   ├── 06-loop.md
│   └── 07-validacao/        # E7: bateria e evidências
├── schemas/
│   ├── prompt-spec.json     # schema canônico (fonte única de verdade)
│   ├── run-record.json      # schema do registro em runs/
│   └── exemplos/            # 3 instâncias âncora
├── templates/               # 8 templates
├── src/imagegem/            # pacote Python
│   ├── schema.py resolver.py render.py check.py
│   ├── policy.py runs.py cli.py
│   └── clients/gemini.py clients/higgsfield.py
├── mcp_server/server.py     # servidor MCP
├── .claude/skills/imagegem/SKILL.md
├── tests/test_pipeline.py   # regressão
├── runs/EXEMPLO-*/          # registros-âncora do loop
└── pyproject.toml
```

## Fontes técnicas

Toda afirmação técnica em `docs/` é rastreável a uma fonte marcada:

| Etiqueta | Fonte | Autoridade para |
|---|---|---|
| `[GAI]` | `ai.google.dev/gemini-api/docs/*` | Capacidades, limites e preços do Nano Banana |
| `[HF]` | `docs.higgsfield.ai` + OpenAPI | API Higgsfield |
| `[SDK]` | `googleapis/python-genai` | Nomes, tipos e valores de parâmetro |
| `[CB]` | `google-gemini/cookbook` | Padrões de uso, dimensões em pixel |
| `[BLOG]` | Google Cloud Blog *Ultimate prompting guide* | Guia de prompts |

Extrações completas em [`docs/00-fontes/`](docs/00-fontes/).

## Contribuir

O projeto foi construído em sete etapas com gate por aprovação. O estado atual e a próxima etapa ficam sempre em [`docs/ESTADO.md`](docs/ESTADO.md). Antes de qualquer mudança, leia esse arquivo e o [`docs/PROMPT-MESTRE.md`](docs/PROMPT-MESTRE.md).

## Licença

MIT.
