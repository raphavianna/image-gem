"""Resolver de templates — converte template + respostas em spec canônico.

Um template é um spec parcial com camada `ask_before[]` por cima. O resolver:
    1. Aplica respostas do usuário sobre os defaults por caminho de campo.
    2. Grava trilha auditável em `meta.defaults_applied[]` — a diferença entre
       "o usuário pediu" e "o template decidiu".
    3. Recusa a resolver se qualquer `ask_before` fica sem resposta — regra dura
       do prompt-mestre, nada de default silencioso.
"""

from __future__ import annotations

import copy
from typing import Any


def _set_por_caminho(alvo: dict, caminho: str, valor: Any) -> None:
    """Escreve `valor` em `alvo` seguindo `caminho` no formato `a.b.c`.

    Cria dicionários intermediários. Índices numéricos escrevem em listas.
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


def _lista_caminhos_folhas(obj, prefixo="") -> list[str]:
    """Todos os caminhos que apontam para valor escalar ou lista de escalares."""
    if isinstance(obj, dict):
        out = []
        for k, v in obj.items():
            out += _lista_caminhos_folhas(v, f"{prefixo}.{k}" if prefixo else k)
        return out
    if isinstance(obj, list):
        if not obj or all(not isinstance(x, (dict, list)) for x in obj):
            return [prefixo] if prefixo else []
        out = []
        for i, v in enumerate(obj):
            out += _lista_caminhos_folhas(v, f"{prefixo}.{i}")
        return out
    return [prefixo] if prefixo else []


def resolve(template: dict, answers: dict | None = None) -> dict:
    """Converte template + respostas em spec canônico.

    Se `answers` for None, usa `template.example_answers` — modo teste.
    Levanta `ValueError` se algum `ask_before` fica sem resposta.
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

    for caminho, valor in respostas.items():
        _set_por_caminho(spec, caminho, valor)

    # Trilha de auditoria: caminhos que só vêm do template entram em
    # meta.defaults_applied[]. Ignora quem foi sobrescrito por resposta.
    aplicados = [c for c in _lista_caminhos_folhas(template.get("defaults", {})) if c not in respostas]
    meta = spec.setdefault("meta", {})
    meta["template"] = template["template_id"]
    if aplicados:
        meta["defaults_applied"] = [
            {"field": c, "source": f"template:{template['template_id']}"} for c in aplicados
        ]

    return spec
