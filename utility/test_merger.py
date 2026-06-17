# testar merger.py

import pandas as pd
import sys
from pathlib import Path
# Adiciona o diretório src (que está fora de utility) ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from ingestion.merger import detectar_join, executar_merge

# Carregar os dados das planilhas
print("Carregando dados de vendas e marketing...")
base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"
if not data_dir.exists():
    data_dir = Path.cwd() / "data"

df_vendas = pd.read_excel(data_dir / "vendas.xlsx")
df_marketing = pd.read_excel(data_dir / "marketing.xlsx")

# Print dos shapes para verificar se os dados foram carregados corretamente
print(f"   vendas:    {df_vendas.shape}")     # (1200, 18)
print(f"   marketing: {df_marketing.shape}")  # (330, 14)

# Detectar a configuração de merge usando a LLM
config = detectar_join(df_vendas, df_marketing)

print("\nExecutar Merge...")
df_merged = executar_merge(df_vendas, df_marketing, config)


#Inspensão de resultados
print(f"\n Dataset final: {df_merged.shape}")
print(f"\nColunas disponíveis:")
for col in df_merged.columns:
    print(f"  {col}")

print(f"\nPrimeiras 2 linhas (colunas principais):")
cols_ver = ["produto", "mes_referencia", "receita_total",
            "custo_total_brl", "orcamento_marketing"]
print(df_merged[cols_ver].head(2).to_string())

#Verifica se vendas sem campanha ficaram com 0
sem_campanha = df_merged[df_merged["orcamento_marketing"] == 0]
print(f"\nVendas sem campanha no mês: {len(sem_campanha)} linhas")
print("(essas ficam com orcamento_marketing = 0, não NaN)")

# Salva para as próximas etapas usarem
df_merged.to_parquet(data_dir / "merged.parquet", index=False)
print("\n✅ Salvo em data/merged.parquet")