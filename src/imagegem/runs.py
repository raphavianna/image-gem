"""Registro versionado de execuções — insumo do loop da E6.

Cada geração produz uma pasta em `runs/YYYYmmdd-HHMMSS-<slug>/`:

    spec.json         # o spec canônico usado, com meta.defaults_applied
    prompt.txt        # o corpo + cauda que foram para o modelo
    envelope.json     # o envelope da modalidade (payload ou controles)
    response.json     # tudo que o cliente devolveu, cru
    metadata.json     # conforme schemas/run-record.json — validado ao gravar
    image_XX.jpg      # imagens salvas pelo cliente, quando houver

A trilha `meta.defaults_applied[]` no spec.json + `spec_hash` no metadata.json
são o par que a E6 usa para correlacionar aparência do resultado com escolha
de default e detectar regressões.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from imagegem import schema


RECORD_SCHEMA_PATH = schema.SCHEMA_PATH.parent / "run-record.json"


def _record_schema() -> dict:
    return json.loads(RECORD_SCHEMA_PATH.read_text(encoding="utf-8"))


def _slug(texto: str, max_len: int = 32) -> str:
    s = re.sub(r"[^\w\-]+", "-", (texto or "").strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len] or "sem-titulo"


def _hash_spec(spec: dict) -> str:
    """SHA-256 do spec serializado deterministicamente (chaves ordenadas)."""
    corpo = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(corpo.encode("utf-8")).hexdigest()


def _checklist_signature(spec: dict) -> str:
    """Ids das regras+checks que se aplicam a este spec, em ordem canônica.

    Prova que dois registros foram avaliados com o mesmo rigor. Se a signature
    muda entre execuções do mesmo template, alguma condição de aplicabilidade
    mudou — sinal para investigar antes de comparar resultados.
    """
    # Import tardio para evitar ciclo (check → render → check via validate).
    from imagegem import check as _check

    cfg = schema.cfg()
    ids: list[str] = []
    for regra in cfg["regras_de_coerencia"]:
        if _check.aplica(regra, spec):
            ids.append(regra["id"])
    for item in cfg["checklist_de_emissao"]:
        if _check.aplica(item, spec):
            ids.append(f"ck{item['item']}")
    return "|".join(ids)


def _valida(record: dict) -> None:
    """Valida o metadata contra schemas/run-record.json — falha ruidosamente."""
    jsonschema.Draft202012Validator(_record_schema()).validate(record)


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
    """Persiste um registro completo. Devolve o caminho da pasta.

    O metadata é validado contra `schemas/run-record.json` antes de gravar.
    Se o schema reprova, `jsonschema.ValidationError` sobe — melhor falhar do
    que gravar um registro que o loop da E6 não consegue ler.
    """
    started_at = started_at or time.time()
    finished_at = time.time()
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

    status = response.get("status") if response else None
    if not status:
        status = "failed" if error else "completed"

    template_meta = schema.load_template(template) if template != "sem-template" else {}
    record = {
        "record_version": "1.0",
        "id": nome,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": int((finished_at - started_at) * 1000),
        "status": status,
        "error": error,
        "template": template,
        "template_version": template_meta.get("template_version", "unknown"),
        "spec_hash": _hash_spec(spec),
        "schema_version": spec.get("spec_version", "unknown"),
        "modality": spec["meta"]["modality"],
        "client": client,
        "correlation_id": correlation_id,
        "request_id": (response or {}).get("request_id"),
        "defaults_applied_count": len((spec.get("meta") or {}).get("defaults_applied", [])),
        "prompt_word_count": len(prompt.split()) if prompt else None,
        "checklist_signature": _checklist_signature(spec),
    }
    _valida(record)
    (pasta / "metadata.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    for i, img in enumerate(imagens or []):
        (pasta / f"image_{i:02d}.jpg").write_bytes(img)

    return pasta


# --------------------------------------------------------------------------- #
# Leitura e avaliação                                                          #
# --------------------------------------------------------------------------- #


def load(run_id_or_path: str | Path) -> tuple[Path, dict]:
    """Carrega uma pasta de registro. Devolve (caminho, metadata)."""
    p = Path(run_id_or_path)
    if not p.exists():
        p = schema.RUNS_DIR / str(run_id_or_path)
    if not p.exists():
        raise FileNotFoundError(f"registro {run_id_or_path!r} não encontrado")
    meta = json.loads((p / "metadata.json").read_text(encoding="utf-8"))
    return p, meta


def review(
    run_id_or_path: str | Path,
    *,
    verdict: str,
    reviewer: str = "user",
    rating: int | None = None,
    notes: str = "",
    signals: list[dict] | None = None,
    follow_ups: list[dict] | None = None,
) -> Path:
    """Escreve/atualiza a seção `review` do metadata.

    Um registro pode ser revisado múltiplas vezes — a última avaliação vence,
    porque a decisão do humano é o estado de verdade que interessa ao loop.
    """
    pasta, meta = load(run_id_or_path)
    meta["review"] = {
        "verdict": verdict,
        "reviewer": reviewer,
        "reviewed_at": time.time(),
        "notes": notes,
    }
    if rating is not None:
        meta["review"]["rating"] = rating
    if signals:
        meta["review"]["signals"] = signals
    if follow_ups:
        meta["review"]["follow_ups"] = follow_ups
    _valida(meta)
    (pasta / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return pasta


def list_recent(limit: int = 20, *, only_reviewed: bool = False) -> list[dict[str, Any]]:
    """Registros mais recentes com metadados carregados."""
    if not schema.RUNS_DIR.exists():
        return []
    pastas = sorted(schema.RUNS_DIR.iterdir(), reverse=True)
    out = []
    for p in pastas:
        m = p / "metadata.json"
        if not m.exists():
            continue
        meta = json.loads(m.read_text(encoding="utf-8"))
        if only_reviewed and "review" not in meta:
            continue
        out.append(meta)
        if len(out) >= limit:
            break
    return out


def pending_follow_ups(limit: int = 100) -> list[dict[str, Any]]:
    """Follow-ups revisados mas ainda não promovidos, por registro.

    A E6 usa isso para gerar a próxima entrada de docs/04-aprendizados.md.
    """
    out = []
    for meta in list_recent(limit=limit, only_reviewed=True):
        for fu in meta["review"].get("follow_ups", []):
            if not fu.get("promoted_to"):
                out.append({
                    "run_id": meta["id"],
                    "template": meta["template"],
                    "spec_hash": meta["spec_hash"],
                    **fu,
                })
    return out
