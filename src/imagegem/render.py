"""Renderizadores das quatro modalidades sobre o schema canônico.

Todas as modalidades leem o mesmo spec, produzindo o mesmo corpo textual em
blocos rotulados. O que muda é o envelope: modalidade 1 devolve texto puro,
2 devolve texto + controles do painel Higgsfield, 3 devolve payload REST
`POST /nano-banana`, 4 devolve `contents` + `ImageConfig` do google-genai.

A base compartilhada é `renderiza_modalidade_1(spec, incluir_output_no_texto)`.
As demais chamam ela com `False` para tirar proporção/resolução do texto — nas
APIs, esses valores viram parâmetros estruturados.
"""

from __future__ import annotations

import re


def _frase(*partes) -> str:
    """Junta partes não vazias numa frase terminada em ponto.

    Normaliza pontuação de junção (sem espaço antes de vírgula, sem vírgula
    duplicada), inicial maiúscula. Sem isso a concatenação de campos produz
    artefatos como 'waist-up , vertical' que denunciam texto montado por máquina.
    """
    texto = " ".join(p.strip().rstrip(".") for p in partes if p and p.strip())
    if not texto:
        return ""
    texto = re.sub(r"\s+([,;:])", r"\1", texto)
    texto = re.sub(r",\s*,", ",", texto)
    texto = re.sub(r"\s{2,}", " ", texto)
    return texto[0].upper() + texto[1:] + "."


def _join_and(items):
    """Oxford comma para qualquer tamanho de lista.

    1 item  → 'x'
    2 itens → 'x and y'
    3+      → 'x, y, and z'   ← consertado; antes juntava sem 'and' final
    """
    n = len(items)
    if n == 0:
        return ""
    if n == 1:
        return items[0]
    if n == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _bloco_subject(spec):
    s = spec["subject"]
    assimetrias = _join_and(s["asymmetries"])
    marcas = ", ".join(s["preserved_marks"])
    return " ".join(
        filter(
            None,
            [
                _frase(s["description"]),
                # 'The subject's' em vez de 'Her' — o hardcoded quebrava frase
                # inteira quando o sujeito era masculino ou não-binário.
                _frase("The subject's facial structure is specifically asymmetric:", assimetrias),
                _frase(marcas[0].upper() + marcas[1:]),
                _frase("Vellus hair is", s.get("vellus_hair", "")),
                _frase("The expression is", s["expression"]),
            ],
        )
    )


