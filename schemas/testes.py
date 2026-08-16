#!/usr/bin/env python3
"""Testes negativos do schema canônico — etapa E2.

O validador aprovar os dois exemplos âncora não prova que ele valida coisa
alguma: um validador que sempre devolve "aprovado" faz o mesmo. Estes testes
partem de uma instância válida, introduzem uma violação por vez, e exigem que a
regra correspondente dispare.

Cada caso declara o fragmento que precisa aparecer na mensagem de falha, de modo
que um teste passar por acidente — porque outra regra disparou — conta como
falha do teste.

Uso:
    python3 schemas/testes.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validador import SCHEMA_PATH, valida  # noqa: E402

RAIZ = Path(__file__).resolve().parent
BASE_PESSOA = RAIZ / "exemplos" / "exemplo-1-retrato-estudio.json"
BASE_PRODUTO = RAIZ / "exemplos" / "exemplo-4-produto-estudio.json"


def m_iso(spec):
    """C1 — ISO alto com grão descrito como de ISO baixo."""
    spec["camera"]["iso"] = 3200


def m_abertura(spec):
    """C2 — abertura fechada com queda de foco declarada."""
    spec["camera"]["aperture_f"] = 22


def m_obturador(spec):
    """C3 — velocidade lenta sem arrasto declarado."""
    spec["camera"]["shutter"] = "1/15s"


def m_penumbra(spec):
    """C4 — fonte pequena e distante com penumbra larga."""
    spec["lighting"]["sources"][0]["size_m"] = 0.3
    spec["lighting"]["sources"][0]["distance_m"] = 3.0


def m_catchlight(spec):
    """C5 — catchlight redondo sob octabox."""
    spec["lighting"]["catchlight"]["shape"] = "a small round circle"


def m_sombra(spec):
    """C6 — duas direções de sombra no mesmo campo."""
    spec["lighting"]["shadow_direction"] = "falls camera-left for the subject and camera-right for the background"


def m_flare(spec):
    """C7 — veiling flare sem fonte que o justifique."""
    spec["optics"]["veiling_flare"] = "low-contrast veiling flare across the right third"


def m_tecido(spec):
    """C9 — seda declarada sem caimento fluido correspondente."""
    spec["wardrobe"][0]["fabric"] = "raw silk"
    spec["wardrobe"][0]["weave"] = "the fabric shows its grain at close range"
    spec["wardrobe"][0]["tension_creases"] = ["a mark at the elbow"]


def m_exterior(spec):
    """C10 — cena exterior com geometria solar mas sem preenchimento de céu.

    A metade estrutural da C10 (existir elevação, azimute e condição de céu) é
    imposta declarativamente pelo allOf do schema e falha antes das regras
    rodarem. O que sobra para a regra é a divergência de temperatura entre sol e
    cúpula, que é o que assina exterior real — e é isso que este caso exercita.
    """
    spec["scene"]["setting"] = "exterior"
    spec["environment"] = {
        "solar_elevation_deg": 8,
        "solar_azimuth_deg": 250,
        "sky_condition": "clear",
    }


def m_refs(spec):
    """C11 — referências de identidade acima do teto de 5."""
    spec["character"] = {
        "invariant": ["facial geometry"],
        "variable": ["pose"],
        "identity_reference_count": 8,
    }


def m_reflexo(spec):
    """C12 — superfície polida refletindo fonte que não existe em lighting.sources."""
    spec["materials"][1]["reflects"] = "a large octabox reflected across the indices"


def m_sem_pele(spec):
    """C13 — pessoa no quadro sem o bloco skin."""
    del spec["skin"]


def m_fonte_incompleta(spec):
    """Checklist item 1 — fonte sem temperatura de cor."""
    del spec["lighting"]["sources"][1]["colour_temp_k"]


def m_imperfeicao_generica(spec):
    """Checklist item 5 — imperfeição formulada genericamente."""
    spec["imperfection_budget"] = [
        {"category": "styling", "specific": "some imperfections are present in the frame"}
    ]


def m_termo_proibido(spec):
    """Checklist item 6 — termo proibido em campo de texto."""
    spec["render"]["palette_note"] = "ultra detailed, award winning colour science"


def m_cauda_conteudo(spec):
    """Checklist item 7 — conteúdo de cena na cauda, que exige formulação positiva."""
    spec["avoid"].append("no cars in the background")


def m_densidade(spec):
    """Checklist item 8 — corpo abaixo do piso do regime.

    Remove apenas campos opcionais: se a mutação violasse um mínimo declarado no
    schema, a falha viria da validação estrutural e o item 8 nunca rodaria.
    Isto é a ordem de sacrifício da doutrina levada além do limite — óptica,
    vestuário e ambiente cortados até o prompt ficar subespecificado.
    """
    for bloco, campo in [
        ("subject", "vellus_hair"),
        ("optics", "chromatic_aberration"),
        ("optics", "vignetting"),
        ("optics", "bokeh_character"),
        ("skin", "subsurface"),
        ("skin", "regional_variation"),
        ("skin", "capillary"),
        ("skin", "makeup"),
        ("lighting", "background_treatment"),
        ("lighting", "mixed_temperature"),
        ("camera", "perspective_note"),
        ("render", "palette_note"),
        ("render", "chroma_noise"),
        ("frame", "headroom"),
    ]:
        spec[bloco].pop(campo, None)
    spec.pop("wardrobe", None)
    spec.pop("capture_reality", None)


# (nome, base, mutação, fragmento exigido na mensagem de falha)
CASOS = [
    ("C1  ISO vs grão", BASE_PESSOA, m_iso, "C1"),
    ("C2  abertura vs plano focal", BASE_PESSOA, m_abertura, "C2"),
    ("C3  velocidade vs movimento", BASE_PESSOA, m_obturador, "C3"),
    ("C4  tamanho da fonte vs penumbra", BASE_PESSOA, m_penumbra, "C4"),
    ("C5  catchlight vs modificador", BASE_PESSOA, m_catchlight, "C5"),
    ("C6  direção de sombra única", BASE_PESSOA, m_sombra, "C6"),
    ("C7  flare exige fonte", BASE_PESSOA, m_flare, "C7"),
    ("C9  tecido vs caimento", BASE_PESSOA, m_tecido, "C9"),
    ("C10 exterior exige sol", BASE_PESSOA, m_exterior, "C10"),
    ("C11 teto de referências", BASE_PESSOA, m_refs, "identity_reference_count"),
    ("C12 reflexo declara fonte", BASE_PRODUTO, m_reflexo, "C12"),
    ("C13 pessoa exige pele", BASE_PESSOA, m_sem_pele, "skin"),
    ("ck1 fonte completa", BASE_PESSOA, m_fonte_incompleta, "colour_temp_k"),
    ("ck5 imperfeição específica", BASE_PESSOA, m_imperfeicao_generica, "item 5"),
    ("ck6 termos proibidos", BASE_PESSOA, m_termo_proibido, "item 6"),
    ("ck7 cauda sem conteúdo de cena", BASE_PESSOA, m_cauda_conteudo, "item 7"),
    ("ck8 orçamento de densidade", BASE_PESSOA, m_densidade, "item 8"),
]


def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    largura = max(len(nome) for nome, *_ in CASOS)
    falhou = 0

    # Guarda: as bases precisam estar aprovadas, senão os testes negativos não
    # provam nada — qualquer mutação "falharia" pelo motivo errado.
    print("Bases:")
    for base in (BASE_PESSOA, BASE_PRODUTO):
        spec = json.loads(base.read_text(encoding="utf-8"))
        falhas, _, _ = valida(spec, schema)
        estado = "aprovada" if not falhas else f"REPROVADA: {falhas}"
        print(f"  {base.name:38} {estado}")
        if falhas:
            falhou += 1
    print()

    print("Testes negativos — cada mutação deve disparar a regra correspondente:")
    for nome, base, mutacao, fragmento in CASOS:
        spec = copy.deepcopy(json.loads(base.read_text(encoding="utf-8")))
        mutacao(spec)
        falhas, _, _ = valida(spec, schema)
        acertou = any(fragmento in f for f in falhas)
        if acertou:
            print(f"  ok    {nome:{largura}}  disparou")
        else:
            falhou += 1
            motivo = falhas if falhas else "nenhuma falha detectada"
            print(f"  FALHA {nome:{largura}}  esperava {fragmento!r}, obteve {motivo}")

    print()
    if falhou:
        print(f"{falhou} problema(s).")
        return 1
    print(f"{len(CASOS)} testes negativos passaram, e as duas bases seguem aprovadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
