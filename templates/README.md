# Biblioteca de templates

Cada template é uma **especificação parcial** do schema canônico (E2): traz o que o template decide, deixa em `ask_before[]` o que o usuário precisa fornecer, e valida com o mesmo validador da E2.

## Formato

```jsonc
{
  "template_id":       "retrato-estudio",
  "template_version":  "1.0",
  "description":       "...",
  "regime":            "generation",
  "has_person":        true,
  "aliases":           ["headshot", "..."],
  "ask_before": [
    { "field": "subject.description", "prompt": "..." },
    ...
  ],
  "defaults": {
    // spec canônico parcial — tudo que o template decide
    "camera": { ... },
    "lighting": { ... },
    "render": { ... },
    ...
  },
  "example_answers": {
    "subject.description": "...",
    ...
  }
}
```

### Regra dura de resolução

O resolver **não inventa valores silenciosamente**. Se um `ask_before` fica sem resposta, `resolve()` levanta `ValueError`. Essa é a implementação direta da "regra de pedidos subespecificados" do prompt-mestre: o sistema pergunta antes de decidir.

`example_answers` existe só para o teste automático — no uso real, a Skill da E5 coleta as respostas do usuário.

### Auditoria de defaults

Toda geração registra em `meta.defaults_applied[]` os caminhos que vieram do template em vez do usuário. É a diferença entre "o usuário pediu" e "o template decidiu" — para o registro em `runs/` da E6 poder correlacionar aparência com escolha do template.

## Templates disponíveis

| ID | Regime | Pessoa? | Uso | Ancorado em |
|---|---|---|---|---|
| `retrato-estudio` | generation | sim | Perfil corporativo, capa editorial, retrato de imprensa | exemplo 1 do prompt-mestre |
| `retrato-ceu-aberto` | generation | sim | Editorial em locação, retrato de reportagem | exemplo 2 (resumido) do prompt-mestre |
| `corpo-inteiro-locacao` | generation | sim | Editorial de moda em rua, ensaio de campanha | novo |
| `produto-estudio` | generation | não | E-commerce premium, hero de landing | exemplo 4 do prompt-mestre |
| `still-moda` | generation | não | Catálogo editorial, look book, cover art | novo |
| `edicao-troca-fundo` | edit | sim | Mover retrato de estúdio para locação plausível | exemplo 3 do prompt-mestre |
| `composicao-multi-referencia` | composition | sim | Combinar sujeito + objeto + estilo | novo |
| `consistencia-personagem` | generation | sim | Nova pose/ângulo com identidade preservada | novo, deriva da doutrina seção 5 |

## Como rodar

```bash
# lista todos os templates
imagegem templates

# resolve template + example_answers para spec canônico
imagegem resolve retrato-estudio --out /tmp/spec.json

# valida o spec resultante contra o checklist
imagegem validate /tmp/spec.json

# suíte completa de regressão
python3 tests/test_pipeline.py
```

## Uso programático

```python
from imagegem import resolver, schema, check
from imagegem.render import renderiza_modalidade_1

template = schema.load_template("retrato-estudio")
answers = {
    "meta.user_request": "...",
    "subject.description": "...",
    "subject.asymmetries": ["...", "..."],
    ...
}
spec = resolver.resolve(template, answers)
falhas, corpo, cauda = check.validate(spec)
```
