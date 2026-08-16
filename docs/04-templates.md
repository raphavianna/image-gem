# Biblioteca de templates

Etapa **E4**. Cada template é uma instância parcial do schema canônico com defaults campo a campo, uma lista de campos de pergunta obrigatória, e um exemplo verificável. O piso pedido pelo prompt-mestre está entregue, mais dois templates que a doutrina exige mas que ele não enumerou.

## Piso e desvios

Do prompt-mestre:

> `templates/`: no mínimo retrato de estúdio, retrato editorial em céu aberto, corpo inteiro em locação, produto em estúdio, still de moda, e as variantes de edição, composição multi-referência e consistência de personagem.

Oito templates, todos entregues:

| # | ID | Regime | Pessoa? | Origem |
|---|---|---|---|---|
| 1 | `retrato-estudio` | generation | sim | exemplo 1 do prompt-mestre |
| 2 | `retrato-ceu-aberto` | generation | sim | exemplo 2 do prompt-mestre, instanciado por completo |
| 3 | `corpo-inteiro-locacao` | generation | sim | novo |
| 4 | `produto-estudio` | generation | não | exemplo 4 do prompt-mestre |
| 5 | `still-moda` | generation | não | novo |
| 6 | `edicao-troca-fundo` | edit | sim | exemplo 3 do prompt-mestre |
| 7 | `composicao-multi-referencia` | composition | sim | novo, deriva da seção 5 da doutrina |
| 8 | `consistencia-personagem` | generation | sim | novo, deriva da seção 5 da doutrina |

Os oito passam o checklist com respostas de exemplo, medidas reais:

| Template | Corpo | Cauda | Faixa aplicada |
|---|---|---|---|
| `retrato-estudio` | 620 | 28 | 500–650 (geração com pessoa) |
| `retrato-ceu-aberto` | 641 | 37 | 500–650 |
| `corpo-inteiro-locacao` | 639 | 37 | 500–650 |
| `produto-estudio` | 549 | 26 | 350–560 (geração sem pessoa) |
| `still-moda` | 476 | 31 | 350–560 |
| `edicao-troca-fundo` | 290 | 42 | 250–400 (edição) |
| `composicao-multi-referencia` | 456 | 45 | **350–560 (ancorado em referência)** |
| `consistencia-personagem` | 453 | 45 | **350–560 (ancorado em referência)** |

## Formato

Um template é o schema canônico com uma camada `ask_before[]` por cima. Não é um subformato — é o mesmo formato, com dois blocos de auditoria:

```jsonc
{
  "template_id":  "retrato-estudio",
  "regime":       "generation",
  "has_person":   true,
  "ask_before": [
    { "field": "subject.description", "prompt": "..." },
    ...
  ],
  "defaults": { /* spec parcial */ },
  "example_answers": { /* preenchimento de teste */ }
}
```

A decisão de reaproveitar o schema em vez de criar um formato próprio de template evita divergência entre "o que o template diz" e "o que o spec exige".

## Regra dura: nada de default implícito

`resolve()` levanta `ValueError` se qualquer `ask_before` fica sem resposta. Isso implementa a **regra de pedidos subespecificados** do prompt-mestre: características físicas do sujeito, proporção, uso final e presença de referência **sempre** vêm do usuário. O que não é obrigatório vem do template. Nada é default silencioso.

`example_answers` existe **só para o teste automático** de cada template — não é usado no fluxo real. Isso garante que "o template passa o checklist" seja verificável sem chamada humana.

## Auditoria de origem

Toda geração registra em `meta.defaults_applied[]` os caminhos que vieram do template em vez do usuário. É a diferença entre "o usuário pediu" e "o template decidiu" — pré-requisito para o loop da E6 poder correlacionar aparência de saída com escolha de default.

Exemplo, após resolver o template 1:

```json
"defaults_applied": [
  { "field": "camera.body",           "source": "template:retrato-estudio" },
  { "field": "camera.focal_length_mm","source": "template:retrato-estudio" },
  { "field": "camera.aperture_f",     "source": "template:retrato-estudio" },
  { "field": "lighting.sources.0.modifier", "source": "template:retrato-estudio" },
  ...
]
```

O caminho `subject.description`, que veio da resposta do usuário, **não** aparece.

## O que a instanciação encontrou

Duas surpresas estruturais durante a E4, que mudaram o schema:

### 1. `character.references_urls` e `edit.source_urls`

Os renderizadores das modalidades 3 e 4 já liam desses campos na E3, mas eles não estavam declarados no schema. Enquanto os exemplos eram só descrição, isso passou; os templates de composição e consistência precisam declarar URLs de referência ou os campos ficam órfãos. Ambos foram adicionados como opcionais.

### 2. Faixa de densidade "ancorada em referência"

Templates 7 e 8 rendem ~455 palavras — legitimamente menos, porque muitos campos apontam para a referência em vez de redeclarar sujeito, pele, vestuário e luz. Análogo ao que a edição faz. Cair na faixa de "geração com pessoa" (500–650) reprovaria os dois com prompt fisicamente correto.

A decisão foi **abrir uma quarta faixa por atributo, não por regime**:

```
quando: character.references_urls não vazio
faixa:  350–560
razão:  o mecanismo que reduz o texto é a referência externa, não o regime
```

A faixa tem **prioridade sobre o regime**. Cobre composição multi-referência (regime `composition`) e consistência de personagem (regime `generation`) sob o mesmo critério estrutural.

Codificada em `x-imagegem.orcamento_densidade.faixas[]`, com `quando` explícito. `faixa_de_densidade()` no validador consulta esse campo primeiro.

## Templates de identidade e a política de conteúdo

O prompt-mestre veta gerar imagens fotorrealistas de pessoas reais identificáveis, **exceto** quando a própria pessoa é a referência fornecida pelo usuário. Os templates 7 e 8 respeitam isso:

- `subject.description` descreve traços genéricos, não identidade.
- `character.references_urls` recebe a imagem que o usuário fornece.
- `character.invariant` declara o que deve sobreviver da referência.
- Nenhum default do template menciona nome próprio.

A Skill da E5 valida esse contrato quando o pedido do usuário contém nome de pessoa real e a referência não está presente.

## Como rodar

```bash
# valida todos os 8 templates com seus example_answers
python3 templates/_resolver.py

# valida um só
python3 templates/_resolver.py templates/retrato-estudio.json
```

## O que fica para as etapas seguintes

- **E5** implementa a Skill que roteia o pedido em linguagem natural para o template correto (via `aliases`), coleta as respostas do `ask_before`, chama `resolve()`, e passa para o renderizador da modalidade escolhida.
- **E6** consome `meta.defaults_applied[]` no registro `runs/` para correlacionar aparência de saída com escolha de default — a base para promover correções recorrentes para a doutrina ou para os templates.
- **E7** valida um template por chamada real com credencial em cada modalidade.
