# src/llm/advisor.py
#
# Responsabilidade: receber o DataFrame de projeção do ML e gerar
# um conselho executivo em linguagem natural via Ollama.

import requests
import pandas as pd

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO     = "llama3.1:latest"


def _formatar_contexto(
    df_proj:         pd.DataFrame,
    dolar:           float,
    variacao_mkt_pct: float,
) -> str:
    """
    Transforma o DataFrame de projeção em texto estruturado
    para o prompt. A LLM lê texto, não DataFrames.
    """
    em_risco    = df_proj[df_proj["alerta"] == True]
    saudaveis   = df_proj[df_proj["alerta"] == False]

    linhas = []
    linhas.append(f"Cenário simulado:")
    linhas.append(f"  - Dólar: R$ {dolar:.2f}")
    linhas.append(f"  - Variação no marketing: {variacao_mkt_pct*100:+.0f}%")
    linhas.append("")

    if not em_risco.empty:
        linhas.append("Produtos com margem NEGATIVA (prejuízo projetado):")
        for _, row in em_risco.iterrows():
            linhas.append(
                f"  - {row['produto']}: "
                f"margem R$ {row['margem_projetada']:,.0f} "
                f"({row['variacao_receita_pct']:+.1f}% vs mês atual)"
            )
    else:
        linhas.append("Nenhum produto em situação de risco neste cenário.")

    linhas.append("")

    if not saudaveis.empty:
        linhas.append("Produtos com margem POSITIVA (oportunidades):")
        for _, row in saudaveis.iterrows():
            linhas.append(
                f"  - {row['produto']}: "
                f"margem R$ {row['margem_projetada']:,.0f} "
                f"({row['variacao_receita_pct']:+.1f}% vs mês atual)"
            )
    else:
        linhas.append("Nenhum produto com margem positiva neste cenário.")

    return "\n".join(linhas)


def gerar_conselho(
    df_proj:          pd.DataFrame,
    dolar:            float,
    variacao_mkt_pct: float,
) -> str:
    """
    Envia o contexto da simulação para o Ollama e retorna
    um parágrafo de conselho executivo pronto para o dashboard.
    """
    contexto = _formatar_contexto(df_proj, dolar, variacao_mkt_pct)

    prompt = f"""Você é um consultor financeiro especializado em importação de tecnologia no Brasil.
Analise os dados abaixo e escreva UM parágrafo executivo em português brasileiro.

{contexto}

Instruções para o parágrafo:
- Máximo 10 frases
- Comece identificando o maior risco
- Cite produtos específicos pelo nome
- Termine com UMA recomendação de ação imediata e concreta
- Use linguagem direta, sem jargão técnico
- NÃO use markdown, bullets ou títulos — apenas texto corrido

Escreva apenas o parágrafo, sem introdução e sem comentários."""

    try:
        resposta = requests.post(
            OLLAMA_URL,
            json={
                "model":  MODELO,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # um pouco mais criativo que nos testes
                                         # mas ainda controlado — não queremos
                                         # que ele invente números
                    "num_predict": 300,  # parágrafo curto — 300 tokens são ~200 palavras
                }
            },
            timeout=120,
        )
        resposta.raise_for_status()
        return resposta.json()["response"].strip()

    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama não está rodando. Execute: ollama serve"
    except requests.exceptions.Timeout:
        return "⚠️ Ollama demorou demais. Tente novamente."