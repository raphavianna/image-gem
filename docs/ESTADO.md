# Estado do projeto

Arquivo de retomada. Leia isto primeiro ao abrir uma sessão nova.

Atualizado em: **2026-08-16**

> **Todas as sete etapas concluídas e aprovadas.** O projeto está em estado de entrega. Para retomar, comece pelo `README.md` e pela `docs/07-validacao/`. As pendências permanentes desta entrega são L3 e L7 — ambas exigem credencial real (`GEMINI_API_KEY` e `HF_API_KEY_ID`/`SECRET`) e produziriam a primeira entrada não-retroativa em `docs/04-aprendizados.md`.

## Como retomar

1. Leia `docs/PROMPT-MESTRE.md` — é a constituição do projeto: papel, doutrina, checklist de emissão, gramática, as quatro modalidades e a decomposição em etapas.
2. Leia este arquivo para saber onde o trabalho parou.
3. Continue da próxima etapa não aprovada, respeitando o gate: uma etapa por vez, parando para aprovação.

## Progresso

| Etapa | Estado |
|---|---|
| **E0 — Fontes** | **Concluída e aprovada.** `docs/00-fontes/`, commit `e95ac90`. **Revisada em 2026-08-16** com a fonte primária liberada — ver `00-fontes/06-fonte-primaria-ai-google-dev.md` |
| **E1 — Doutrina de hiper-realismo** | **Concluída e aprovada.** `docs/01-doutrina-hiper-realismo.md`, commit `310c503` |
| **E2 — Gramática do prompt** | **Concluída e aprovada.** `docs/02-gramatica-do-prompt.md`, `schemas/`, commit `ea52f57` |
| **E3 — Modalidades** | **Concluída e aprovada.** `docs/03-modalidades/`, commit `4f95674` |
| **E4 — Biblioteca de templates** | **Concluída e aprovada.** `templates/`, commit `62fd37d` |
| **E5 — Implementação** | **Concluída e aprovada.** `src/imagegem/`, `mcp_server/`, `.claude/skills/imagegem/`, commit `1cad865` |
| **E6 — Loop de retroalimentação** | **Concluída e aprovada.** `schemas/run-record.json`, `docs/04-aprendizados.md`, `docs/06-loop.md`, commit `6b08674` |
| **E7 — Validação e fechamento** | **Concluída.** `README.md` na raiz, `docs/07-validacao/` com bateria executada — 27 comandos com exit 0 |

## Decisões travadas (não reabrir)

- Modelo alvo: **`gemini-3-pro-image`** (Nano Banana Pro). Alternativa de custo documentada: `gemini-3.1-flash-image`.
- Prompts gerados em **inglês**; documentação em **português do Brasil**.
- Entrega inclui Skill, documentação, CLI, servidor MCP e cliente Higgsfield completo.
- Gramática de blocos rotulados em maiúsculas + cauda `AVOID` curta. Justificada em `docs/00-fontes/04-guia-de-prompts-oficial.md`. Critério de admissão à cauda formalizado em `docs/01-doutrina-hiper-realismo.md`, seção 6.
- Teto de **5 imagens de referência** para qualquer template que dependa de identidade preservada. A documentação primeiro-parte decompõe os 14 em orçamentos por papel: **5 personagens** para identidade, **6 objetos** em alta fidelidade, **3 referências de estilo**. Razão em `docs/00-fontes/05-divergencias-e-lacunas.md`, D2. *Corrigido em 2026-08-16 e aprovado pelo autor no gate de E1; a versão anterior desta decisão dizia 6, que era o orçamento de objetos lido como se valesse para identidade.*
- Orçamento de densidade **por regime**, não banda única: 500–650 para geração com pessoa, 350–560 sem pessoa, 250–400 para edição. A banda 350–500 do prompt-mestre reprovava dois dos três exemplos âncora, e o "~450" atribuído ao exemplo 1 erra por ~150 palavras — ele tem 597. Derivação em `docs/02-gramatica-do-prompt.md`, seção 3. *Decidido pelo autor no gate de E2, em 2026-08-16.*
- **Faixa "ancorada em referência" (350–560) com prioridade sobre a faixa por regime**, aplicada quando `character.references_urls` não é vazio. Cobre composição multi-referência e consistência de personagem — os dois têm menos texto legítimo porque muitos campos apontam para a referência em vez de redeclarar. Derivação em `docs/04-templates.md`. *Adicionado em modo auto durante a E4, em 2026-08-16.*
- Resolução padrão de saída: **2K**. 1K e 2K consomem os mesmos 1120 tokens e custam o mesmo (`$0,134`); 4K custa `$0,24`. Fonte em `docs/00-fontes/06-fonte-primaria-ai-google-dev.md`.

## Pendências externas

| Item | Estado | Bloqueia |
|---|---|---|
| `GEMINI_API_KEY` no environment | **Pendente** | Execução real da modalidade 4; resolução das lacunas L3 (`person_generation`) e L7 (variante do `/nano-banana`) |
| Egress da Higgsfield | **Resolvido em 2026-08-16** — todos os hosts respondem | — |
| Egress de `ai.google.dev` | **Resolvido em 2026-08-16** — fonte primária lida, L1/L2/L4/L6 fechadas | — |
| **Credenciais Higgsfield (`HF_API_KEY_ID` + `HF_API_KEY_SECRET`)** | **Pendente** — a extração `[HF]` na E3 corrigiu o formato antes assumido de `refresh_token` | Modalidade 3 em execução real |
| Documentação da API Higgsfield extraída | **Resolvido em 2026-08-16, na E3** — ver `docs/00-fontes/07-fonte-primaria-higgsfield.md` | — |

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
