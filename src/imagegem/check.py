"""Regras de coerência (C1–C14) e checklist de emissão (itens 1–8).

Cada função de regra recebe `(spec, cfg)` e devolve lista de mensagens de falha;
cada função de checklist recebe `(spec, cfg, corpo)` — o corpo é o texto
renderizado pela modalidade 1, para que o item 6 (termos proibidos) e o item 8
(orçamento de densidade) inspecionem o resultado final e não os campos.

As regras moram no schema (`x-imagegem.regras_de_coerencia`); este módulo só
provê a implementação. `validate(spec)` executa schema → coerência → checklist
na ordem, parando na primeira etapa que falha.
"""

from __future__ import annotations

import re
from typing import Callable

import jsonschema

from imagegem import render, schema


# --------------------------------------------------------------------------- #
# Regras de coerência entre campos                                            #
# --------------------------------------------------------------------------- #

FAIXAS_ISO = [
    (0, 200, ("fine", "very fine", "faint", "minimal")),
    (201, 1600, ("moderate", "visible", "present", "fine")),
    (1601, 100000, ("coarse", "heavy", "pronounced", "grainy")),
]


def iso_vs_grain(spec, cfg):
    """C1 — o grão declarado corresponde à faixa de ISO."""
    iso = spec["camera"]["iso"]
    grao = spec["render"]["grain"].lower()
    for baixo, alto, termos in FAIXAS_ISO:
        if baixo <= iso <= alto:
            if not any(t in grao for t in termos):
                return [
                    f"C1: ISO {iso} está na faixa {baixo}–{alto}, que espera grão "
                    f"descrito com um de {termos}; o campo render.grain diz "
                    f"{spec['render']['grain']!r}"
                ]
            if str(iso) not in spec["render"]["grain"]:
                return [
                    f"C1: render.grain não cita o ISO declarado ({iso}). A cadeia "
                    "causal precisa estar explícita no texto emitido."
                ]
            return []
    return [f"C1: ISO {iso} fora de qualquer faixa conhecida"]


def aperture_vs_focal_plane(spec, cfg):
    """C2 — abertura larga exige queda de foco declarada."""
    f = spec["camera"]["aperture_f"]
    fora = spec["camera"]["focal_plane"]["out_of_focus"]
    if f <= 5.6 and not fora:
        return [f"C2: f/{f} é abertura larga e nenhum elemento fora de foco foi declarado"]
    if f >= 16 and fora:
        return [
            f"C2: f/{f} é abertura fechada; declarar {len(fora)} elemento(s) fora de "
            "foco contradiz a profundidade de campo implícita"
        ]
    return []


def shutter_vs_motion(spec, cfg):
    """C3 — velocidade e arrasto de movimento concordam."""
    obturador = spec["camera"]["shutter"]
    m = re.search(r"1/(\d+)", obturador)
    if not m:
        return [f"C3: velocidade {obturador!r} não é legível como fração"]
    denominador = int(m.group(1))
    texto = " ".join(i["specific"].lower() for i in spec["imperfection_budget"])
    tem_arrasto = any(t in texto for t in ("blur", "drag", "smear", "motion"))
    if denominador >= 500 and tem_arrasto:
        return [f"C3: {obturador} congela movimento, mas o orçamento de imperfeição prescreve arrasto"]
    if denominador <= 60 and not tem_arrasto:
        return [f"C3: {obturador} é lenta o bastante para arrastar movimento e nenhuma consequência foi declarada"]
    return []