def _bloco_wardrobe(spec):
    partes = []
    for peca in spec.get("wardrobe", []):
        vincos = _join_and(peca["tension_creases"])
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

    A geometria sai numa oração só ('at X degrees azimuth and <elevação>,
    Y metres away') em vez de três coordenadas: o custo em palavras de
    satisfazer o item 1 do checklist se multiplica pelo número de fontes.
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
    por_papel: dict[str, list] = {}
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
                _frase(
                    r["grain"],
                    "with" if r.get("chroma_noise") else "",
                    r.get("chroma_noise", ""),
                ),
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


# --------------------------------------------------------------------------- #
# Modalidades                                                                  #
# --------------------------------------------------------------------------- #

# Aspect ratios extras da Higgsfield versus a Gemini API. "auto" herda do input.
ASPECT_RATIOS_HIGGSFIELD = {
    "auto", "1:1", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "16:9", "9:16", "21:9"
}


def renderiza_modalidade_1(spec, incluir_output_no_texto: bool = True) -> tuple[str, str]:
    """Modalidade 1 — texto puro colável para a interface do Gemini."""
    o = spec["output"]
    if incluir_output_no_texto:
        orientacao = o.get("orientation")
        sufixo = (
            f", {orientacao} {o['aspect_ratio']} frame"
            if orientacao
            else f", {o['aspect_ratio']} frame"
        )
        cabecalho = _frase(spec["scene"]["headline"], sufixo)
    else:
        cabecalho = _frase(spec["scene"]["headline"])

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


def renderiza_modalidade_2(spec) -> tuple[str, str, dict]:
    """Modalidade 2 — texto colável para a interface Higgsfield + controles."""
    corpo, cauda = renderiza_modalidade_1(spec, incluir_output_no_texto=False)
    o = spec["output"]

    if o["aspect_ratio"] not in ASPECT_RATIOS_HIGGSFIELD:
        raise ValueError(
            f"aspect_ratio {o['aspect_ratio']!r} não é aceito pela Higgsfield em /nano-banana"
        )

    controles = {
        "model": "Nano Banana (endpoint /nano-banana)",
        "aspect_ratio": o["aspect_ratio"],
        "num_images": 1,
        "output_format": "jpeg",
        "input_images": [],
        "_nota_resolucao": (
            "A Higgsfield não expõe controle de resolução em /nano-banana. "
            "Se precisa de 4K auditável, use a modalidade 4."
        ),
    }
    return corpo, cauda, controles


def _colhe_refs(spec) -> list[str]:
    """URLs de referência agregadas — identidade e, em edição, o quadro origem."""
    refs = list(spec.get("character", {}).get("references_urls") or [])
    if spec["scene"]["regime"] == "edit":
        refs += list(spec.get("edit", {}).get("source_urls") or [])
    return refs


def renderiza_modalidade_3(spec) -> dict:
    """Modalidade 3 — payload REST para POST /nano-banana da Higgsfield."""
    if spec["output"]["aspect_ratio"] not in ASPECT_RATIOS_HIGGSFIELD:
        raise ValueError(
            f"aspect_ratio {spec['output']['aspect_ratio']!r} não é aceito por "
            "/nano-banana da Higgsfield"
        )

    corpo, cauda = renderiza_modalidade_1(spec, incluir_output_no_texto=False)
    payload = {
        "prompt": f"{corpo}\n\n{cauda}",
        "num_images": 1,
        "aspect_ratio": spec["output"]["aspect_ratio"],
        "output_format": "jpeg",
    }

    refs = _colhe_refs(spec)
    if refs:
        if len(refs) > 8:
            raise ValueError(
                f"{len(refs)} imagens de referência excede o teto de 8 do endpoint "
                "/nano-banana da Higgsfield"
            )
        payload["input_images"] = [{"type": "image_url", "image_url": u} for u in refs]

    return {
        "method": "POST",
        "url": "https://platform.higgsfield.ai/nano-banana",
        "headers": {
            "Authorization": "Key ${HF_API_KEY_ID}:${HF_API_KEY_SECRET}",
            "Content-Type": "application/json",
        },
        "body": payload,
    }


def renderiza_modalidade_4(spec) -> dict:
    """Modalidade 4 — payload para a API Gemini via google-genai."""
    corpo, cauda = renderiza_modalidade_1(spec, incluir_output_no_texto=False)
    prompt = f"{corpo}\n\n{cauda}"

    chamada = {
        "sdk": "google-genai",
        "model": spec["meta"]["target_model"],
        "contents": prompt,
        "config": {
            "response_modalities": ["IMAGE"],
            "image_config": {
                "aspect_ratio": spec["output"]["aspect_ratio"],
                "image_size": spec["output"]["resolution"],
            },
        },
    }
    refs = _colhe_refs(spec)
    if refs:
        chamada["contents"] = [prompt] + [{"image_url": u} for u in refs]
    return chamada


def por_modalidade(spec, modalidade: int):
    """Roteador — a Skill e a CLI chamam daqui, sem escolher assinatura à mão."""
    if modalidade == 1:
        corpo, cauda = renderiza_modalidade_1(spec)
        return {"modality": 1, "corpo": corpo, "cauda": cauda}
    if modalidade == 2:
        corpo, cauda, controles = renderiza_modalidade_2(spec)
        return {"modality": 2, "corpo": corpo, "cauda": cauda, "controles": controles}
    if modalidade == 3:
        return {"modality": 3, "envelope": renderiza_modalidade_3(spec)}
    if modalidade == 4:
        return {"modality": 4, "envelope": renderiza_modalidade_4(spec)}
    raise ValueError(f"modalidade desconhecida: {modalidade!r}")
