"""Cliente da API Gemini para a modalidade 4.

Usa `google-genai` quando `GEMINI_API_KEY` está no ambiente; caso contrário
entra em **modo simulação** — imprime o payload e devolve uma resposta
sintética.

O envelope vem de `render.renderiza_modalidade_4(spec)`. Este módulo apenas
executa; a decisão de o que chamar mora no `spec` e no renderizador.

Notas de fonte:
- SDK path e ImageConfig: `[SDK]` `googleapis/python-genai/types.py`.
- `image_size` 1K/2K/4K e preço por resolução: `[GAI]` `docs/00-fontes/06-*.md`.
- `include_thoughts` para diagnóstico (E6): `[CB]`.
- Resposta pode conter múltiplas imagens (`[CB]`) — o leitor itera.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from imagegem import render


@dataclass
class Resultado:
    modo: str  # "real" ou "simulacao"
    imagens: list[bytes]      # bytes brutos das imagens; vazio em simulação
    thoughts: list[str]       # partes de raciocínio quando include_thoughts=True
    raw: dict                 # resposta bruta, para o registro
    error: str | None = None


def credenciais_disponiveis() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def submit(spec: dict, *, include_thoughts: bool = False) -> Resultado:
    """Envia o spec para a Gemini API e devolve o resultado.

    Sem `GEMINI_API_KEY` volta simulação — mesmo formato de resultado, sem
    bytes de imagem.
    """
    envelope = render.renderiza_modalidade_4(spec)
    if include_thoughts:
        envelope["config"]["thinking_config"] = {"include_thoughts": True}

    if not credenciais_disponiveis():
        return _simulacao(envelope)

    return _chamada_real(envelope, include_thoughts=include_thoughts)


def _simulacao(envelope: dict) -> Resultado:
    """Fallback sem credencial. Imprime o payload, devolve resposta sintética."""
    print("[gemini:simulacao] payload que iria para google-genai:")
    print(f"  model:  {envelope['model']}")
    ic = envelope["config"]["image_config"]
    print(f"  image:  aspect_ratio={ic['aspect_ratio']}, image_size={ic['image_size']}")
    contents = envelope["contents"]
    if isinstance(contents, str):
        print(f"  prompt: {len(contents.split())} palavras")
    else:
        prompt = contents[0] if contents else ""
        refs = [c for c in contents[1:] if isinstance(c, dict)]
        print(f"  prompt: {len(prompt.split())} palavras + {len(refs)} referências")
    return Resultado(
        modo="simulacao",
        imagens=[],
        thoughts=[],
        raw={"status": "simulated", "envelope": envelope},
    )


def _chamada_real(envelope: dict, *, include_thoughts: bool) -> Resultado:
    """Executa via `google-genai`. Isolado num bloco try por import opcional."""
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        return Resultado(
            modo="real",
            imagens=[],
            thoughts=[],
            raw={},
            error=f"google-genai não instalado: pip install 'imagegem[gemini]' ({e})",
        )

    client = genai.Client()  # lê GEMINI_API_KEY do ambiente

    ic = envelope["config"]["image_config"]
    kw = {
        "model": envelope["model"],
        "contents": envelope["contents"],
        "config": types.GenerateContentConfig(
            response_modalities=envelope["config"]["response_modalities"],
            image_config=types.ImageConfig(
                aspect_ratio=ic["aspect_ratio"],
                image_size=ic["image_size"],
            ),
            thinking_config=(
                types.ThinkingConfig(include_thoughts=True) if include_thoughts else None
            ),
        ),
    }

    try:
        resposta = client.models.generate_content(**kw)
    except Exception as e:
        return Resultado(modo="real", imagens=[], thoughts=[], raw={}, error=str(e))

    imagens: list[bytes] = []
    thoughts: list[str] = []

    # [CB]: iterar sobre todas as partes; não parar na primeira imagem.
    for candidate in getattr(resposta, "candidates", []) or []:
        for part in getattr(candidate.content, "parts", []) or []:
            if getattr(part, "thought", False) and getattr(part, "text", None):
                thoughts.append(part.text)
            data = getattr(part, "inline_data", None)
            if data and getattr(data, "data", None):
                b = data.data
                if isinstance(b, str):
                    b = base64.b64decode(b)
                imagens.append(b)

    return Resultado(
        modo="real",
        imagens=imagens,
        thoughts=thoughts,
        raw={"model": envelope["model"], "num_images": len(imagens)},
    )
