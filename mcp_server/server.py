"""Servidor MCP para o pipeline imagegem.

Expõe as capacidades centrais como ferramentas MCP para qualquer cliente Claude
(Claude Code, Claude Desktop, extensões IDE, etc.):

    generate_image      resolve um template e submete
    edit_image          instancia o template de edição e submete
    render_prompt       resolve + renderiza sem submeter (barato, seguro)
    list_templates      metadata dos 8 templates
    validate_spec       roda o checklist sobre um spec JSON cru
    check_content_policy verifica se um pedido em linguagem natural passa

Todas as ferramentas aplicam a política de conteúdo antes de qualquer chamada
externa. Sem credenciais, os submits caem em modo simulação (é o gate
condicional do prompt-mestre).
"""

from __future__ import annotations

import json
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types as mcp_types
except ImportError as e:  # pragma: no cover — dependência opcional
    raise SystemExit(
        "mcp não está instalado. Rode: pip install 'imagegem[mcp]'"
    ) from e

from imagegem import check, policy, render, resolver, runs, schema
from imagegem.clients import gemini, higgsfield


server: Server = Server("imagegem")


@server.list_tools()
async def _list_tools() -> list[mcp_types.Tool]:
    return [
        mcp_types.Tool(
            name="list_templates",
            description="Lista os 8 templates disponíveis com id, regime e descrição.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        ),
        mcp_types.Tool(
            name="render_prompt",
            description=(
                "Resolve um template com respostas e devolve o prompt renderizado na "
                "modalidade escolhida. Não submete — barato, seguro, ideal para preview."
            ),
            inputSchema={
                "type": "object",
                "additionalProperties": False,
                "required": ["template", "answers"],
                "properties": {
                    "template": {"type": "string"},
                    "answers": {"type": "object"},
                    "modality": {"type": "integer", "enum": [1, 2, 3, 4], "default": 1},
                },
            },
        ),
        mcp_types.Tool(
            name="generate_image",
            description=(
                "Resolve um template, valida, e submete pelo cliente da modalidade 3 "
                "(Higgsfield) ou 4 (Gemini). Sem credenciais no ambiente, cai em "
                "modo simulação — devolve o payload sem chamar a rede."
            ),
            inputSchema={
                "type": "object",
                "additionalProperties": False,
                "required": ["template", "answers", "modality"],
                "properties": {
                    "template": {"type": "string"},
                    "answers": {"type": "object"},
                    "modality": {"type": "integer", "enum": [3, 4]},
                    "include_thoughts": {"type": "boolean", "default": False},
                },
            },
        ),
        mcp_types.Tool(
            name="validate_spec",
            description="Roda schema + regras de coerência + checklist sobre um spec JSON cru.",
            inputSchema={
                "type": "object",
                "additionalProperties": False,
                "required": ["spec"],
                "properties": {"spec": {"type": "object"}},
            },
        ),
        mcp_types.Tool(
            name="check_content_policy",
            description="Verifica se um pedido em linguagem natural passa na política de conteúdo do sistema.",
            inputSchema={
                "type": "object",
                "additionalProperties": False,
                "required": ["request"],
                "properties": {
                    "request": {"type": "string"},
                    "has_user_reference": {"type": "boolean", "default": False},
                },
            },
        ),
    ]


def _text(obj: Any) -> list[mcp_types.TextContent]:
    """Serializa qualquer resultado em uma única TextContent JSON."""
    return [mcp_types.TextContent(type="text", text=json.dumps(obj, ensure_ascii=False, indent=2, default=str))]


@server.call_tool()
async def _call_tool(name: str, arguments: dict) -> list[mcp_types.TextContent]:
    if name == "list_templates":
        out = []
        for p in sorted(schema.TEMPLATES_DIR.glob("*.json")):
            t = json.loads(p.read_text(encoding="utf-8"))
            out.append({
                "id": t["template_id"],
                "regime": t["regime"],
                "has_person": t["has_person"],
                "description": t["description"],
                "ask_before": [a["field"] for a in t.get("ask_before", [])],
            })
        return _text(out)

    if name == "check_content_policy":
        veredito = policy.check_pedido(arguments["request"], arguments.get("has_user_reference", False))
        return _text({"permitido": veredito.permitido, "razao": veredito.razao})

    if name == "validate_spec":
        falhas, corpo, cauda = check.validate(arguments["spec"])
        return _text({
            "aprovado": not falhas,
            "falhas": falhas,
            "corpo_palavras": len(corpo.split()) if corpo else 0,
        })

    # A partir daqui os comandos usam template + answers e passam pela política.
    template = schema.load_template(arguments["template"])
    answers = arguments["answers"]
    pedido = answers.get("meta.user_request", "")
    tem_ref = bool(answers.get("character.references_urls"))
    veredito = policy.check_pedido(pedido, tem_referencia=tem_ref)
    if not veredito:
        return _text({"erro": "content_policy", "razao": veredito.razao})

    try:
        spec = resolver.resolve(template, answers)
    except ValueError as e:
        return _text({"erro": "ask_before_incompleto", "razao": str(e)})

    if name == "render_prompt":
        mod = arguments.get("modality", 1)
        return _text(render.por_modalidade(spec, mod))

    if name == "generate_image":
        modality = arguments["modality"]
        falhas, corpo, cauda = check.validate(spec)
        if falhas:
            return _text({"erro": "checklist_reprovado", "falhas": falhas})

        if modality == 3:
            resultado = higgsfield.submit(spec)
            envelope = render.renderiza_modalidade_3(spec)
            resposta = {
                "modo": resultado.modo, "status": resultado.status,
                "request_id": resultado.request_id, "images": resultado.images,
                "error": resultado.error, "correlation_id": resultado.correlation_id,
            }
        else:
            resultado = gemini.submit(spec, include_thoughts=arguments.get("include_thoughts", False))
            envelope = render.renderiza_modalidade_4(spec)
            resposta = {
                "modo": resultado.modo, "num_images": len(resultado.imagens),
                "thoughts_count": len(resultado.thoughts), "error": resultado.error,
            }
        pasta = runs.register(
            spec=spec, envelope=envelope, prompt=f"{corpo}\n\n{cauda}",
            response=resposta,
            client="higgsfield" if modality == 3 else "gemini",
            correlation_id=getattr(resultado, "correlation_id", None),
            error=getattr(resultado, "error", None),
            imagens=(getattr(resultado, "imagens", None) or []) if modality == 4 else None,
        )
        return _text(resposta | {"run": str(pasta)})

    return _text({"erro": "tool_desconhecida", "tool": name})


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
