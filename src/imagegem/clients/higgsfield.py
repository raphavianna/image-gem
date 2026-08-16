"""Cliente da API Higgsfield para a modalidade 3.

Implementa o ciclo assíncrono completo do endpoint `POST /nano-banana`:

    POST /nano-banana      → { queued, request_id, status_url }
    GET  {status_url}       → { in_progress | completed | failed | nsfw | canceled }
    GET  {status_url}       → { completed, images: [{ url }] }

Backoff: começa em 2s, sobe até 10s, com jitter — a estratégia recomendada
em `[HF]` (`concepts/polling.md`).

Sem chave de idempotência para POST `[HF]` — grava `request_id` **antes** de
qualquer retry ambíguo. Retry de GET status é seguro; retry cego de POST cobra
crédito duplicado.

Modo simulação: quando `HF_API_KEY_ID` ou `HF_API_KEY_SECRET` faltam, imprime
o payload e devolve resultado sintético — mesmo formato do caminho real.
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from urllib.parse import quote

import httpx

from imagegem import render


BASE_URL = "https://platform.higgsfield.ai"


@dataclass
class Resultado:
    modo: str  # "real" ou "simulacao"
    status: str  # completed | failed | nsfw | canceled | simulated
    request_id: str | None
    images: list[dict]           # [{"url": ..., "content_type": ...}]
    raw: dict                    # último response cru
    correlation_id: str | None = None
    error: str | None = None


def credenciais_disponiveis() -> bool:
    return bool(os.environ.get("HF_API_KEY_ID") and os.environ.get("HF_API_KEY_SECRET"))


def _auth_header() -> str:
    return f"Key {os.environ['HF_API_KEY_ID']}:{os.environ['HF_API_KEY_SECRET']}"


def submit(spec: dict, *, webhook: str | None = None, timeout_s: float = 600.0) -> Resultado:
    """Submete e faz polling até estado terminal ou timeout.

    Sem credencial, entra em simulação — devolve resultado sintético.
    """
    envelope = render.renderiza_modalidade_3(spec)

    if not credenciais_disponiveis():
        return _simulacao(envelope)

    return _chamada_real(envelope, webhook=webhook, timeout_s=timeout_s)


def estimate(spec: dict) -> dict:
    """`POST /estimate/nano-banana` — devolve custo sem consumir créditos."""
    envelope = render.renderiza_modalidade_3(spec)
    if not credenciais_disponiveis():
        return {"modo": "simulacao", "credits": None, "usd": None, "note": "sem credencial"}
    url = BASE_URL + "/estimate/nano-banana"
    r = httpx.post(
        url,
        headers={"Authorization": _auth_header(), "Content-Type": "application/json"},
        json=envelope["body"],
        timeout=30.0,
    )
    r.raise_for_status()
    return r.json() | {"modo": "real"}


def _simulacao(envelope: dict) -> Resultado:
    body = envelope["body"]
    print("[higgsfield:simulacao] payload que iria para POST /nano-banana:")
    print(f"  url:           {envelope['url']}")
    print(f"  aspect_ratio:  {body['aspect_ratio']}")
    print(f"  num_images:    {body['num_images']}")
    print(f"  prompt:        {len(body['prompt'].split())} palavras")
    print(f"  input_images:  {len(body.get('input_images', []))}")
    return Resultado(
        modo="simulacao",
        status="simulated",
        request_id=None,
        images=[],
        raw={"envelope": envelope},
    )


def _chamada_real(envelope: dict, *, webhook: str | None, timeout_s: float) -> Resultado:
    url = envelope["url"]
    if webhook:
        url = f"{url}?hf_webhook={quote(webhook, safe='')}"

    with httpx.Client(timeout=60.0) as client:
        # POST — grava request_id antes de qualquer retry ambíguo.
        try:
            r = client.post(
                url,
                headers={"Authorization": _auth_header(), "Content-Type": "application/json"},
                json=envelope["body"],
            )
        except httpx.HTTPError as e:
            return Resultado(modo="real", status="failed", request_id=None, images=[], raw={}, error=str(e))

        correlation_id = r.headers.get("X-Correlation-ID")
        if r.status_code >= 400:
            return Resultado(
                modo="real", status="failed", request_id=None, images=[], raw=_body(r),
                correlation_id=correlation_id, error=f"HTTP {r.status_code}: {_body(r).get('detail')}",
            )

        inicial = r.json()
        request_id = inicial["request_id"]
        status_url = inicial["status_url"]

        # Poll com backoff 2s → 10s + jitter, estratégia [HF] `concepts/polling.md`.
        atraso = 2.0
        prazo = time.time() + timeout_s
        atual = inicial

        while atual["status"] not in ("completed", "failed", "nsfw", "canceled"):
            if time.time() > prazo:
                return Resultado(
                    modo="real", status="failed", request_id=request_id, images=[], raw=atual,
                    correlation_id=correlation_id,
                    error=f"timeout de {timeout_s:g}s ainda em {atual['status']}",
                )
            time.sleep(atraso + random.uniform(0, 0.5))
            atraso = min(atraso * 1.5, 10.0)

            try:
                r = client.get(status_url, headers={"Authorization": _auth_header()})
                r.raise_for_status()
                atual = r.json()
            except httpx.HTTPError as e:
                # Retry de GET é seguro — continua o loop com o mesmo atraso.
                atual = atual | {"transient_error": str(e)}

    imagens = atual.get("images") or []
    return Resultado(
        modo="real",
        status=atual["status"],
        request_id=request_id,
        images=imagens,
        raw=atual,
        correlation_id=correlation_id,
        error=atual.get("error"),
    )


def _body(r) -> dict:
    try:
        return r.json()
    except Exception:
        return {"detail": r.text}


def upload_image(caminho: str, content_type: str = "image/jpeg") -> str:
    """Fluxo presigned URL: `POST /files/generate-upload-url` → PUT bytes.

    Devolve o `public_url` que serve para `input_images[].image_url`.
    """
    if not credenciais_disponiveis():
        raise RuntimeError("upload_image requer HF_API_KEY_ID e HF_API_KEY_SECRET")

    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            BASE_URL + "/files/generate-upload-url",
            headers={"Authorization": _auth_header(), "Content-Type": "application/json"},
            json={"content_type": content_type},
        )
        r.raise_for_status()
        info = r.json()

        with open(caminho, "rb") as f:
            put = httpx.put(
                info["upload_url"],
                headers=info["upload_headers"],
                content=f.read(),
                timeout=120.0,
            )
        put.raise_for_status()
    return info["public_url"]