def source_size_vs_penumbra(spec, cfg):
    """C4 — a penumbra corresponde ao tamanho angular da fonte principal.

    Guarda grosseira, não modelo fotométrico: a largura real depende também da
    distância objeto-superfície, que o schema não modela. Pega a contradição
    franca — luz dura com penumbra de softbox e vice-versa.
    """
    penumbra = spec["lighting"].get("penumbra")
    if penumbra is None:
        return ["C4: cena de estúdio sem largura de penumbra declarada"]
    key = next((s for s in spec["lighting"]["sources"] if s["role"] == "key"), None)
    if key is None:
        return ["C4: nenhuma fonte com papel 'key'"]
    if not key.get("size_m") or not key.get("distance_m"):
        return ["C4: a key não declara tamanho e distância, então a penumbra não é verificável"]

    razao = key["size_m"] / key["distance_m"]
    largura = penumbra["width_cm"]
    numeros = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", largura)]
    if not numeros:
        return [f"C4: largura de penumbra {largura!r} não contém valor numérico"]
    maior = max(numeros)

    if razao >= 0.8 and maior < 1.5:
        return [
            f"C4: key de {key['size_m']:g}m a {key['distance_m']:g}m é fonte larga "
            f"(razão {razao:.2f}) e produz penumbra aberta; declarada {maior:g}cm"
        ]
    if razao < 0.3 and maior > 2:
        return [
            f"C4: key de {key['size_m']:g}m a {key['distance_m']:g}m é fonte dura "
            f"(razão {razao:.2f}) e produz sombra de borda estreita; declarada {maior:g}cm"
        ]
    return []


# Modificador de luz → forma de catchlight que ele produz.
FORMAS_CATCHLIGHT = {
    "octabox": ("octagon", "octagonal"),
    "beauty dish": ("circle", "circular", "round"),
    "strip": ("rectangle", "rectangular", "strip", "band"),
    "softbox": ("rectangle", "rectangular", "square"),
    "umbrella": ("circle", "circular", "round"),
    "window": ("rectangle", "rectangular", "quadrilateral", "pane"),
    "ring": ("ring", "annular"),
    "sunlight": ("small", "round", "point", "concentrated", "specular"),
    "sun ": ("small", "round", "point", "concentrated", "specular"),
    "sky": ("large", "diffuse", "hemispherical", "broad"),
}


def _fonte_principal(spec):
    """Preferência: key > sun > sky > primeira. Em exterior a key some."""
    fontes = spec["lighting"]["sources"]
    for papel in ("key", "sun", "sky"):
        f = next((s for s in fontes if s["role"] == papel), None)
        if f is not None:
            return f
    return fontes[0] if fontes else None


def catchlight_vs_modifier(spec, cfg):
    """C5 — a forma do catchlight corresponde ao modificador da fonte principal."""
    catchlight = spec["lighting"].get("catchlight")
    if catchlight is None:
        return ["C5: há pessoa no quadro e nenhum catchlight declarado"]
    key = _fonte_principal(spec)
    if key is None:
        return ["C5: nenhuma fonte de luz declarada"]
    modificador = key["modifier"].lower()
    forma = catchlight["shape"].lower()
    for chave, formas_ok in FORMAS_CATCHLIGHT.items():
        if chave in modificador:
            if not any(f in forma for f in formas_ok):
                return [
                    f"C5: a key é {chave!r}, que produz catchlight {formas_ok}; "
                    f"declarado {catchlight['shape']!r}"
                ]
            return []
    return [
        f"C5: modificador {key['modifier']!r} não está na tabela de formas de "
        "catchlight; acrescente-o ou declare a forma explicitamente"
    ]


def single_shadow_direction(spec, cfg):
    """C6 — uma e só uma direção de sombra projetada."""
    direcao = spec["lighting"]["shadow_direction"]
    if not direcao.strip():
        return ["C6: direção de sombra vazia"]
    opostos = [("camera-left", "camera-right"), ("toward camera", "away from camera")]
    baixo = direcao.lower()
    for a, b in opostos:
        if a in baixo and b in baixo:
            return [f"C6: direção de sombra declara {a!r} e {b!r} ao mesmo tempo"]
    return []


def flare_requires_source(spec, cfg):
    """C7 — veiling flare exige fonte no quadro ou em ângulo de incidência."""
    flare = spec.get("optics", {}).get("veiling_flare")
    if not flare:
        return []
    papeis = {s["role"] for s in spec["lighting"]["sources"]}
    if "sun" in papeis or "practical" in papeis:
        return []
    return ["C7: veiling_flare declarado sem fonte de luz que o justifique (nenhuma fonte com papel 'sun' ou 'practical')"]


