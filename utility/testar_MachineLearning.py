# testar_ml.py — python3 testar_MachineLearning.py

import sys
from pathlib import Path
sys.path.insert(0, "src")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import pandas as pd
from ml.predictor import treinar, simular, salvar_modelo

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"
if not data_dir.exists():
    data_dir = Path.cwd() / "data"

print("📥 Carregando dados...")
df = pd.read_parquet(data_dir / "merged.parquet")

print("\n🧠 Treinando modelo...")
metricas = treinar(df)
salvar_modelo()
# print(f"   MAPE: {metricas['mape']}%")

# ── Cenário 1: dólar alto, mais marketing ────────────────────────────────────
print("\n" + "=" * 60)
print("CENÁRIO 1 — Dólar R$ 6.20 | Marketing +20%")
print("=" * 60)
df_c1 = simular(df, dolar_simulado=6.20, variacao_mkt_pct=0.20)

for _, row in df_c1.iterrows():
    icone = "🔴" if row["alerta"] else "✅"
    print(
        f"{icone} {row['produto']:<22} "
        f"Receita atual: R${row['receita_atual']:>8,.0f}  "
        f"Projetada: R${row['receita_projetada']:>8,.0f}  "
        f"Margem: R${row['margem_projetada']:>8,.0f}  "
        f"({row['variacao_receita_pct']:+.1f}%)"
    )

# ── Cenário 2: dólar baixo, menos marketing ──────────────────────────────────
print("\n" + "=" * 60)
print("CENÁRIO 2 — Dólar R$ 5.20 | Marketing -10%")
print("=" * 60)
df_c2 = simular(df, dolar_simulado=5.20, variacao_mkt_pct=-0.10)

for _, row in df_c2.iterrows():
    icone = "🔴" if row["alerta"] else "✅"
    print(
        f"{icone} {row['produto']:<22} "
        f"Margem projetada: R${row['margem_projetada']:>8,.0f}  "
        f"({row['variacao_receita_pct']:+.1f}%)"
    )

# ── Comparação direta dos dois cenários ─────────────────────────────────────
print("\n" + "=" * 60)
print("IMPACTO DO DÓLAR — produto mais sensível")
print("=" * 60)
df_comp = df_c1[["produto","margem_projetada"]].merge(
    df_c2[["produto","margem_projetada"]],
    on="produto", suffixes=("_dolar_alto","_dolar_baixo")
)
df_comp["diferenca"] = df_comp["margem_projetada_dolar_baixo"] - df_comp["margem_projetada_dolar_alto"]
df_comp = df_comp.sort_values("diferenca", ascending=False)

for _, row in df_comp.iterrows():
    print(
        f"  {row['produto']:<22} "
        f"ganho com dólar baixo: R${row['diferenca']:>8,.0f}"
    )