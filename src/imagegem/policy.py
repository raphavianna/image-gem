"""Política de conteúdo do sistema.

Do prompt-mestre, seção 'Política de conteúdo do sistema':

> O sistema não gera nem edita imagens fotorrealistas de pessoas reais
> identificáveis, exceto quando a própria pessoa é a referência fornecida pelo
> usuário para consistência de personagem; não gera imagens de menores; não
> produz conteúdo que simule documentos, evidências ou registros jornalísticos
> reais.

Este módulo aplica isso ao pedido do usuário **antes** de resolver o template
ou chamar qualquer cliente. Herdado por Skill, CLI e MCP.

Heurística, não classificador. Estratégia em duas camadas para reduzir falsos
positivos sem abrir mão da recusa:

- **Termos duros** — recusam sozinhos. `child`, `criança`, `passaporte`, etc.
- **Termos ambíguos** — em português `menor` e `jovem` têm sentido além de
  idade, e recusar sozinhos gera falso positivo em contexto óptico ou
  comparativo. Só recusam quando aparecem em janela próxima de um marcador
  de idade (número < 18, "de idade", "years old").
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


# --------------------------------------------------------------------------- #
# Menores                                                                     #
# --------------------------------------------------------------------------- #

# Termos que denunciam menor sem ambiguidade. Recusam sozinhos.
_MENOR_HARD_RE = re.compile(
    r"\b(child|children|kid|kids|infant|infants|toddler|toddlers|"
    r"teenager|teenagers|teen|teens|preteen|preteens|schoolboy|schoolgirl|"
    r"adolescente|adolescentes|crian[cç]a|crian[cç]as|"
    r"menina|meninas|menino|meninos|beb[eê]|beb[eê]s)\b",
    re.IGNORECASE,
)

# Termos ambíguos em PT-BR — 'menor' também significa 'de tamanho menor',
# 'jovem' também designa adulto jovem. Só recusam com corroboração.
_MENOR_SOFT_RE = re.compile(r"\b(menor|jovem)\b", re.IGNORECASE)

# Marcadores que corroboram sentido de idade infantil: 'de idade escolar',
# 'idade escolar', ou nada específico + sem idade adulta declarada.
_IDADE_INFANTIL_RE = re.compile(
    r"\b(idade\s+escolar|elementary|middle\s+school|high\s+school|"
    r"escola\s+prim[aá]ria|jovem\s+demais|too\s+young)\b",
    re.IGNORECASE,
)

# Idade numérica declarada. Captura número seguido de anos/years/yo.
_IDADE_NUM_RE = re.compile(
    r"\b(\d{1,2})[\s\-]?(?:year|years|anos?|yr|y[\-\s]?o)\b",
    re.IGNORECASE,
)


def _termo_ambiguo_denuncia_menor(texto: str) -> bool:
    """Termo ambíguo ('menor', 'jovem') sinaliza menor apenas se:
    - marcador de idade infantil aparece em alguma parte do texto, E
    - não há declaração de idade adulta (≥18) em nenhum lugar.

    Isso mata os falsos positivos ('menor dos dois relógios', 'jovem
    executivo', 'jovem adulto de 30 anos') sem afrouxar a barreira.
    """
    if not _MENOR_SOFT_RE.search(texto):
        return False
    # Se há idade numérica declarada, o passo 1 já teria bloqueado se < 18.
    # Se chegou aqui, qualquer idade declarada é ≥ 18 — então não é menor.
    if _IDADE_NUM_RE.search(texto):
        return False
    # Sem número de idade, só bloqueia se marcador infantil aparece.
    return bool(_IDADE_INFANTIL_RE.search(texto))


# --------------------------------------------------------------------------- #
# Documentos e imagem jornalística                                            #
# --------------------------------------------------------------------------- #

_DOCUMENTO_RE = re.compile(
    r"\b(passport|passaporte|id\s?card|identidade|driver'?s?\s?license|"
    r"cnh|carteira\s+de\s+motorista|receipt|recibo|invoice|nota\s+fiscal|"
    r"press\s+photo|imagem\s+jornal[íi]stica|news\s+photo|forensic|evid[eê]ncia|"
    r"crime\s+scene|cena\s+de\s+crime)\b",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- #
# Pessoas reais identificáveis                                                #
# --------------------------------------------------------------------------- #

# Padrão 1: dois nomes próprios em sequência, aceitando conector minúsculo
# entre eles (da, de, do, van, von, etc.). Sem o conector, 'Lula da Silva'
# escapava porque 'da' quebrava a sequência de duas capitalizadas.
_NOME_SOBRENOME_RE = re.compile(
    r"\b[A-ZÁÀÂÃÉÊÍÓÔÕÚÜ][a-záàâãéêíóôõúüç]+"
    r"(?:\s+(?:da|de|do|das|dos|von|van|di|del|la|el)\s+"
    r"|\s+)"
    r"[A-ZÁÀÂÃÉÊÍÓÔÕÚÜ][a-záàâãéêíóôõúüç]+\b"
)

# Padrão 2: título + nome próprio único (para figuras conhecidas por primeiro
# nome ou por título). Pega "presidente Lula", "papa Francisco",
# "the President", "a rainha".
_TITULO_NOME_RE = re.compile(
    r"\b("
    r"presidente|president|primeir[oa][\-\s]ministr[oa]|prime\s+minister|"
    r"pap[ae]|pope|rei|rainha|king|queen|principe|princesa|prince|princess|"
    r"chanceler|chancellor|imperador|imperatriz|"
    r"senador[a]?|senator|deputad[oa]|governador[a]?|governor|"
    r"prefeit[oa]|mayor|ceo|founder|fundador[a]?|"
    r"ex[\-\s]presidente|ex[\-\s]president|"
    r"primeir[oa][\-\s]dama|first\s+lady"
    r")\b",
    re.IGNORECASE,
)

# Padrão 3: figura pública conhecida por um nome só. Lista curta e conservadora.
# Não é exaustiva; falsos negativos vão passar. Documentado.
_MONONIMO_RE = re.compile(
    r"\b(beyonc[eé]|madonna|rihanna|shakira|pel[eé]|ronaldinho|neymar|"
    r"messi|ronaldo|zidane|mbapp[eé]|lula|dilma|bolsonaro|obama|trump|"
    r"biden|putin|zelensky|zelenskyy|macron|merkel|erdogan|"
    r"elon|zuckerberg|bezos|musk|gates|jobs|banksy|"
    r"drake|adele|eminem|jay[\-\s]z|nicki|kanye|beyonce)\b",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- #
# API pública                                                                  #
# --------------------------------------------------------------------------- #


def check_pedido(pedido: str, tem_referencia: bool = False) -> Decisao:
    """Avalia se o pedido em linguagem natural é permitido.

    `tem_referencia=True` — o usuário anexou a própria imagem, o caminho
    autorizado para gerar pessoa identificável conforme o prompt-mestre.
    """
    texto = pedido or ""

    # 1) Idade numérica abaixo de 18 — barreira dura.
    for m in _IDADE_NUM_RE.finditer(texto):
        try:
            idade = int(m.group(1))
        except ValueError:
            continue
        if idade < 18:
            return Decisao(
                False,
                f"Recuso: idade declarada ({idade}) abaixo de 18 — o sistema não "
                "gera imagens de menores.",
            )

    # 2) Termos duros de menor.
    if _MENOR_HARD_RE.search(texto):
        return Decisao(
            False,
            "Recuso: o sistema não gera nem edita imagens de menores.",
        )

    # 3) Termos ambíguos ('menor', 'jovem') — só recusam sem idade adulta declarada
    #    e com marcador de infância presente. Ver _termo_ambiguo_denuncia_menor.
    if _termo_ambiguo_denuncia_menor(texto):
        return Decisao(
            False,
            "Recuso: 'menor'/'jovem' em contexto de idade — o sistema não "
            "gera imagens de menores.",
        )

    # 4) Documentos e simulação jornalística.
    if _DOCUMENTO_RE.search(texto):
        return Decisao(
            False,
            "Recuso: o sistema não produz simulação de documento oficial, "
            "recibo, evidência ou imagem jornalística.",
        )

    # 5) Pessoas reais identificáveis, sem referência anexada.
    if not tem_referencia:
        # Padrão 1: nome + sobrenome capitalizados.
        sobrenomes = _NOME_SOBRENOME_RE.findall(texto)
        if sobrenomes:
            return Decisao(
                False,
                f"Recuso: o pedido menciona pessoa identificável ({sobrenomes[0]}) e "
                "nenhuma referência da própria pessoa foi anexada. Para gerar com "
                "identidade preservada, forneça uma imagem sua e use o template "
                "consistencia-personagem.",
            )
        # Padrão 2: título + nome (ou 'the president', 'o presidente' isolado).
        m = _TITULO_NOME_RE.search(texto)
        if m:
            return Decisao(
                False,
                f"Recuso: o pedido menciona figura pública por título ({m.group(0)!r}). "
                "Se pretende gerar personagem fictícia com esse papel, descreva "
                "traços físicos sem título institucional; se pretende gerar a "
                "pessoa real, forneça imagem de referência da própria pessoa.",
            )
        # Padrão 3: mononimo de figura pública conhecida.
        m = _MONONIMO_RE.search(texto)
        if m:
            return Decisao(
                False,
                f"Recuso: o pedido menciona figura pública identificável "
                f"({m.group(0)!r}). Forneça imagem de referência da própria pessoa "
                "ou descreva um personagem fictício sem citar nome real.",
            )

    return Decisao(True)
