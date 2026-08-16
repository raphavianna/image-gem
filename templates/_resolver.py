#!/usr/bin/env python3
"""Resolver de templates — etapa E4.

Um template é uma **especificação parcial** do schema canônico:

- `defaults` traz tudo que o template decide (câmera, luz, revelação, cauda).
- `ask_before` enumera o que o template **exige** que o usuário forneça.
- `example_answers` é um preenchimento de exemplo dos `ask_before`, usado só
  para o teste automático — o pedido real do usuário substitui.

O resolver faz três coisas, nesta ordem:

1. Aplica `example_answers` (ou `answers` reais) sobre `defaults` por
   deep-merge por caminho de campo (`camera.iso`, `subject.description`).
2. Preenche `meta.defaults_applied[]` com todo caminho resolvido pelo default do
   template — a auditoria de "o usuário pediu" × "o template decidiu" que a
   regra de pedidos subespecificados do prompt-mestre exige.
3. Devolve o spec pronto para o validador da E2.

Uso como biblioteca:
    spec = resolve(template, answers)

Uso como CLI de teste:
    python3 templates/_resolver.py           # resolve todos e valida
    python3 templates/_resolver.py foo.json  # resolve e valida um
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "schemas"))

from validador import SCHEMA_PATH, valida  # noqa: E402

RAIZ = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- #
# Utilitários de caminho                                                      #
# --------------------------------------------------------------------------- #


def _set_por_caminho(alvo: dict, caminho: str, valor: Any) -> None:
    """Escreve `valor` em `alvo` seguindo `caminho` no formato `a.b.c`.

    Cria dicionários intermediários. Índices numéricos escrevem em listas,
    criando slots faltantes preenchidos com dicionários vazios.
    """
    partes = caminho.split(".")
    no = alvo
    for i, chave in enumerate(partes[:-1]):
        proxima = partes[i + 1]
        if chave.isdigit():
            idx = int(chave)
            while len(no) <= idx:
                no.append({} if not proxima.isdigit() else [])
            no = no[idx]
        else:
            if chave not in no or not isinstance(no[chave], (dict, list)):
                no[chave] = [] if proxima.isdigit() else {}
            no = no[chave]
    ultima = partes[-1]
    if ultima.isdigit():
        idx = int(ultima)
        while len(no) <= idx:
            no.append(None)
        no[idx] = valor
    else:
        no[ultima] = valor


def _get_por_caminho(alvo: dict, caminho: str, ausente=None) -> Any:
    """Lê `caminho` de `alvo`; devolve `ausente` se algum passo faltar."""
    no = alvo
    for parte in caminho.split("."):
        if parte.isdigit():
            idx = int(parte)
            if not isinstance(no, list) or idx >= len(no):
                return ausente
            no = no[idx]
        else:
            if not isinstance(no, dict) or parte not in no:
                return ausente
            no = no[parte]
    return no


# --------------------------------------------------------------------------- #
# Resolver                                                                    #
# --------------------------------------------------------------------------- #


def resolve(template: dict, answers: dict | None = None) -> dict:
    """Converte template + respostas em spec.

    `answers` é dict `{caminho.no.spec: valor}`. Qualquer `ask_before` sem
    resposta vira `ValueError` — não inventamos silenciosamente, é a regra
    dura do prompt-mestre.
    """
    respostas = answers if answers is not None else template.get("example_answers", {}) or {}

    obrigatorios = [item["field"] for item in template.get("ask_before", [])]
    faltando = [c for c in obrigatorios if c not in respostas]
    if faltando:
        raise ValueError(
            f"template {template['template_id']!r} exige respostas para "
            f"{faltando} — nenhum default implícito é aplicado"
        )

    spec = copy.deepcopy(template.get("defaults", {}))

    # Aplica respostas do usuário.
    for caminho, valor in respostas.items():
        _set_por_caminho(spec, caminho, valor)

    # Trilha de auditoria: cada caminho que só vem do template entra em
    # meta.defaults_applied[]. Percorre o defaults e ignora quem foi
    # sobrescrito por resposta.
    aplicados = _lista_caminhos_folhas(template.get("defaults", {}))
    aplicados = [c for c in aplicados if c not in respostas]
    meta = spec.setdefault("meta", {})
    meta["template"] = template["template_id"]
    if aplicados:
        meta["defaults_applied"] = [
            {"field": c, "source": f"template:{template['template_id']}"} for c in aplicados
        ]

    return spec


def _lista_caminhos_folhas(obj, prefixo=""):
    """Todos os caminhos que apontam para valor escalar ou lista de escalares."""
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            out += _lista_caminhos_folhas(v, f"{prefixo}.{k}" if prefixo else k)
        return out
    if isinstance(obj, list):
        # Listas de escalares (assimetrias, marcas, avoid) são folhas.
        if not obj or all(not isinstance(x, (dict, list)) for x in obj):
            return [prefixo] if prefixo else []
        # Lista de dicts (wardrobe, sources) é enumerada por índice.
        out = []
        for i, v in enumerate(obj):
            out += _lista_caminhos_folhas(v, f"{prefixo}.{i}")
        return out
    return [prefixo] if prefixo else []


# --------------------------------------------------------------------------- #
# Execução como CLI de teste                                                   #
# --------------------------------------------------------------------------- #


def main(argv):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    alvos = (
        [Path(a) for a in argv[1:]]
        if len(argv) > 1
        else sorted(p for p in RAIZ.glob("*.json"))
    )

    codigo = 0
    for caminho in alvos:
        template = json.loads(caminho.read_text(encoding="utf-8"))
        print("=" * 78)
        print(f"TEMPLATE: {caminho.name}  ({template['template_id']})")
        print(f"  regime={template['defaults']['scene']['regime']}  "
              f"has_person={template['defaults']['scene']['has_person']}  "
              f"ask_before={len(template.get('ask_before', []))} campo(s)")

        try:
            spec = resolve(template)
        except Exception as e:
            codigo = 1
            print(f"  RESOLVE FALHOU: {e}")
            continue

        falhas, corpo, cauda = valida(spec, schema)
        if falhas:
            codigo = 1
            print(f"  VALIDA FALHOU — {len(falhas)} falha(s):")
            for f in falhas:
                print(f"    - {f}")
        else:
            n = len(corpo.split())
            print(f"  OK — corpo {n}p, cauda {len(cauda.split())}p")
    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv))
