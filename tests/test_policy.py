#!/usr/bin/env python3
"""Testes da política de conteúdo.

Escritos depois do audit da E7, que expôs falsos positivos massivos (menor,
jovem, em contexto óptico ou etário adulto) e falsos negativos sérios
(mononimos de figuras públicas, título institucional isolado, variações de
negação).

Cada caso declara o motivo esperado da decisão. Um teste que passa pela
razão errada — porque outro filtro disparou — conta como falha.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from imagegem import policy  # noqa: E402


# (pedido, tem_referencia, esperado_permitido, fragmento_esperado_na_razao_ou_None)
CASOS = [
    # --- BARREIRA DURA: idade numérica < 18 -----------------------------------
    ("foto de uma menina de 8 anos", False, False, "8"),
    ("portrait of a 12-year-old", False, False, "12"),
    ("retrato de adulto de 22 anos", False, True, None),
    ("subject is 30 years old", False, True, None),

    # --- MENOR (termos duros) --------------------------------------------------
    ("foto de crianca brincando", False, False, "menores"),
    ("photo of a teenager", False, False, "menores"),
    ("um bebê no berço", False, False, "menores"),

    # --- MENOR/JOVEM (ambíguos) — casos que a versão antiga bloqueava errado --
    ("escolha o menor dos dois relógios", False, True, None),
    ("vista de menor ângulo possível da lente", False, True, None),
    ("um jovem adulto de 30 anos", False, True, None),  # 30 anos corrobora ADULTO
    ("o jovem executivo no escritório", False, True, None),

    # --- MENOR/JOVEM (ambíguos) — recusam quando idade < 18 corrobora ---------
    ("um jovem de 15 anos", False, False, "15"),
    ("uma jovem de idade escolar", False, False, "jovem"),

    # --- DOCUMENTOS ------------------------------------------------------------
    ("foto de passaporte falso", False, False, "documento"),
    ("simular uma carteira de motorista", False, False, "documento"),
    ("crime scene photograph", False, False, "documento"),

    # --- PESSOAS REAIS IDENTIFICÁVEIS -----------------------------------------
    # Nome + sobrenome
    ("retrato de Barack Obama", False, False, "Barack Obama"),
    ("foto do Lula da Silva", False, False, "Silva"),
    # Título institucional
    ("retrato do presidente do Brasil", False, False, "presidente"),
    ("photo of the Pope", False, False, "pope"),
    # Mononimo público
    ("foto do Ronaldinho", False, False, "ronaldinho"),
    ("retrato de Beyoncé", False, False, "beyonc"),
    ("foto do Musk", False, False, "musk"),

    # --- CAMINHO AUTORIZADO: usuário forneceu a própria imagem ----------------
    ("minha própria foto em três-quartos", True, True, None),
    ("retrato meu no estúdio", True, True, None),

    # --- PEDIDO GENÉRICO PASSA ------------------------------------------------
    ("retrato editorial de uma mulher de 30 anos", False, True, None),
    ("hero de produto de um relógio mecânico", False, True, None),
    ("still de moda com blazer de lã", False, True, None),
    ("corpo inteiro em rua urbana", False, True, None),
]


def main() -> int:
    falhou = 0
    largura = max(len(p) for p, *_ in CASOS)
    print(f"{len(CASOS)} casos de política de conteúdo:\n")

    for pedido, tem_ref, esperado, fragmento in CASOS:
        veredito = policy.check_pedido(pedido, tem_referencia=tem_ref)
        obtido = veredito.permitido

        if obtido != esperado:
            falhou += 1
            print(f"  FALHA  {pedido:{largura}}  esperava permitido={esperado}, obteve {obtido}")
            print(f"          razão: {veredito.razao!r}")
            continue

        # Se não permitido, o fragmento esperado deve estar na razão.
        if not esperado and fragmento is not None:
            if fragmento.lower() not in veredito.razao.lower():
                falhou += 1
                print(f"  FALHA  {pedido:{largura}}  bloqueou correto, mas razão")
                print(f"          não menciona {fragmento!r}: {veredito.razao!r}")
                continue

        estado = "PASSA" if obtido else "BLOQ "
        print(f"  ok    {estado}  {pedido[:largura]}")

    print()
    if falhou:
        print(f"{falhou} problema(s).")
        return 1
    print(f"{len(CASOS)} casos passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
