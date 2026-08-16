"""imagegem — geração de prompts hiper-realistas para Nano Banana Pro.

O pacote consolida o pipeline: schema canônico, resolver de templates,
renderizadores das quatro modalidades, checagem de regras/checklist, política
de conteúdo, clientes Gemini/Higgsfield, e registro de execuções.

Cada módulo é chamado em ordem no fluxo típico:

    schema.load()  →  resolver.resolve(template, answers)  →  spec
    check.validate(spec)                                    →  falhas
    render.renderiza_modalidade_N(spec)                    →  envelope
    clients.gemini/higgsfield.submit(envelope)             →  imagem
    runs.register(...)                                      →  registro
"""

from imagegem import check, policy, render, resolver, runs, schema  # noqa: F401

__version__ = "0.1.0"

__all__ = ["check", "policy", "render", "resolver", "runs", "schema", "__version__"]