CAIMENTO = {
    "silk": ("fluid", "drape", "narrow", "soft"),
    "wool": ("heavy", "structured", "broad", "compression", "crepe"),
    "denim": ("stiff", "angular", "rigid"),
    "linen": ("crisp", "rumpled", "sharp"),
    "cotton": ("soft", "moderate", "even"),
    "leather": ("stiff", "fold", "crease"),
}


def fabric_vs_drape(spec, cfg):
    """C9 — tecido nomeado exige caimento correspondente declarado."""
    falhas = []
    for peca in spec.get("wardrobe", []):
        tecido = peca["fabric"].lower()
        texto = " ".join(
            [peca.get("drape", "") or ""] + list(peca["tension_creases"]) + [peca["weave"]]
        ).lower()
        for chave, termos in CAIMENTO.items():
            if chave in tecido:
                if not any(t in texto for t in termos):
                    falhas.append(
                        f"C9: tecido {peca['fabric']!r} espera caimento descrito com "
                        f"um de {termos}; nada equivalente em drape/tension_creases/weave"
                    )
                break
    return falhas


def exterior_requires_solar(spec, cfg):
    """C10 — cena exterior exige geometria solar e condição de céu."""
    env = spec.get("environment", {})
    faltando = [c for c in ("solar_elevation_deg", "solar_azimuth_deg", "sky_condition") if c not in env]
    if faltando:
        return [f"C10: cena exterior sem {', '.join(faltando)}"]
    if not env.get("sky_fill"):
        return ["C10: cena exterior sem sky_fill; a divergência de temperatura entre sol e cúpula do céu é o que assina exterior real"]
    return []


def identity_reference_ceiling(spec, cfg):
    """C11 — referências de identidade não excedem o teto da fonte."""
    teto = cfg["limites_referencia"]["identidade"]
    n = spec.get("character", {}).get("identity_reference_count")
    if n is not None and n > teto:
        return [f"C11: {n} referências de identidade excedem o teto de {teto}"]
    return []


def reflection_declares_source(spec, cfg):
    """C12 — reflexo não implica fonte de luz ausente de lighting.sources."""
    modificadores = " ".join(s["modifier"].lower() for s in spec["lighting"]["sources"])
    falhas = []
    for material in spec.get("materials", []):
        if material["finish"] != "polished":
            continue
        reflete = (material.get("reflects") or "").lower()
        if not reflete:
            falhas.append(f"C12: superfície polida {material['surface']!r} não declara o que reflete")
            continue
        for termo in ("softbox", "strip", "octabox", "window", "ring", "beauty dish"):
            if termo in reflete and termo not in modificadores:
                falhas.append(
                    f"C12: {material['surface']!r} reflete {termo!r}, que não existe em lighting.sources"
                )
    return falhas


def person_requires_skin_and_subject(spec, cfg):
    """C13 — has_person exige os blocos subject e skin."""
    faltando = [b for b in ("subject", "skin") if b not in spec]
    return [f"C13: has_person é true e falta {', '.join(faltando)}"] if faltando else []


def edit_requires_edit_block(spec, cfg):
    """C14 — regime edit exige o bloco edit, com preservação não vazia."""
    if "edit" not in spec:
        return ["C14: regime 'edit' sem bloco edit"]
    if not spec["edit"]["preserve"]:
        return ["C14: bloco edit com preserve vazio"]
    return []


CHECKS_COERENCIA: dict[str, Callable] = {
    "iso_vs_grain": iso_vs_grain,
    "aperture_vs_focal_plane": aperture_vs_focal_plane,
    "shutter_vs_motion": shutter_vs_motion,
    "source_size_vs_penumbra": source_size_vs_penumbra,
    "catchlight_vs_modifier": catchlight_vs_modifier,
    "single_shadow_direction": single_shadow_direction,
    "flare_requires_source": flare_requires_source,
    "fabric_vs_drape": fabric_vs_drape,
    "exterior_requires_solar": exterior_requires_solar,
    "identity_reference_ceiling": identity_reference_ceiling,
    "reflection_declares_source": reflection_declares_source,
    "person_requires_skin_and_subject": person_requires_skin_and_subject,
    "edit_requires_edit_block": edit_requires_edit_block,
}


