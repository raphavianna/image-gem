"""Servidor MCP expõe geração e edição como ferramentas.

Uso:
    python -m mcp_server.server   # via stdio, para clientes MCP

Duas ferramentas:
    generate_image(template, answers, modality)
    edit_image(source_url, edit_replace, edit_light_reconciliation, edit_integration, modality)

Ambas passam pela política de conteúdo antes de resolver ou chamar cliente,
e registram em runs/ ao final.
"""
