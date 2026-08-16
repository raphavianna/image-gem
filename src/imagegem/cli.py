"""CLI `imagegem` — amarra pipeline sobre o schema canônico.

Subcomandos:
    validate  SPEC                    → roda schema + coerência + checklist
    render    SPEC [--modality N]      → gera o envelope da modalidade
    resolve   TEMPLATE [--answers J]   → resolve template + respostas em spec
    submit    SPEC --modality {3,4}    → chama o cliente correspondente
    estimate  SPEC --modality 3        → custo sem consumir créditos (Higgsfield)
    templates                          → lista todos os templates disponíveis

Sem credenciais, `submit` cai em modo simulação — imprime o payload e
devolve resposta sintética.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from imagegem import check, policy, render, resolver, runs, schema
from imagegem.clients import gemini, higgsfield


def _carrega(caminho: str) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def _cmd_validate(args) -> int:
    spec = _carrega(args.spec)
    falhas, corpo, _ = check.validate(spec)
    if falhas:
        print(f"REPROVADO — {len(falhas)} falha(s):")
        for f in falhas:
            print(f"  - {f}")
        return 1
    faixa = check.faixa_de_densidade(spec, schema.cfg())
    print(f"OK — corpo {len(corpo.split())}p, faixa {faixa['min_palavras']}–{faixa['max_palavras']}")
    return 0


def _cmd_render(args) -> int:
    spec = _carrega(args.spec)
    saida = render.por_modalidade(spec, args.modality)
    print(json.dumps(saida, ensure_ascii=False, indent=2, default=str))
    return 0


def _cmd_resolve(args) -> int:
    template = schema.load_template(args.template)
    answers = _carrega(args.answers) if args.answers else None

    # Política de conteúdo aplicada antes de resolver.
    pedido = (answers or template.get("example_answers", {})).get("meta.user_request", "")
    tem_ref = bool(
        (answers or template.get("example_answers", {})).get("character.references_urls")
    )
    veredito = policy.check_pedido(pedido, tem_referencia=tem_ref)
    if not veredito:
        print(f"POLÍTICA DE CONTEÚDO: {veredito.razao}")
        return 2

    try:
        spec = resolver.resolve(template, answers)
    except ValueError as e:
        print(f"ERRO: {e}")
        return 1

    if args.out:
        Path(args.out).write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"spec escrito em {args.out}")
    else:
        print(json.dumps(spec, ensure_ascii=False, indent=2))
    return 0


def _cmd_submit(args) -> int:
    spec = _carrega(args.spec)

    # Valida antes de gastar créditos.
    falhas, corpo, cauda = check.validate(spec)
    if falhas:
        print(f"REPROVADO no checklist ({len(falhas)} falha(s)); submissão cancelada")
        for f in falhas:
            print(f"  - {f}")
        return 1

    if args.modality == 3:
        resultado = higgsfield.submit(spec)
        envelope = render.renderiza_modalidade_3(spec)
        client_name = "higgsfield"
        response = {
            "modo": resultado.modo,
            "status": resultado.status,
            "request_id": resultado.request_id,
            "images": resultado.images,
            "error": resultado.error,
            "correlation_id": resultado.correlation_id,
        }
    elif args.modality == 4:
        resultado = gemini.submit(spec, include_thoughts=args.thoughts)
        envelope = render.renderiza_modalidade_4(spec)
        client_name = "gemini"
        response = {
            "modo": resultado.modo,
            "num_images": len(resultado.imagens),
            "thoughts_count": len(resultado.thoughts),
            "error": resultado.error,
        }
    else:
        print("ERRO: submit exige --modality 3 ou --modality 4")
        return 1

    pasta = runs.register(
        spec=spec,
        envelope=envelope,
        prompt=f"{corpo}\n\n{cauda}",
        response=response,
        client=client_name,
        correlation_id=getattr(resultado, "correlation_id", None),
        error=getattr(resultado, "error", None),
        imagens=(getattr(resultado, "imagens", None) or []) if client_name == "gemini" else None,
    )
    print(f"registro salvo em {pasta}")

    if getattr(resultado, "error", None):
        print(f"FALHA: {resultado.error}")
        return 1
    print(f"OK — modo={resultado.modo} status={getattr(resultado, 'status', 'completed')}")
    return 0


def _cmd_estimate(args) -> int:
    if args.modality != 3:
        print("ERRO: estimate só existe para a modalidade 3 (Higgsfield)")
        return 1
    spec = _carrega(args.spec)
    print(json.dumps(higgsfield.estimate(spec), ensure_ascii=False, indent=2))
    return 0


def _cmd_templates(args) -> int:
    for p in sorted(schema.TEMPLATES_DIR.glob("*.json")):
        t = json.loads(p.read_text(encoding="utf-8"))
        print(f"{t['template_id']:32} regime={t['regime']:11} pessoa={str(t['has_person']):5} — {t['description'][:60]}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="imagegem", description=__doc__.strip().splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("validate", help="valida um spec")
    p.add_argument("spec")

    p = sub.add_parser("render", help="renderiza um spec numa das quatro modalidades")
    p.add_argument("spec")
    p.add_argument("--modality", type=int, default=1, choices=[1, 2, 3, 4])

    p = sub.add_parser("resolve", help="resolve template + respostas em spec")
    p.add_argument("template", help="id do template ou caminho .json")
    p.add_argument("--answers", help="caminho de arquivo .json com respostas; usa example_answers se omitido")
    p.add_argument("--out", help="grava spec no caminho em vez de imprimir")

    p = sub.add_parser("submit", help="chama o cliente da modalidade (3 ou 4)")
    p.add_argument("spec")
    p.add_argument("--modality", type=int, required=True, choices=[3, 4])
    p.add_argument("--thoughts", action="store_true", help="modalidade 4: include_thoughts para diagnóstico")

    p = sub.add_parser("estimate", help="custo de uma chamada Higgsfield sem consumir créditos")
    p.add_argument("spec")
    p.add_argument("--modality", type=int, default=3, choices=[3])

    p = sub.add_parser("templates", help="lista todos os templates disponíveis")

    args = parser.parse_args(argv)
    return {
        "validate": _cmd_validate,
        "render":   _cmd_render,
        "resolve":  _cmd_resolve,
        "submit":   _cmd_submit,
        "estimate": _cmd_estimate,
        "templates": _cmd_templates,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
