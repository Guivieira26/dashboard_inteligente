# testar_advisor.py — python3 testar_advisor.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import pandas as pd
from ml.predictor import carregar_modelo, treinar, salvar_modelo, simular
from llm.advisor  import gerar_conselho

base_dir = Path(__file__).resolve().parents[1]
data_dir = base_dir / "data"

print("📥 Carregando dados...")
df = pd.read_parquet(data_dir / "merged.parquet")

# Tenta carregar o modelo; se não existir, treina e salva
print("📦 Carregando modelo...")
try:
    carregar_modelo()
    print("   ✅ Modelo carregado com sucesso")
except FileNotFoundError:
    print("   ⚠️  Modelo não encontrado. Treinando novo modelo...")
    treinar(df)
    salvar_modelo()
    print("   ✅ Modelo treinado e salvo com sucesso")
except Exception as e:
    print(f"❌ Erro ao carregar o modelo: {e}")
    sys.exit(1)

# ── Teste com o Cenário 1 (o mais crítico) ───────────────────────────────────
dolar        = 6.20
variacao_mkt = 0.20

print(f"\n🔮 Simulando: Dólar R${dolar} | Marketing {variacao_mkt*100:+.0f}%...")
df_proj = simular(df, dolar_simulado=dolar, variacao_mkt_pct=variacao_mkt)

print("\n📊 Projeção do ML:")
for _, row in df_proj.iterrows():
    icone = "🔴" if row["alerta"] else "✅"
    print(f"  {icone} {row['produto']:<22} margem: R${row['margem_projetada']:>8,.0f}")

print("\n🤖 Gerando conselho com Ollama...")
print("   (pode levar 10-30 segundos dependendo do hardware)\n")

conselho = gerar_conselho(df_proj, dolar, variacao_mkt)

print("=" * 60)
print("CONSELHO EXECUTIVO")
print("=" * 60)
print(conselho)
print("=" * 60)

# ── Teste com Cenário 2 para comparar o tom ──────────────────────────────────
dolar2       = 5.20
variacao_mkt2 = -0.10

print(f"\n🔮 Simulando: Dólar R${dolar2} | Marketing {variacao_mkt2*100:+.0f}%...")
df_proj2 = simular(df, dolar_simulado=dolar2, variacao_mkt_pct=variacao_mkt2)

print("\n🤖 Gerando conselho com Ollama...")
conselho2 = gerar_conselho(df_proj2, dolar2, variacao_mkt2)

print("\n" + "=" * 60)
print("CONSELHO EXECUTIVO — CENÁRIO FAVORÁVEL")
print("=" * 60)
print(conselho2)
print("=" * 60)