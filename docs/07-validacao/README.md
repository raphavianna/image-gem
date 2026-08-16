# Validação e fechamento

Etapa **E7**. Última do plano. Prova que tudo que é executável sem credencial foi executado com sucesso, que o README cobre o repositório para quem chega frio, e que a branch está enviada.

## Bateria executada

Log completo em `bateria.log`, capturado em 2026-08-16. Oito seções:

| # | Seção | Resultado |
|---|---|---|
| 1 | Instalação limpa (`pip show imagegem`) | 0.1.0 |
| 2 | Suíte de testes (`tests/test_pipeline.py`) | **18 negativos + 3 bases + 5 renderizadores** aprovados |
| 3 | CLI `imagegem templates` | 8 templates listados |
| 4 | Ciclo `resolve → validate` em **cada** template | 8 de 8 OK, com corpo dentro da faixa correta |
| 5 | `render` em modalidades 1, 2, 3, 4 | envelopes gerados |
| 6 | `submit` modalidades 3 e 4 em simulação | resposta sintética, registro em `runs/` |
| 7 | `runs --limit 5` | inclui `EXEMPLO-e6-registro-ancora` com verdict mixed |
| 8 | Política de conteúdo em 4 casos | menor, documento e "Barack Obama" recusados; pedido genérico aprovado |

Contagem final: **27 comandos com exit 0**, nenhum vermelho.

## Resultado por template

| Template | Corpo | Faixa aplicada |
|---|---|---|
| `retrato-estudio` | 620 | 500–650 (geração com pessoa) |
| `retrato-ceu-aberto` | 641 | 500–650 |
| `corpo-inteiro-locacao` | 639 | 500–650 |
| `produto-estudio` | 549 | 350–560 (geração sem pessoa) |
| `still-moda` | 476 | 350–560 |
| `edicao-troca-fundo` | 290 | 250–400 (edição) |
| `composicao-multi-referencia` | 456 | 350–560 (ancorado em referência) |
| `consistencia-personagem` | 453 | 350–560 (ancorado em referência) |

## O que **não** foi validado

**L3 e L7 seguem pendências permanentes** da entrega, ambas dependentes de credencial real:

| Lacuna | O que resolve | O que fazer quando abrir |
|---|---|---|
| **L3** — default e comportamento de `person_generation` | `GEMINI_API_KEY` no ambiente | `imagegem submit … --modality 4` real, inspecionar comportamento com `person_generation` omitido, `ALLOW_ADULT` e `DONT_ALLOW`. Atualizar `docs/00-fontes/05-divergencias-e-lacunas.md` e a política em `src/imagegem/policy.py` se necessário. |
| **L7** — variante do `/nano-banana` na Higgsfield | `HF_API_KEY_ID` + `HF_API_KEY_SECRET` | `imagegem submit … --modality 3` real e `imagegem submit … --modality 4` do mesmo spec; comparar latência e comportamento. Se `/nano-banana` roteia para Flash em vez de Pro, ajustar `docs/03-modalidades/2-*` e `.../3-*` com a descoberta. |

Ambas produziriam entrada em `docs/04-aprendizados.md` — a primeira **não-retroativa** da série.

## Reprodução

Do zero, em ambiente Python 3.10+:

```bash
git clone https://github.com/raphavianna/image-gem
cd image-gem
pip install -e .
python3 tests/test_pipeline.py     # 18 negativos + 3 bases + 5 renderizadores
python3 tests/test_policy.py       # 29 casos da política de conteúdo
python3 tests/test_resolver.py     # 4 testes do resolver + validação dos 8 templates
# todos passam

for t in retrato-estudio retrato-ceu-aberto corpo-inteiro-locacao \
         produto-estudio still-moda edicao-troca-fundo \
         composicao-multi-referencia consistencia-personagem; do
  imagegem resolve $t --out /tmp/spec.json > /dev/null
  imagegem validate /tmp/spec.json
done
# 8× OK

imagegem submit /tmp/spec.json --modality 4
# [gemini:simulacao] payload que iria para google-genai …
# registro salvo em runs/…
# OK — modo=simulacao status=completed
```

`bateria.log` deste diretório é a saída literal correspondente.

## Estado das sete etapas

Todas concluídas e aprovadas:

| Etapa | Commit final |
|---|---|
| E0 — Fontes | `e95ac90` |
| E1 — Doutrina | `310c503`, `d0a4136` |
| E2 — Gramática do prompt | `ea52f57` |
| E3 — Modalidades | `4f95674` |
| E4 — Biblioteca de templates | `62fd37d` |
| E5 — Implementação | `1cad865` |
| E6 — Loop de retroalimentação | `6b08674` |
| E7 — Validação e fechamento | *este commit* |

`docs/ESTADO.md` guarda o quadro completo com decisões travadas e pendências.
