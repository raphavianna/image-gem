"""Registro versionado de cada execução para o loop da E6.

Cada geração produz uma pasta em `runs/`:

    runs/YYYYmmdd-HHMMSS-<slug>/
        spec.json         # o spec canônico usado
        prompt.txt        # o corpo + cauda que foram para o modelo
        envelope.json     # o envelope da modalidade (payload ou controles)
        response.json     # tudo que o cliente devolveu, cru
        metadata.json     # template, modalidade, cliente, timing, correlação
        image_00.jpg      # imagens salvas pelo cliente, quando houver

A trilha `meta.defaults_applied[]` no spec.json é o que a E6 usa para
correlacionar aparência do resultado com escolha de default do template.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from imagegem import schema


@dataclass
class Registro:
    id: str
    template: str | None
    modality: int
    client: str
    started_at: float
    finished_at: float | None = None
    status: str = "started"
    error: str | None = None
    correlation_id: str | None = None
    extra: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> int | None:
        if self.finished_at is None:
            return None
        return int((self.finished_at - self.started_at) * 1000)


def _slug(texto: str, max_len: int = 32) -> str:
    s = re.sub(r"[^\w\-]+", "-", (texto or "").strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len] or "sem-titulo"


def register(
    *,
    spec: dict,
    envelope: dict,
    prompt: str,
    response: dict | None,
    client: str,
    correlation_id: str | None = None,
    error: str | None = None,
    started_at: float | None = None,
    imagens: list[bytes] | None = None,
) -> Path:
    """Persiste um registro completo. Devolve o caminho da pasta."""
    started_at = started_at or time.time()
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime(started_at))
    template = (spec.get("meta") or {}).get("template", "sem-template")
    request_id = (response or {}).get("request_id") or _slug(template)
    nome = f"{stamp}-{_slug(request_id)}"

    pasta = schema.RUNS_DIR / nome
    pasta.mkdir(parents=True, exist_ok=True)

    (pasta / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    (pasta / "prompt.txt").write_text(prompt, encoding="utf-8")
    (pasta / "envelope.json").write_text(json.dumps(envelope, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if response is not None:
        (pasta / "response.json").write_text(json.dumps(response, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    registro = Registro(
        id=nome,
        template=template,
        modality=spec["meta"]["modality"],
        client=client,
        started_at=started_at,
        finished_at=time.time(),
        status="failed" if error else "completed",
        error=error,
        correlation_id=correlation_id,
        extra={"defaults_applied_count": len(spec.get("meta", {}).get("defaults_applied", []))},
    )
    (pasta / "metadata.json").write_text(
        json.dumps(asdict(registro) | {"duration_ms": registro.duration_ms}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for i, img in enumerate(imagens or []):
        (pasta / f"image_{i:02d}.jpg").write_bytes(img)

    return pasta


def list_recent(limit: int = 20) -> list[dict[str, Any]]:
    """Lista os registros mais recentes com metadados carregados."""
    if not schema.RUNS_DIR.exists():
        return []
    pastas = sorted(schema.RUNS_DIR.iterdir(), reverse=True)[:limit]
    out = []
    for p in pastas:
        meta = p / "metadata.json"
        if meta.exists():
            out.append(json.loads(meta.read_text(encoding="utf-8")))
    return out
