# Modalidade 2 — Interface Higgsfield

Texto colável para o painel `cloud.higgsfield.ai`, mais o mapeamento dos controles nativos do painel. É a modalidade de quem já opera na Higgsfield e quer manter o fluxo.

> **Aviso — L7 aberta.** A Higgsfield expõe `/nano-banana` como endpoint único, sem distinguir Pro (`gemini-3-pro-image`) de Flash (`gemini-3.1-flash-image`) na URL nem em parâmetro documentado. Toda referência a "target: Nano Banana Pro" nesta página é **assumption**, não fato verificado. Se a Higgsfield estiver roteando para Flash em contas standard, a qualidade entregue é inferior à prometida — silenciosamente. Detalhes em `docs/00-fontes/05-divergencias-e-lacunas.md` L7. Só resolve empiricamente com credencial e comparação contra a modalidade 4.

## O que muda em relação à modalidade 1

O corpo textual é **o mesmo**, com uma diferença: **a proporção sai do texto e vai para o controle da interface**. A Higgsfield expõe `aspect_ratio` como controle nativo, então verbalizar no prompt é redundante e a duplicação pode confundir o modelo — o campo estruturado vence o texto.

A resolução **não é controle exposto** em `/nano-banana`, ao contrário da Gemini API e do próprio SOUL da Higgsfield que expõem `2K` e `4K`. Documentado em `docs/00-fontes/07-fonte-primaria-higgsfield.md`, seção 2. Consequência: se você precisa de 4K auditável, use a modalidade 4.

## Renderizador

```python
def renderiza_modalidade_2(spec): ...
```

Devolve três coisas:

1. **Corpo** — a mesma prosa em blocos rotulados da modalidade 1, sem a proporção no cabeçalho.
2. **Cauda** — `AVOID: ...`.
3. **Controles** — dicionário com os valores para preencher no painel.

## Mapeamento dos controles

Do OpenAPI `[HF]`, `POST /nano-banana`:

| Controle no painel | Origem no schema | Observação |
|---|---|---|
| Model | fixo — Nano Banana | endpoint `/nano-banana`; **variante Pro vs Flash é assumption, não fato** — L7, ver aviso abaixo |
| Prompt | corpo + cauda concatenados | copiado literalmente |
| Aspect ratio | `output.aspect_ratio` | dez valores mais `auto`; `auto` herda do input em modo de edição |
| Number of images | 1 por default | máximo 4 |
| Output format | JPEG por default | também aceita PNG |
| Input images | uploads no painel, até 8 | limite mais apertado que os 14 do Gemini nativo |

**Enum de aspect ratio aceito por `/nano-banana`:** `auto`, `1:1`, `4:3`, `3:4`, `3:2`, `2:3`, `5:4`, `4:5`, `16:9`, `9:16`, `21:9`.

Este é um superconjunto dos dez valores do Gemini API — o extra é `auto`. O renderizador valida contra esse enum e falha com mensagem explícita se o `output.aspect_ratio` do spec estiver fora.

## Exemplo ponta a ponta

Instância: `schemas/exemplos/exemplo-1-retrato-estudio.json`.
Prompt renderizado: `exemplos/exemplo-1-retrato-estudio-mod2.txt`.

O texto colável começa **sem** o sufixo de proporção do cabeçalho:

```
Editorial studio portrait, single subject, waist-up.

SUBJECT. A 34-year-old woman with warm olive skin, dark brown eyes and
[...]
```

E os controles a preencher no painel:

```json
{
  "model":         "Nano Banana (endpoint /nano-banana)",
  "aspect_ratio":  "4:5",
  "num_images":    1,
  "output_format": "jpeg",
  "input_images":  []
}
```

## Refinamento iterativo no painel

A Higgsfield mantém histórico de gerações por conta `[HF]`. Iteração conversacional segue o mesmo padrão da modalidade 1 — endereçar um bloco por vez, colar o prompt inteiro, mudar só o que precisa mudar. O painel não tem chat verdadeiro, então cada refinamento é uma nova submissão; as *thought signatures* do Gemini 3 mencionadas em `[CB]` não se acumulam por esse caminho.

## Retenção

Literal `[HF]`, `concepts/requests.md`:

> Output URLs are retained for at least seven days. Copy completed media to your own storage if you need it for longer.

O painel oferece download e histórico visível. Para produção auditável, use a modalidade 3, que dá controle programático.

## Custos

O painel exibe custo estimado por geração antes de disparar. O endpoint `POST /estimate/nano-banana` responde ao mesmo cálculo, disponível na modalidade 3 sem consumir créditos. Modalidade 2 usa apenas o valor mostrado pelo painel.
