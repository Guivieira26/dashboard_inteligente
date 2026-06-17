# Calcular as duas métricas de negócio principais a partir do dataset merged gerado.

import pandas as pd

def calcular_margem_por_produto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Métrica X — Margem líquida por produto.

    Lógica de negócio:
        margem_bruta   = receita - custo de importação
        margem_líquida = margem_bruta - investimento em marketing

    Por que separar bruta de líquida?
    Porque a margem bruta mostra o potencial do produto.
    A líquida mostra o que sobrou depois de pagar para vender.
    Um produto com margem bruta boa mas líquida ruim
    significa que o marketing está comendo o lucro.
    """
    df = df.copy()
    
    por_mes = (
        df
        .groupby(["produto", "mes_referencia"], as_index=False)
        .agg(
            receita_mes    = ("receita_total",       "sum"),
            custo_mes      = ("custo_total_brl",     "sum"),
            marketing_mes  = ("orcamento_marketing", "first"),  # ← first, não sum
            qtd_mes        = ("quantidade",          "sum"),
            ticket_mes     = ("preco_unitario",      "mean"),
            dolar_mes      = ("dolar_na_compra",     "mean"),
        )
    )

    # Calcula margem no nível mensal (já com o marketing correto)
    por_mes["margem_bruta_mes"]   = por_mes["receita_mes"] - por_mes["custo_mes"]
    por_mes["margem_liquida_mes"] = por_mes["margem_bruta_mes"] - por_mes["marketing_mes"]
    por_mes["margem_pct_mes"]     = (
        por_mes["margem_liquida_mes"] / (por_mes["receita_mes"] + 1)
    ) * 100
    
    resumo = (
        por_mes
        .groupby("produto", as_index=False)
        .agg(
            receita_total      = ("receita_mes",      "sum"),
            custo_total        = ("custo_mes",    "sum"),
            marketing_gasto    = ("marketing_mes","sum"),
            margem_bruta       = ("margem_bruta_mes",       "sum"),
            margem_liquida     = ("margem_liquida_mes",     "sum"),
            margem_pct_media   = ("margem_pct_mes",         "mean"),
            qtd_vendas         = ("qtd_mes",         "sum"),
            ticket_medio       = ("ticket_mes",     "mean"),
            dolar_medio        = ("dolar_mes",    "mean"),
        )
        .sort_values("margem_liquida", ascending=False)
        .reset_index(drop=True)
    )

    return resumo

def calcular_eficiencia_canal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Métrica Y — Eficiência por canal de marketing.

    Três dimensões avaliadas:
        ROAS  (Return on Ad Spend) — receita gerada por R$1 investido
        NPS   — satisfação média do cliente que veio por esse canal
        Volume — quantas vendas esse canal gerou

    Score composto: 60% ROAS + 40% satisfação (ambos normalizados 0-1)
    O peso maior no ROAS reflete que o objetivo principal é retorno financeiro.
    """
    df = df.copy()
    
    por_mes = (
        df
        .groupby(["canal_origem", "mes_referencia"], as_index=False)
        .agg(
            receita_mes         = ("receita_total",       "sum"),
            marketing_mes       = ("orcamento_marketing", "first"),
            satisfacao_mes      = ("satisfacao_cliente",  "mean"),
            vendas_mes          = ("id_venda",            "count"),
            ticket_mes          = ("preco_unitario",      "mean"),
        )
    )

    resumo = (
        por_mes
        .groupby("canal_origem", as_index=False)
        .agg(
            receita_gerada      = ("receita_mes",     "sum"),
            marketing_investido = ("marketing_mes",   "sum"),
            satisfacao_media    = ("satisfacao_mes",  "mean"),
            total_vendas        = ("vendas_mes",      "sum"),
            ticket_medio        = ("ticket_mes",      "mean"),
        )
    )

    # ROAS: para cada R$1 investido em marketing, quanto voltou em receita
    # Somamos 1 no denominador para canais sem investimento (Orgânico)
    # não gerarem divisão por zero — eles terão ROAS altíssimo, o que é correto
    resumo["roas"] = (
        resumo["receita_gerada"] / (resumo["marketing_investido"] + 1)
    )

    # Normalização Min-Max: transforma cada métrica para escala 0-1
    # Necessário para poder somar ROAS (que pode ser 50x) com satisfação (escala 1-5)
    # sem que o ROAS domine completamente o score
    def normalizar(serie: pd.Series) -> pd.Series:
        minimo = serie.min()
        maximo = serie.max()
        if maximo == minimo:          # evita divisão por zero se todos iguais
            return pd.Series([0.5] * len(serie), index=serie.index)
        return (serie - minimo) / (maximo - minimo)

    resumo["score_eficiencia"] = (
        0.6 * normalizar(resumo["roas"]) +
        0.4 * normalizar(resumo["satisfacao_media"])
    )

    return resumo.sort_values("score_eficiencia", ascending=False).reset_index(drop=True)