def aplica(regra, spec):
    """Avalia o campo 'aplica_quando' de uma regra declarada no schema."""
    quando = regra.get("aplica_quando", "sempre")
    cena = spec["scene"]
    if quando == "sempre":
        return True
    if quando == "scene.has_person":
        return cena["has_person"]
    if quando == "scene.has_person and scene.regime != edit":
        return cena["has_person"] and cena["regime"] != "edit"
    if quando == "scene.regime != edit":
        return cena["regime"] != "edit"
    if quando == "scene.setting == studio":
        return cena["setting"] == "studio"
    if quando == "scene.setting == exterior":
        return cena["setting"] == "exterior"
    if quando == "scene.regime == edit":
        return cena["regime"] == "edit"
    if quando == "optics.veiling_flare presente":
        return bool(spec.get("optics", {}).get("veiling_flare"))
    if quando == "wardrobe não vazio":
        return bool(spec.get("wardrobe"))
    if quando == "materials não vazio":
        return bool(spec.get("materials"))
    if quando == "materials contém finish polished":
        return any(m["finish"] == "polished" for m in spec.get("materials", []))
    if quando == "character presente":
        return "character" in spec
    raise ValueError(f"condição 'aplica_quando' desconhecida: {quando!r}")


# --------------------------------------------------------------------------- #
# Checklist de emissão                                                        #
# --------------------------------------------------------------------------- #


def ck1_light_sources_complete(spec, cfg, corpo):
    obrigatorios = ("size_m", "distance_m", "azimuth_deg", "elevation", "colour_temp_k")
    falhas = []
    for fonte in spec["lighting"]["sources"]:
        for campo in obrigatorios:
            if fonte.get(campo) is None and fonte["role"] not in ("sun", "sky"):
                falhas.append(f"item 1: fonte {fonte['role']!r} sem {campo}")
    if not spec["lighting"].get("key_fill_ratio"):
        falhas.append("item 1: razão key:fill ausente")
    return falhas


def ck2_exposure_coherent(spec, cfg, corpo):
    # Delega às regras de coerência, já executadas antes do checklist.
    return []


def ck3_single_shadow_direction(spec, cfg, corpo):
    return single_shadow_direction(spec, cfg)


def ck4a_skin(spec, cfg, corpo):
    falhas = []
    pele = spec.get("skin", {})
    sujeito = spec.get("subject", {})
    if not pele.get("pore_scale"):
        falhas.append("item 4a: escala de poro ausente")
    if not pele.get("specular_zones"):
        falhas.append("item 4a: especular de zona T ausente")
    if not sujeito.get("asymmetries"):
        falhas.append("item 4a: nenhuma assimetria específica")
    if not sujeito.get("preserved_marks"):
        falhas.append("item 4a: nenhuma marca preservada")
    return falhas


def ck4b_materials(spec, cfg, corpo):
    return [
        f"item 4b: {m['surface']!r} sem resposta especular"
        for m in spec.get("materials", []) if not m.get("specular_response")
    ]


GENERICOS = ("some ", "various", "a few imperfections", "slight imperfections", "minor flaws")


def ck5_imperfection_budget(spec, cfg, corpo):
    orcamento = spec["imperfection_budget"]
    falhas = []
    if not 1 <= len(orcamento) <= 3:
        falhas.append(f"item 5: {len(orcamento)} imperfeições, fora da faixa de 1 a 3")
    for imp in orcamento:
        if any(g in imp["specific"].lower() for g in GENERICOS):
            falhas.append(f"item 5: imperfeição genérica: {imp['specific']!r}")
    return falhas


def ck6_forbidden_terms(spec, cfg, corpo):
    return [
        f"item 6: termo proibido no prompt renderizado: {t!r}"
        for t in cfg["termos_proibidos"]
        if re.search(rf"\b{re.escape(t)}\b", corpo, flags=re.IGNORECASE)
    ]


