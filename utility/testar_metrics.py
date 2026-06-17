# testar metrics.py

from pathlib import Path
import sys
# Adiciona o diretório src (que está fora de utility) ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from analytics.metrics import calcular_margem_por_produto, calcular_eficiencia_canal
import pandas as pd


base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"
if not data_dir.exists():
    data_dir = Path.cwd() / "data"
    
print("📥 Carregando dataset merged...")
df = pd.read_parquet(data_dir / "merged.parquet")
print(f"   {df.shape[0]} linhas × {df.shape[1]} colunas\n")

# ── Métrica X ────────────────────────────────────────────────────────────────
print("=" * 60)
print("MÉTRICA X — Margem líquida por produto")
print("=" * 60)

df_margem = calcular_margem_por_produto(df)

# Formata valores monetários para leitura humana
for _, linha in df_margem.iterrows():
    sinal = "✅" if linha["margem_liquida"] > 0 else "🔴"
    print(
        f"{sinal} {linha['produto']:<22} "
        f"Receita: R${linha['receita_total']:>10,.0f}  "
        f"Margem: R${linha['margem_liquida']:>10,.0f}  "
        f"({linha['margem_pct_media']:+.1f}%)"
    )

# ── Métrica Y ────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("MÉTRICA Y — Eficiência por canal")
print("=" * 60)

df_canais = calcular_eficiencia_canal(df)

for _, linha in df_canais.iterrows():
    print(
        f"#{int(_)+1} {linha['canal_origem']:<20} "
        f"ROAS: {linha['roas']:>6.1f}x  "
        f"NPS: {linha['satisfacao_media']:.2f}/5  "
        f"Score: {linha['score_eficiencia']:.3f}  "
        f"Vendas: {linha['total_vendas']}"
    )

# ── Insight rápido ────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("INSIGHTS AUTOMÁTICOS")
print("=" * 60)

# Produto com maior margem
melhor = df_margem.iloc[0]
print(f"💰 Melhor margem:   {melhor['produto']} "
      f"(R$ {melhor['margem_liquida']:,.0f})")

# Produto em risco
em_risco = df_margem[df_margem["margem_liquida"] < 0]
if not em_risco.empty:
    for _, p in em_risco.iterrows():
        print(f"⚠️  Margem negativa: {p['produto']} "
              f"(R$ {p['margem_liquida']:,.0f})")

# Melhor canal
melhor_canal = df_canais.iloc[0]
print(f"📣 Canal mais eficiente: {melhor_canal['canal_origem']} "
      f"(ROAS {melhor_canal['roas']:.1f}x, "
      f"NPS {melhor_canal['satisfacao_media']:.2f})")

# Salva os resultados para o dashboard usar
df_margem.to_parquet(data_dir / "margem.parquet",  index=False)
df_canais.to_parquet(data_dir / "canais.parquet",  index=False)
print("\n✅ Salvos: data/margem.parquet e data/canais.parquet")