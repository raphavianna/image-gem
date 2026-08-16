"""Política de conteúdo do sistema.

Do prompt-mestre, seção 'Política de conteúdo do sistema', literal e curta:

> O sistema não gera nem edita imagens fotorrealistas de pessoas reais
> identificáveis, exceto quando a própria pessoa é a referência fornecida pelo
> usuário para consistência de personagem; não gera imagens de menores; não
> produz conteúdo que simule documentos, evidências ou registros jornalísticos
> reais.

Este módulo aplica isso ao pedido do usuário **antes** de resolver o template
ou chamar qualquer cliente. Herdado por Skill, CLI e MCP.

Heurística, não classificador: pega os padrões óbvios em texto e recusa com
explicação de uma linha. Falsos negativos vão passar; falsos positivos são
preferíveis a gerar um conteúdo vetado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Decisao:
    permitido: bool
    razao: str = ""

    def __bool__(self) -> bool:
        return self.permitido


# Padrões de idade que denunciam menor: "criança", "menina/menino", "adolescente",
# "teen(ager)?", números "10 anos", "5-year-old" abaixo de 18.
_MENOR_RE = re.compile(
    r"\b(child|children|kid|kids|infant|toddler|teenager|teen|adolescente|crian[cç]a|"
    r"menor|menina|menino|jovem)\b",
    re.IGNORECASE,
)
_IDADE_NUM_RE = re.compile(r"\b(\d{1,2})[\s\-]?(?:year|years|anos?|yr|y[\-\s]?o)\b", re.IGNORECASE)

# Documentos e simulação jornalística — palavras que indicam intento.
_DOCUMENTO_RE = re.compile(
    r"\b(passport|passaporte|id\s?card|identidade|driver'?s?\s?license|"
    r"cnh|carteira\s+de\s+motorista|receipt|recibo|invoice|nota\s+fiscal|"
    r"press\s+photo|imagem\s+jornal[íi]stica|news\s+photo|forensic|evid[eê]ncia)\b",
    re.IGNORECASE,
)

# Pessoas reais identificáveis: nome de figura pública mais "photorealistic"
# ou "foto (realista)". Padrão bem simples e de propósito conservador — palavras
# como "Presidente Silva" ou nome + sobrenome capitalizados.
_NOME_PROPRIO_RE = re.compile(
    r"\b[A-Z][a-záàâãéêíóôõúü]+\s+[A-Z][a-záàâãéêíóôõúü]+\b"
)


def check_pedido(pedido: str, tem_referencia: bool = False) -> Decisao:
    """Avalia se o pedido em linguagem natural é permitido.

    `tem_referencia=True` significa que o usuário anexou a própria imagem — o
    caminho autorizado para gerar pessoa identificável, conforme o prompt-mestre.
    """
    texto = pedido or ""

    # Menores.
    if _MENOR_RE.search(texto):
        return Decisao(False, "Recuso: o sistema não gera nem edita imagens de menores.")
    for m in _IDADE_NUM_RE.finditer(texto):
        try:
            idade = int(m.group(1))
        except ValueError:
            continue
        if idade < 18:
            return Decisao(
                False,
                f"Recuso: idade declarada ({idade}) abaixo de 18 — o sistema não gera imagens de menores.",
            )

    # Documentos e jornalismo simulado.
    if _DOCUMENTO_RE.search(texto):
        return Decisao(
            False,
            "Recuso: o sistema não produz simulação de documento oficial, "
            "recibo, evidência ou imagem jornalística.",
        )

    # Pessoas reais identificáveis por nome, sem referência anexada.
    if not tem_referencia:
        nomes = _NOME_PROPRIO_RE.findall(texto)
        if nomes:
            return Decisao(
                False,
                f"Recuso: o pedido menciona pessoa identificável ({nomes[0]}) e "
                "nenhuma referência da própria pessoa foi anexada. Para gerar com "
                "a identidade preservada, forneça uma imagem sua e use o template "
                "consistencia-personagem.",
            )

    return Decisao(True)
