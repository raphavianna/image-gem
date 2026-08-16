#!/usr/bin/env python3
"""Validador de referência do schema canônico — etapa E2.

Faz três coisas, nesta ordem, e para na primeira que falhar:

1. Valida a instância contra `prompt-spec.json` (estrutura e cardinalidade).
2. Executa as regras de coerência entre campos declaradas em `x-imagegem.regras_de_coerencia`.
3. Executa o checklist de emissão declarado em `x-imagegem.checklist_de_emissao`.

E renderiza a modalidade 1 a partir da instância, que é o teste de volta da etapa.

Este é um validador de referência: existe para tornar a definição de pronto da E2
verificável, não para ser o código de produção. A E5 implementa o mesmo contrato
dentro de `src/imagegem/`. As regras não se movem — elas moram no schema, e tanto
este arquivo quanto a E5 as leem de lá.

Uso:
    python3 schemas/validador.py                      # valida e renderiza todos os exemplos
    python3 schemas/validador.py caminho/spec.json    # valida e renderiza um spec
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema

RAIZ = Path(__file__).resolve().parent
SCHEMA_PATH = RAIZ / "prompt-spec.json"


# --------------------------------------------------------------------------- #
# Regras de coerência entre campos                                            #
# --------------------------------------------------------------------------- #
# Cada função recebe (spec, cfg) e devolve lista de mensagens de falha.
# cfg é o bloco x-imagegem do schema. Lista vazia significa aprovado.

# Faixas de ISO e os descritores de grão compatíveis com cada uma.
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
            # O grão precisa citar o ISO para amarrar a consequência à causa.
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
        return [
            f"C3: {obturador} congela movimento, mas o orçamento de imperfeição "
            "prescreve arrasto"
        ]
    if denominador <= 60 and not tem_arrasto:
        return [
            f"C3: {obturador} é lenta o bastante para arrastar movimento e nenhuma "
            "consequência foi declarada"
        ]
    return []


def source_size_vs_penumbra(spec, cfg):
    """C4 — a penumbra corresponde ao tamanho angular da fonte principal."""
    penumbra = spec["lighting"].get("penumbra")
    if penumbra is None:
        return ["C4: cena de estúdio sem largura de penumbra declarada"]
    key = next((s for s in spec["lighting"]["sources"] if s["role"] == "key"), None)
    if key is None:
        return ["C4: nenhuma fonte com papel 'key'"]
    if not key.get("size_m") or not key.get("distance_m"):
        return ["C4: a key não declara tamanho e distância, então a penumbra não é verificável"]

    # Razão tamanho/distância como proxy do tamanho angular da fonte. É o que
    # governa a dureza da sombra: fonte grande e próxima abre a penumbra, fonte
    # pequena e distante a estreita.
    #
    # Guarda grosseira, não modelo fotométrico: a largura real também depende da
    # distância entre o objeto e a superfície que recebe a sombra, que o schema
    # não modela. Os limiares abaixo estão calibrados para pegar a contradição
    # franca — luz dura com penumbra de softbox e vice-versa — e deixam passar a
    # faixa intermediária. Ambos os âncoras do prompt-mestre caem na faixa larga
    # (1,07 e 1,29) com penumbras de 3–4cm e 1–2cm.
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
}


def catchlight_vs_modifier(spec, cfg):
    """C5 — a forma do catchlight corresponde ao modificador da key."""
    catchlight = spec["lighting"].get("catchlight")
    if catchlight is None:
        return ["C5: há pessoa no quadro e nenhum catchlight declarado"]
    key = next((s for s in spec["lighting"]["sources"] if s["role"] == "key"), None)
    if key is None:
        return ["C5: nenhuma fonte com papel 'key'"]
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
    # Duas direções cardinais opostas no mesmo campo denunciam incoerência.
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
    return [
        "C7: veiling_flare declarado sem fonte de luz que o justifique "
        "(nenhuma fonte com papel 'sun' ou 'practical')"
    ]


# Tecido → termos de caimento compatíveis.
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
        # O caimento pode estar no campo próprio ou implícito nos vincos de tensão.
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
    faltando = [
        c
        for c in ("solar_elevation_deg", "solar_azimuth_deg", "sky_condition")
        if c not in env
    ]
    if faltando:
        return [f"C10: cena exterior sem {', '.join(faltando)}"]
    if not env.get("sky_fill"):
        return [
            "C10: cena exterior sem sky_fill; a divergência de temperatura entre sol "
            "e cúpula do céu é o que assina exterior real"
        ]
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
            falhas.append(
                f"C12: superfície polida {material['surface']!r} não declara o que reflete"
            )
            continue
        # Se o reflexo nomeia um tipo de fonte, ele precisa existir em lighting.sources.
        for termo in ("softbox", "strip", "octabox", "window", "ring", "beauty dish"):
            if termo in reflete and termo not in modificadores:
                falhas.append(
                    f"C12: {material['surface']!r} reflete {termo!r}, que não existe "
                    "em lighting.sources"
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


CHECKS_COERENCIA = {
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
    falhas = []
    for material in spec.get("materials", []):
        if not material.get("specular_response"):
            falhas.append(f"item 4b: {material['surface']!r} sem resposta especular")
    return falhas


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
    falhas = []
    for termo in cfg["termos_proibidos"]:
        if re.search(rf"\b{re.escape(termo)}\b", corpo, flags=re.IGNORECASE):
            falhas.append(f"item 6: termo proibido no prompt renderizado: {termo!r}")
    return falhas


# Padrões de conteúdo de cena, que devem ser formulados positivamente [GAI].
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
    """Seleciona a faixa de densidade aplicável ao regime do spec.

    Os três regimes carregam conjuntos diferentes de blocos obrigatórios, então
    a faixa é por regime e não banda única. Ver x-imagegem.orcamento_densidade.
    """
    regime = spec["scene"]["regime"]
    # Composição segue as faixas de geração: os blocos obrigatórios são os mesmos.
    if regime == "composition":
        regime = "generation"
    for faixa in cfg["orcamento_densidade"]["faixas"]:
        if faixa["regime"] != regime:
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


CHECKS_CHECKLIST = {
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
# Renderizador da modalidade 1 — o teste de volta                             #
# --------------------------------------------------------------------------- #


def _frase(*partes):
    """Junta partes não vazias numa frase terminada em ponto.

    Normaliza a pontuação de junção: sem espaço antes de vírgula, sem vírgula
    duplicada, inicial maiúscula. Sem isso a concatenação de campos produz
    artefatos como 'waist-up , vertical' que denunciam texto montado por máquina.
    """
    texto = " ".join(p.strip().rstrip(".") for p in partes if p and p.strip())
    if not texto:
        return ""
    texto = re.sub(r"\s+([,;:])", r"\1", texto)
    texto = re.sub(r",\s*,", ",", texto)
    texto = re.sub(r"\s{2,}", " ", texto)
    return texto[0].upper() + texto[1:] + "."


def _bloco_subject(spec):
    s = spec["subject"]
    assimetrias = ", and ".join(s["asymmetries"])
    marcas = ", ".join(s["preserved_marks"])
    return " ".join(
        filter(
            None,
            [
                _frase(s["description"]),
                _frase("Her facial structure is specifically asymmetric:", assimetrias),
                _frase(marcas[0].upper() + marcas[1:]),
                _frase("Vellus hair is", s.get("vellus_hair", "")),
                _frase("The expression is", s["expression"]),
            ],
        )
    )


def _bloco_wardrobe(spec):
    partes = []
    for peca in spec.get("wardrobe", []):
        vincos = ", and ".join(peca["tension_creases"]) if len(peca["tension_creases"]) < 3 else ", ".join(peca["tension_creases"])
        partes.append(
            " ".join(
                filter(
                    None,
                    [
                        _frase(peca["garment"][0].upper() + peca["garment"][1:]),
                        _frase(peca["weave"], ", with", vincos),
                        _frase(peca.get("drape", "")),
                        _frase(peca.get("wear", "")),
                    ],
                )
            )
        )
    return " ".join(partes)


def _bloco_camera(spec):
    c = spec["camera"]
    o = spec.get("optics", {})
    em_foco = " and ".join(c["focal_plane"]["in_focus"])
    fora = "; ".join(c["focal_plane"]["out_of_focus"])
    return " ".join(
        filter(
            None,
            [
                _frase(
                    f"{c['body']}, {c['focal_length_mm']:g}mm at f/{c['aperture_f']:g},",
                    f"{c['shutter']}, ISO {c['iso']}",
                ),
                _frase(f"Camera {c['height']}, {c['distance_m']:g} metres from the subject"),
                _frase(f"Focal plane on {em_foco}; {fora}"),
                _frase(c.get("perspective_note", "")),
                _frase("Bokeh is", o.get("bokeh_character", "")),
                _frase(o.get("chromatic_aberration", "")),
                _frase(o.get("vignetting", "")),
                _frase(o.get("distortion", "")),
                _frase(o.get("veiling_flare", "")),
            ],
        )
    )


def _descreve_fonte(f):
    """Descreve uma fonte com as seis grandezas do eixo 2, sem andaime supérfluo.

    A geometria sai numa oração só ('at X degrees azimuth and <elevação>, Y metres
    away') em vez de três orações coordenadas: o custo em palavras de satisfazer o
    item 1 do checklist multiplica pelo número de fontes.
    """
    partes = [f["modifier"]]
    geometria = []
    if f.get("azimuth_deg") is not None:
        geometria.append(f"at {f['azimuth_deg']:g} degrees azimuth")
    if f.get("elevation"):
        geometria.append(f"and {f['elevation']}")
    if f.get("distance_m"):
        geometria.append(f"{f['distance_m']:g} metres away")
    if geometria:
        partes.append(" ".join(geometria[:2]) + (f", {geometria[2]}" if len(geometria) > 2 else ""))
    if f.get("feathering"):
        partes.append(f["feathering"])
    return ", ".join(partes)


def _bloco_lighting(spec):
    lg = spec["lighting"]
    por_papel = {}
    for f in lg["sources"]:
        por_papel.setdefault(f["role"], []).append(f)

    frases = []
    for f in por_papel.get("key", []):
        texto = _descreve_fonte(f)
        if lg.get("penumbra"):
            p = lg["penumbra"]
            texto += (
                f", producing a soft-edged shadow with a {p['width_cm']} "
                f"centimetre penumbra {p['location']}"
            )
        frases.append(_frase("Key is a", texto))
    for f in por_papel.get("fill", []):
        frases.append(
            _frase(
                "Fill is a",
                _descreve_fonte(f),
                f", holding the key-to-fill ratio at {lg['key_fill_ratio']}",
            )
        )
    for f in por_papel.get("rim", []):
        frases.append(_frase("A", _descreve_fonte(f), "lays a narrow rim on the subject"))
    for f in por_papel.get("sun", []) + por_papel.get("sky", []):
        frases.append(_frase("A", _descreve_fonte(f)))

    frases.append(_frase(lg.get("background_treatment", "")))
    frases.append(_frase(lg.get("mixed_temperature", "")))
    frases.append(_frase("The cast shadow", lg["shadow_direction"]))
    frases.append(_frase(lg.get("contact_shadow", "")))

    cl = lg.get("catchlight")
    if cl:
        frases.append(
            _frase(
                "The catchlight in each eye is",
                cl["shape"],
                "at",
                cl["position"] + ",",
                cl.get("far_eye", ""),
            )
        )
    return " ".join(filter(None, frases))


def _bloco_skin(spec):
    s = spec["skin"]
    return " ".join(
        filter(
            None,
            [
                _frase(s["pore_scale"]),
                _frase(s["specular_zones"]),
                _frase(s.get("subsurface", "")),
                _frase(s.get("regional_variation", "")),
                _frase(s.get("capillary", "")),
                _frase(s.get("makeup", "")),
            ],
        )
    )


def _bloco_materials(spec):
    partes = []
    for m in spec.get("materials", []):
        # O conteúdo do reflexo NÃO sai aqui: ele é consolidado em REFLECTION
        # GEOMETRY. Repetir por material é o que inflava o corpo em 44%.
        partes.append(
            " ".join(
                filter(
                    None,
                    [
                        _frase(m["surface"] + ":", m["specular_response"]),
                        _frase(m.get("typography", "")),
                        _frase(m.get("manufacturing_defect", "")),
                    ],
                )
            )
        )
    return " ".join(partes)


def _bloco_reflection(spec):
    """Consolida a geometria de reflexo num bloco único, como no exemplo 4."""
    reflexos = [m["reflects"] for m in spec.get("materials", []) if m.get("reflects")]
    if not reflexos:
        return ""
    corpo = _frase("; ".join(reflexos))
    fechamento = _frase(spec.get("reflection_closure", ""))
    return " ".join(filter(None, [corpo, fechamento]))


def _bloco_render(spec):
    r = spec["render"]
    cabeca = r["colour_profile"]
    if r.get("palette_note"):
        cabeca += f" palette: {r['palette_note']}"
    return " ".join(
        filter(
            None,
            [
                _frase(cabeca),
                _frase(r["highlight_rolloff"]),
                _frase(r["black_point"]),
                _frase(r["grain"], "with" if r.get("chroma_noise") else "", r.get("chroma_noise", "")),
            ],
        )
    )


def _bloco_frame(spec):
    f = spec["frame"]
    return " ".join(filter(None, [_frase(f["composition"]), _frase(f.get("headroom", ""))]))


def _bloco_capture(spec):
    partes = [i["specific"] for i in spec["imperfection_budget"]]
    if spec.get("capture_reality"):
        partes.append(spec["capture_reality"])
    return " ".join(_frase(p) for p in partes)


def _bloco_edit(spec):
    e = spec["edit"]
    blocos = [
        ("PRESERVE", " ".join(_frase(p) for p in e["preserve"])),
        ("REPLACE", _frase(e["replace"])),
        ("RECONCILE LIGHT", _frase(e["light_reconciliation"])),
    ]
    if e.get("integration"):
        blocos.append(("GROUND AND INTEGRATE", _frase(e["integration"])))
    return blocos


def renderiza_modalidade_1(spec):
    """Renderiza o spec como prompt colável para a interface do Gemini."""
    o = spec["output"]
    cabecalho = _frase(
        spec["scene"]["headline"],
        f", {o['orientation']} {o['aspect_ratio']} frame" if o.get("orientation") else f", {o['aspect_ratio']} frame",
    )

    if spec["scene"]["regime"] == "edit":
        blocos = _bloco_edit(spec)
    else:
        blocos = [
            ("SUBJECT", _bloco_subject(spec) if "subject" in spec else ""),
            ("WARDROBE", _bloco_wardrobe(spec)),
            ("OBJECT AND MATERIALS", _bloco_materials(spec)),
            ("CAMERA AND OPTICS", _bloco_camera(spec)),
            ("LIGHTING", _bloco_lighting(spec)),
            ("REFLECTION GEOMETRY", _bloco_reflection(spec)),
            ("SKIN", _bloco_skin(spec) if "skin" in spec else ""),
            ("COLOUR AND RENDER", _bloco_render(spec)),
            ("FRAME", _bloco_frame(spec)),
            ("CAPTURE REALITY", _bloco_capture(spec)),
        ]

    partes = [cabecalho]
    for rotulo, conteudo in blocos:
        if conteudo and conteudo.strip():
            partes.append(f"{rotulo}. {conteudo}")

    corpo = "\n\n".join(partes)
    cauda = "AVOID: " + ", ".join(spec["avoid"]) + "."
    return corpo, cauda


# --------------------------------------------------------------------------- #
# Execução                                                                     #
# --------------------------------------------------------------------------- #


def valida(spec, schema):
    """Roda schema, coerência e checklist. Devolve (falhas, corpo, cauda)."""
    cfg = schema["x-imagegem"]
    falhas = []

    validador = jsonschema.Draft202012Validator(schema)
    for erro in sorted(validador.iter_errors(spec), key=lambda e: list(e.path)):
        caminho = "/".join(str(p) for p in erro.path) or "(raiz)"
        falhas.append(f"schema: {caminho}: {erro.message}")
    if falhas:
        return falhas, None, None

    for regra in cfg["regras_de_coerencia"]:
        if aplica(regra, spec):
            falhas.extend(CHECKS_COERENCIA[regra["check"]](spec, cfg))

    corpo, cauda = renderiza_modalidade_1(spec)

    for item in cfg["checklist_de_emissao"]:
        if aplica(item, spec):
            falhas.extend(CHECKS_CHECKLIST[item["check"]](spec, cfg, corpo))

    return falhas, corpo, cauda


def main(argv):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    alvos = (
        [Path(a) for a in argv[1:]]
        if len(argv) > 1
        else sorted((RAIZ / "exemplos").glob("*.json"))
    )

    codigo = 0
    for caminho in alvos:
        spec = json.loads(caminho.read_text(encoding="utf-8"))
        falhas, corpo, cauda = valida(spec, schema)

        print("=" * 78)
        print(f"SPEC: {caminho.name}")
        print("=" * 78)
        if falhas:
            codigo = 1
            print(f"\nREPROVADO — {len(falhas)} falha(s):\n")
            for f in falhas:
                print(f"  - {f}")
        else:
            cfg = schema["x-imagegem"]
            aplicaveis = sum(1 for r in cfg["regras_de_coerencia"] if aplica(r, spec))
            faixa = faixa_de_densidade(spec, cfg)
            n = len(corpo.split())
            print(
                f"\nAPROVADO — schema, {aplicaveis} regras de coerência aplicáveis "
                f"e {len(cfg['checklist_de_emissao'])} itens do checklist."
            )
            print(
                f"Corpo: {n} palavras "
                f"(faixa {faixa['min_palavras']}–{faixa['max_palavras']}, "
                f"âncora {faixa['ancora']}).\n"
            )
            print("-" * 78)
            print(corpo)
            print()
            print(cauda)
            print("-" * 78)
        print()

    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv))