CONTEUDO_DE_CENA = re.compile(r"^(no|without|not)\s+\w+", re.IGNORECASE)


def ck7_avoid_tail(spec, cfg, corpo):
    cauda = spec["avoid"]
    falhas = []
    if not cauda:
        falhas.append("item 7: cauda AVOID ausente")
    if len(cauda) > 16:
        falhas.append(f"item 7: cauda com {len(cauda)} entradas, acima do teto de 16")
    for entrada in cauda:
        if CONTEUDO_DE_CENA.match(entrada.strip()):
            falhas.append(
                f"item 7: {entrada!r} é conteúdo de cena, que se declara positivamente; "
                "a cauda aceita apenas modos de falha de renderização"
            )
    return falhas


def faixa_de_densidade(spec, cfg):
    """Seleciona a faixa de densidade aplicável ao spec.

    Prioridade:
      1. Faixa "reference-anchored" — quando `character.references_urls` tem
         itens, o corpo pesa menos porque muitos campos apontam para a referência.
      2. Faixa por regime — a decomposição travada na E2.
    """
    tem_refs = bool(spec.get("character", {}).get("references_urls"))
    faixas = cfg["orcamento_densidade"]["faixas"]

    if tem_refs:
        for faixa in faixas:
            if faixa.get("quando") == "character.references_urls não vazio":
                return faixa

    regime = spec["scene"]["regime"]
    if regime == "composition":
        regime = "generation"
    for faixa in faixas:
        if faixa.get("regime") != regime:
            continue
        if "has_person" in faixa and faixa["has_person"] != spec["scene"]["has_person"]:
            continue
        return faixa
    raise ValueError(f"nenhuma faixa de densidade para o regime {regime!r}")


def ck8_density_budget(spec, cfg, corpo):
    faixa = faixa_de_densidade(spec, cfg)
    n = len(corpo.split())
    if not faixa["min_palavras"] <= n <= faixa["max_palavras"]:
        return [
            f"item 8: corpo com {n} palavras, fora da faixa "
            f"{faixa['min_palavras']}–{faixa['max_palavras']} "
            f"(âncora: {faixa['ancora']})"
        ]
    return []


CHECKS_CHECKLIST: dict[str, Callable] = {
    "ck1_light_sources_complete": ck1_light_sources_complete,
    "ck2_exposure_coherent": ck2_exposure_coherent,
    "ck3_single_shadow_direction": ck3_single_shadow_direction,
    "ck4a_skin": ck4a_skin,
    "ck4b_materials": ck4b_materials,
    "ck5_imperfection_budget": ck5_imperfection_budget,
    "ck6_forbidden_terms": ck6_forbidden_terms,
    "ck7_avoid_tail": ck7_avoid_tail,
    "ck8_density_budget": ck8_density_budget,
}


# --------------------------------------------------------------------------- #
# Pipeline                                                                     #
# --------------------------------------------------------------------------- #


def validate(spec: dict) -> tuple[list[str], str | None, str | None]:
    """Executa schema → coerência → checklist. Devolve (falhas, corpo, cauda).

    Para na primeira etapa que falha: se o schema reprova, coerência e checklist
    não rodam, porque campos podem estar ausentes e produzir erros ruidosos.
    """
    s = schema.load()
    cfg = schema.cfg()
    falhas: list[str] = []

    validador = jsonschema.Draft202012Validator(s)
    for erro in sorted(validador.iter_errors(spec), key=lambda e: list(e.path)):
        caminho = "/".join(str(p) for p in erro.path) or "(raiz)"
        falhas.append(f"schema: {caminho}: {erro.message}")
    if falhas:
        return falhas, None, None

    for regra in cfg["regras_de_coerencia"]:
        if aplica(regra, spec):
            falhas.extend(CHECKS_COERENCIA[regra["check"]](spec, cfg))

    corpo, cauda = render.renderiza_modalidade_1(spec)

    for item in cfg["checklist_de_emissao"]:
        if aplica(item, spec):
            falhas.extend(CHECKS_CHECKLIST[item["check"]](spec, cfg, corpo))

    return falhas, corpo, cauda
