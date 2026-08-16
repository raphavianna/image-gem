"""Clientes de execução: Gemini (modalidade 4) e Higgsfield (modalidade 3).

Ambos suportam **modo simulação** quando as credenciais não estão no ambiente:
imprimem o payload que seriam a chamar e devolvem resultado sintético. Isso
faz a CLI e a Skill executarem de ponta a ponta sem gastar créditos, o que é o
gate condicional do prompt-mestre.
"""

from imagegem.clients import gemini, higgsfield  # noqa: F401
