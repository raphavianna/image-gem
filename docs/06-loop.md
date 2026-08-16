# Loop de retroalimentação

Etapa **E6**. Fecha o ciclo entre gerar e aprender. Sem esta etapa, tudo que as E1–E5 construíram degrada em silêncio: qualquer descoberta feita numa geração morre no chat, e a doutrina fica desatualizada em relação à prática.

## Componentes

| Arquivo | Papel |
|---|---|
| `schemas/run-record.json` | Esquema formal do registro em `runs/`. Validado ao gravar. Campos-chave: `spec_hash`, `checklist_signature`, `template_version`, `defaults_applied_count`, `review`. |
| `src/imagegem/runs.py` | `register(...)` grava o registro completo; `review(...)` acrescenta a avaliação; `list_recent`, `pending_follow_ups` para leitura. Tudo validado contra o schema. |
| `imagegem submit` | Escreve o registro em `runs/{stamp}-{slug}/` a cada chamada — real ou simulada. Sem opt-out. |
| `imagegem review RUN_ID` | Acrescenta `verdict`, `rating`, `signals[]`, `follow_ups[]`. Última avaliação vence. |
| `imagegem runs` | Lista registros com verdict. `--reviewed` filtra por avaliados. `--pending` mostra follow-ups não promovidos. |
| `docs/04-aprendizados.md` | Log vivo. Cada linha aponta para um registro, commit ou arquivo — aprendizado sem prova rastreável não entra. |
| `runs/EXEMPLO-e6-registro-ancora/` | Registro-âncora versionado. Padrão do formato para os demais. |

## Formato do registro

Enforced por `schemas/run-record.json`. Campos obrigatórios:

| Campo | Uso |
|---|---|
| `record_version` | Versão do esquema — hoje `1.0` |
| `id` | Nome da pasta em `runs/` |
| `started_at`, `finished_at`, `duration_ms` | Timing |
| `status` | `started`, `completed`, `failed`, `nsfw`, `canceled`, `simulated` |
| `template`, `template_version` | Origem do spec |
| **`spec_hash`** | SHA-256 do spec canônico serializado ordenado — **chave de comparação entre execuções** |
| `schema_version` | `spec_version` do prompt-spec.json em vigor |
| `modality`, `client` | Onde a execução aconteceu |
| `correlation_id`, `request_id` | Chaves para suporte (Higgsfield inclui `X-Correlation-ID`) |
| `defaults_applied_count` | Quantos caminhos vieram do template — a trilha completa mora em `spec.json/meta.defaults_applied[]` |
| `prompt_word_count` | Densidade emitida |
| **`checklist_signature`** | IDs das regras+checks que se aplicam a este spec, ex. `C1|C2|C3|C6|ck1|ck5|ck6|ck7|ck8` — **prova que dois registros foram avaliados com o mesmo rigor** |
| `review` | Opcional; presente após `imagegem review` |

`spec_hash` + `checklist_signature` são o que impede o loop de virar anedota. Dois registros com o mesmo hash podem ser comparados. Se a signature difere entre execuções do mesmo template, alguma condição de aplicabilidade mudou — sinal para investigar antes de comparar.

## Ciclo típico

```
1.  imagegem resolve retrato-estudio --out spec.json --answers respostas.json
2.  imagegem submit  spec.json --modality 4          # grava em runs/
3.  (autor avalia a imagem)
4.  imagegem review  20260816-.../retrato-estudio \
        --verdict mixed --rating 4 \
        --signal "pele com brilho uniforme|Brilho uniforme no rosto|skin.specular_zones" \
        --follow-up "doctrine|zona T mais reflexiva que maçãs, com gradiente medível|docs/01-doutrina-hiper-realismo.md"
5.  imagegem runs --pending                          # follow-ups aguardando promoção
6.  (autor promove o follow-up: edita a doutrina, commita)
7.  (autor edita metadata.json para preencher review.follow_ups[N].promoted_to)
8.  (autor edita docs/04-aprendizados.md com a linha nova)
```

O passo 6→8 é hoje **manual**: a promoção é decisão humana, o campo `promoted_to` é apenas o marcador de que aconteceu.

## Signals

O campo `review.signals[]` mapeia problemas observados na saída para linhas da **tabela diagnóstica** (`docs/01-doutrina-hiper-realismo.md` seção 4) e para **campos do schema** que carregam a correção. Isso é o que dá endereço para o follow-up.

```json
{
  "signal":       "pele com brilho uniforme, sem gradiente",
  "doctrine_row": "Brilho uniforme no rosto",
  "schema_field": "skin.specular_zones"
}
```

Quando um mesmo `doctrine_row` aparece em dois registros diferentes, a Skill sinaliza para o autor: a correção precisa subir para a doutrina, não para o template específico.

## Follow-ups

`review.follow_ups[]` propõe onde a correção subiria. `kind` é enum:

| Kind | Onde | Exemplo |
|---|---|---|
| `doctrine` | `docs/01-doutrina-hiper-realismo.md` | novo modo de falha, expandir eixo, adicionar linha na tabela |
| `template` | `templates/*.json` | ajustar default específico, adicionar `ask_before`, atualizar `example_answers` |
| `checklist` | `schemas/prompt-spec.json` `x-imagegem` | nova regra de coerência, novo item de checklist, ajustar limiar |
| `rule` | `src/imagegem/check.py` | novo `check` implementando uma regra declarada |
| `client` | `src/imagegem/clients/*` | mudança de envelope, retry, header |
| `docs` | qualquer `docs/*` | esclarecimento, contra-exemplo, nota |
| `none` | — | observação registrada sem ação; documenta que foi visto e ignorado |

Quando promovido, `promoted_to` recebe SHA do commit ou caminho do arquivo. Follow-ups sem `promoted_to` aparecem em `imagegem runs --pending`.

## Precedentes já registrados

`docs/04-aprendizados.md` foi aberto com dez aprendizados **retroativos** das E1–E5. Não é ficção: cada um cita o commit onde a evidência mora, e cada um resultou em mudança concreta no schema, na doutrina ou no cliente. Isso valida o formato — o mesmo modelo que capturou aprendizado retroativo é o que vai capturar aprendizado prospectivo daqui em diante.

## O que a E7 valida

- Rodar `imagegem submit` real com `GEMINI_API_KEY` e verificar que o registro aparece com `status=completed` e `client=gemini`.
- Rodar contra `HF_API_KEY_ID`/`SECRET` e verificar `correlation_id` no metadata.
- Preencher `review` com sinais reais observados nas imagens geradas e ver a primeira entrada não-retroativa em `docs/04-aprendizados.md`.
