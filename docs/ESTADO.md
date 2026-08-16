# Estado do projeto

Arquivo de retomada. Leia isto primeiro ao abrir uma sessão nova.

Atualizado em: **2026-08-16**

## Como retomar

1. Leia `docs/PROMPT-MESTRE.md` — é a constituição do projeto: papel, doutrina, checklist de emissão, gramática, as quatro modalidades e a decomposição em etapas.
2. Leia este arquivo para saber onde o trabalho parou.
3. Continue da próxima etapa não aprovada, respeitando o gate: uma etapa por vez, parando para aprovação.

## Progresso

| Etapa | Estado |
|---|---|
| **E0 — Fontes** | **Concluída e aprovada.** `docs/00-fontes/`, commit `e95ac90`. **Revisada em 2026-08-16** com a fonte primária liberada — ver `00-fontes/06-fonte-primaria-ai-google-dev.md` |
| **E1 — Doutrina de hiper-realismo** | **Concluída e aprovada.** `docs/01-doutrina-hiper-realismo.md`, commit `310c503` |
| **E2 — Gramática do prompt** | **Concluída, aguardando aprovação no gate.** `docs/02-gramatica-do-prompt.md`, `schemas/` |
| E3 — Modalidades | **Próxima.** Aguardando aprovação de E2 |
| E4 — Biblioteca de templates | Não iniciada |
| E5 — Implementação | Não iniciada |
| E6 — Loop de retroalimentação | Não iniciada |
| E7 — Validação e fechamento | Não iniciada |

## Decisões travadas (não reabrir)

- Modelo alvo: **`gemini-3-pro-image`** (Nano Banana Pro). Alternativa de custo documentada: `gemini-3.1-flash-image`.
- Prompts gerados em **inglês**; documentação em **português do Brasil**.
- Entrega inclui Skill, documentação, CLI, servidor MCP e cliente Higgsfield completo.
- Gramática de blocos rotulados em maiúsculas + cauda `AVOID` curta. Justificada em `docs/00-fontes/04-guia-de-prompts-oficial.md`. Critério de admissão à cauda formalizado em `docs/01-doutrina-hiper-realismo.md`, seção 6.
- Teto de **5 imagens de referência** para qualquer template que dependa de identidade preservada. A documentação primeiro-parte decompõe os 14 em orçamentos por papel: **5 personagens** para identidade, **6 objetos** em alta fidelidade, **3 referências de estilo**. Razão em `docs/00-fontes/05-divergencias-e-lacunas.md`, D2. *Corrigido em 2026-08-16 e aprovado pelo autor no gate de E1; a versão anterior desta decisão dizia 6, que era o orçamento de objetos lido como se valesse para identidade.*
- Orçamento de densidade **por regime**, não banda única: 500–650 para geração com pessoa, 350–560 sem pessoa, 250–400 para edição. A banda 350–500 do prompt-mestre reprovava dois dos três exemplos âncora, e o "~450" atribuído ao exemplo 1 erra por ~150 palavras — ele tem 597. Derivação em `docs/02-gramatica-do-prompt.md`, seção 3. *Decidido pelo autor no gate de E2, em 2026-08-16.*
- Resolução padrão de saída: **2K**. 1K e 2K consomem os mesmos 1120 tokens e custam o mesmo (`$0,134`); 4K custa `$0,24`. Fonte em `docs/00-fontes/06-fonte-primaria-ai-google-dev.md`.

## Pendências externas

| Item | Estado | Bloqueia |
|---|---|---|
| `GEMINI_API_KEY` no environment | **Pendente** | Execução real da modalidade 4; resolução da lacuna L3 (`person_generation`) |
| Egress da Higgsfield | **Resolvido em 2026-08-16** — todos os hosts respondem | — |
| Egress de `ai.google.dev` | **Resolvido em 2026-08-16** — fonte primária lida, L1/L2/L4/L6 fechadas | — |
| Credenciais Higgsfield (`refresh_token`) | **Pendente** — não depende mais do egress | Modalidade 3 |
| Documentação da API Higgsfield extraída | Pendente — rede liberada, extração pertence à E5 | Cliente Higgsfield completo |

Nenhuma delas bloqueia E2 a E4, que são schema, documentação e templates.

## Ambiente

Environment renomeado para `image-gem`, nível de rede **Custom**, com a lista padrão de package managers incluída. Domínios adicionados:

```
*.higgsfield.ai
*.clerk.accounts.dev
ai.google.dev
docs.cloud.google.com
generativelanguage.googleapis.com
cloud.google.com
```

Validação numa sessão nova:

```bash
for h in clerk.higgsfield.ai oriented-jay-78.clerk.accounts.dev \
         fnf-api-gw.higgsfield.ai fnf.higgsfield.ai \
         cdn.higgsfield.ai static.higgsfield.ai \
         ai.google.dev docs.cloud.google.com; do
  printf '%-42s -> ' "$h"
  curl -sS -o /dev/null -w '%{http_code}\n' --max-time 15 "https://$h" 2>&1 | tail -1
done
```

Qualquer código HTTP significa liberado. `000` significa que o túnel CONNECT foi recusado — ainda bloqueado.

**Último resultado, 2026-08-16 (abertura da sessão de E1): todos liberados.**

| Host | Código |
|---|---|
| `clerk.higgsfield.ai` | 200 |
| `oriented-jay-78.clerk.accounts.dev` | 200 |
| `fnf-api-gw.higgsfield.ai` | 404 |
| `fnf.higgsfield.ai` | 404 |
| `cdn.higgsfield.ai` | 404 |
| `static.higgsfield.ai` | 404 |
| `ai.google.dev` | 200 |
| `docs.cloud.google.com` | 200 |

A E0 **foi revisitada** em consequência disso, conforme previsto: a lacuna crítica L1 (preço) está fechada, junto com L2, L4 e L6, e as divergências D1 e D2. A revisão corrigiu uma decisão travada — o teto de referências de identidade. Ver `docs/00-fontes/06-fonte-primaria-ai-google-dev.md` e `05-divergencias-e-lacunas.md`.

## Instalação da CLI da Higgsfield

O comando padrão **trava** neste ambiente: o `postinstall` baixa o binário com `https.get` do Node, que não lê `HTTPS_PROXY`. O caminho que funciona:

```bash
npm i -g --ignore-scripts @higgsfield/cli
ROOT=$(npm root -g)/@higgsfield/cli
mkdir -p "$ROOT/vendor"
curl -sSL -o /tmp/hf.tar.gz \
  https://github.com/higgsfield-ai/cli/releases/download/v1.1.23/hf_1.1.23_linux_amd64.tar.gz
tar xzf /tmp/hf.tar.gz -C "$ROOT/vendor" hf
chmod 755 "$ROOT/vendor/hf"
printf '{"install_method":"npm","package_manager":"npm","package_name":"@higgsfield/cli","version":"1.1.23"}\n' \
  > "$ROOT/vendor/install.json"
```

Candidato a virar setup script do environment em E5.
