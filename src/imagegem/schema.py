"""Carrega o schema canônico e expõe caminhos, configurações e constantes.

O schema é a **fonte única de verdade** para regras de coerência, checklist e
orçamentos. Nenhum outro módulo hardcoda esses valores — todos leem daqui.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

# Raiz do repositório, calculada relativa a este arquivo em src/imagegem/.
RAIZ = Path(__file__).resolve().parents[2]

SCHEMA_PATH = RAIZ / "schemas" / "prompt-spec.json"
TEMPLATES_DIR = RAIZ / "templates"
EXEMPLOS_DIR = RAIZ / "schemas" / "exemplos"
RUNS_DIR = RAIZ / "runs"


@lru_cache(maxsize=1)
def load() -> dict:
    """Carrega e cacheia o schema canônico."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def cfg() -> dict:
    """Bloco `x-imagegem` do schema — regras não expressáveis em JSON Schema."""
    return load()["x-imagegem"]


def load_template(nome_ou_caminho: str | Path) -> dict:
    """Carrega um template por nome (`retrato-estudio`) ou caminho absoluto."""
    caminho = Path(nome_ou_caminho)
    if not caminho.suffix:
        caminho = TEMPLATES_DIR / f"{nome_ou_caminho}.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def load_exemplo(nome_ou_caminho: str | Path) -> dict:
    """Carrega uma instância de `schemas/exemplos/`."""
    caminho = Path(nome_ou_caminho)
    if not caminho.suffix:
        caminho = EXEMPLOS_DIR / f"{nome_ou_caminho}.json"
    return json.loads(caminho.read_text(encoding="utf-8"))
