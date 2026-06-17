
# TESTAR O METRICS
# import pandas as pd

# df = pd.read_parquet("data/merged.parquet")

# print("=== AMOSTRA DE MARKETING POR PRODUTO/MÊS ===")
# print(df[["produto", "mes_referencia", "receita_total", "orcamento_marketing"]].head(10).to_string())

# print("\n=== SOMA TOTAL DE MARKETING vs RECEITA ===")
# print(f"Receita total:    R$ {df['receita_total'].sum():,.0f}")
# print(f"Marketing total:  R$ {df['orcamento_marketing'].sum():,.0f}")
# print(f"Custo total:      R$ {df['custo_total_brl'].sum():,.0f}")

# print("\n=== MARKETING POR PRODUTO (soma) ===")
# print(df.groupby("produto")["orcamento_marketing"].sum().sort_values(ascending=False).to_string())

# print("\n=== QUANTAS LINHAS POR PRODUTO/MÊS? ===")
# print(df.groupby(["produto", "mes_referencia"]).size().head(20).to_string())




# TESTAR O MERGE

import pandas as pd

# Lê os arquivos originais, antes de qualquer merge
df_v = pd.read_excel("data/vendas.xlsx")
df_m = pd.read_excel("data/marketing.xlsx")

print("=== MARKETING ORIGINAL (antes do merge) ===")
print(f"Total de campanhas: {len(df_m)}")
print(f"Soma do orçamento original: R$ {df_m['orcamento_gasto'].sum():,.0f}")

print("\n=== MARKETING AGREGADO POR PRODUTO+MÊS ===")
agg = df_m.groupby(["produto_alvo", "mes_referencia"])["orcamento_gasto"].sum().reset_index()
print(f"Combinações produto+mês: {len(agg)}")
print(f"Soma após agregar: R$ {agg['orcamento_gasto'].sum():,.0f}")
print(agg.head(10).to_string())

print("\n=== VENDAS: quantas linhas por produto+mês? ===")
df_v["mes_referencia"] = pd.to_datetime(df_v["data_venda"]).dt.to_period("M").astype(str)
contagem = df_v.groupby(["produto", "mes_referencia"]).size().reset_index(name="n_vendas")
print(contagem.head(10).to_string())

print("\n=== SIMULAÇÃO DO MERGE ===")
# Refaz o merge aqui mesmo para ver o resultado
df_mkt_agg = (
    df_m.groupby(["produto_alvo", "mes_referencia"], as_index=False)
    .agg(orcamento_marketing=("orcamento_gasto", "sum"))
)
merged = df_v.merge(
    df_mkt_agg,
    left_on=["produto", "mes_referencia"],
    right_on=["produto_alvo", "mes_referencia"],
    how="left"
)
merged["orcamento_marketing"] = merged["orcamento_marketing"].fillna(0)

print(f"Linhas após merge: {len(merged)}")
print(f"Marketing no merged (sum direto, ERRADO): R$ {merged['orcamento_marketing'].sum():,.0f}")

# Forma correta: pega uma vez por produto+mês
marketing_correto = (
    merged
    .groupby(["produto", "mes_referencia"])["orcamento_marketing"]
    .first()
    .sum()
)
print(f"Marketing correto (first por grupo):      R$ {marketing_correto:,.0f}")
print(f"Receita total:                            R$ {merged['receita_total'].sum():,.0f}")



# Identify error DEBUG

import pandas as pd
import sys
sys.path.insert(0, "src")

df = pd.read_parquet("data/merged.parquet")

# Refaz a agregação por produto+mês como a Métrica X faz
por_mes = (
    df
    .groupby(["produto", "mes_referencia"], as_index=False)
    .agg(
        receita_mes   = ("receita_total",       "sum"),
        custo_mes     = ("custo_total_brl",     "sum"),
        marketing_mes = ("orcamento_marketing", "first"),
    )
)

print("=== MARKETING POR PRODUTO+MÊS (com first) ===")
print(f"Soma do marketing: R$ {por_mes['marketing_mes'].sum():,.0f}")
print(f"Soma da receita:   R$ {por_mes['receita_mes'].sum():,.0f}")
print(f"Soma do custo:     R$ {por_mes['custo_mes'].sum():,.0f}")

por_mes["margem"] = por_mes["receita_mes"] - por_mes["custo_mes"] - por_mes["marketing_mes"]
print(f"Margem total:      R$ {por_mes['margem'].sum():,.0f}")

print("\n=== POR PRODUTO ===")
resumo = por_mes.groupby("produto").agg(
    receita=("receita_mes", "sum"),
    custo=("custo_mes", "sum"),
    marketing=("marketing_mes", "sum"),
).assign(margem=lambda x: x.receita - x.custo - x.marketing)
print(resumo.to_string())


# Correção das metricas na geração de dados

# import pandas as pd

# df_m = pd.read_excel("data/marketing.xlsx")
# df_v = pd.read_excel("data/vendas.xlsx")

# print("=== ESCALA DO PROBLEMA ===")
# print(f"Orçamento médio por campanha: R$ {df_m['orcamento_gasto'].mean():,.0f}")
# print(f"Campanhas por produto+mês em média: {len(df_m) / df_m.groupby(['produto_alvo','mes_referencia']).ngroups:.1f}")

# df_v["mes_referencia"] = pd.to_datetime(df_v["data_venda"]).dt.to_period("M").astype(str)
# receita_mes = df_v.groupby(["produto", "mes_referencia"])["receita_total"].sum().mean()
# print(f"Receita média por produto+mês: R$ {receita_mes:,.0f}")

# mkt_mes = df_m.groupby(["produto_alvo","mes_referencia"])["orcamento_gasto"].sum().mean()
# print(f"Marketing médio por produto+mês: R$ {mkt_mes:,.0f}")
# print(f"\nRazão marketing/receita: {mkt_mes/receita_mes:.1f}x (deveria ser 0.1x a 0.3x)")
