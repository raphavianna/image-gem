#!/usr/bin/env python3
"""Testes do resolver de templates.

Coberturas críticas ausentes até a E7:
- `ValueError` quando falta resposta a `ask_before` — a Skill depende disso
  para nunca inventar valor silencioso.
- Trilha `meta.defaults_applied[]` correta.
- Overwrite: uma resposta do usuário substitui o default do template.
- Todos os 8 templates resolvem com seus `example_answers`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from imagegem import check, resolver, schema  # noqa: E402


def testa_falta_de_resposta_falha():
    template = schema.load_template("retrato-estudio")
    respostas_incompletas = {"meta.user_request": "só isso"}
    try:
        resolver.resolve(template, respostas_incompletas)
    except ValueError as e:
        assert "subject.description" in str(e) or "ask_before" in str(e).lower()
        return True
    return False


def testa_trilha_defaults_applied():
    template = schema.load_template("retrato-estudio")
    spec = resolver.resolve(template)
    trilha = spec["meta"].get("defaults_applied", [])
    # example_answers dessa template preenche subject.description entre outros —
    # esses caminhos NÃO devem aparecer como default.
    caminhos_do_usuario = set(template["example_answers"].keys())
    caminhos_no_trail = {t["field"] for t in trilha}
    intersecao = caminhos_do_usuario & caminhos_no_trail
    if intersecao:
        raise AssertionError(f"caminhos do usuário viraram default_applied: {intersecao}")
    # E camera.body veio do template — precisa estar na trilha.
    assert "camera.body" in caminhos_no_trail, "camera.body deveria estar em defaults_applied"
    return True


def testa_resposta_sobrescreve_default():
    template = schema.load_template("retrato-estudio")
    ans = dict(template["example_answers"])
    ans["camera.body"] = "Leica Q3"  # substitui o Phase One default
    spec = resolver.resolve(template, ans)
    assert spec["camera"]["body"] == "Leica Q3"
    return True


def testa_todos_os_templates_resolvem_e_validam():
    falhas = []
    for p in sorted(schema.TEMPLATES_DIR.glob("*.json")):
        template = schema.load_template(p.stem)
        try:
            spec = resolver.resolve(template)
        except Exception as e:
            falhas.append(f"{p.stem}: resolve falhou — {e}")
            continue
        problemas, _, _ = check.validate(spec)
        if problemas:
            falhas.append(f"{p.stem}: validate reprovou — {problemas[0]}")
    if falhas:
        raise AssertionError("\n  ".join([""] + falhas))
    return True


def main() -> int:
    testes = [
        ("resolve falha sem ask_before", testa_falta_de_resposta_falha),
        ("trilha defaults_applied", testa_trilha_defaults_applied),
        ("resposta sobrescreve default", testa_resposta_sobrescreve_default),
        ("8 templates resolvem e validam", testa_todos_os_templates_resolvem_e_validam),
    ]
    falhou = 0
    for nome, fn in testes:
        try:
            ok = fn()
            if not ok:
                falhou += 1
                print(f"  FALHA  {nome}  (retornou False)")
            else:
                print(f"  ok     {nome}")
        except AssertionError as e:
            falhou += 1
            print(f"  FALHA  {nome}  {e}")
        except Exception as e:
            falhou += 1
            print(f"  FALHA  {nome}  (exceção inesperada: {type(e).__name__}: {e})")
    print()
    if falhou:
        print(f"{falhou} problema(s).")
        return 1
    print(f"{len(testes)} testes passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
