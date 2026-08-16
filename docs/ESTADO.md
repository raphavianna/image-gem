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
| **E0 — Fontes** | **Concluída e aprovada.** `docs/00-fontes/`, commit `e95ac90` |
| **E1 — Doutrina de hiper-realismo** | **Próxima.** Aguardando início |
| E2 — Gramática do prompt | Não iniciada |
| E3 — Modalidades | Não iniciada |
| E4 — Biblioteca de templates | Não iniciada |
| E5 — Implementação | Não iniciada |
| E6 — Loop de retroalimentação | Não iniciada |
| E7 — Validação e fechamento | Não iniciada |

## Decisões travadas (não reabrir)

- Modelo alvo: **`gemini-3-pro-image`** (Nano Banana Pro). Alternativa de custo documentada: `gemini-3.1-flash-image`.
- Prompts gerados em **inglês**; documentação em **português do Brasil**.
- Entrega inclui Skill, documentação, CLI, servidor MCP e cliente Higgsfield completo.
- Gramática de blocos rotulados em maiúsculas + cauda `AVOID` curta. Justificada em `docs/00-fontes/04-guia-de-prompts-oficial.md`.
- Teto de **6 imagens de referência** para qualquer template que dependa de identidade preservada — não 14. Razão em `docs/00-fontes/03-capacidades.md`.

## Pendências externas

| Item | Estado | Bloqueia |
|---|---|---|
| `GEMINI_API_KEY` no environment | Pendente | Execução real da modalidade 4 |
| Egress da Higgsfield liberado | Em andamento — política do environment alterada para `Custom` | Modalidades 2 e 3 |
| Credenciais Higgsfield (`refresh_token`) | Pendente, depende do egress | Modalidade 3 |

Nenhuma delas bloqueia E1 a E4, que são documentação e templates.

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

Se a liberação de `ai.google.dev` funcionar, vale **revisitar a E0**: a lacuna L1 (preço por imagem), hoje a única crítica, passa a ser resolvível. Ver `docs/00-fontes/05-divergencias-e-lacunas.md`.

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
