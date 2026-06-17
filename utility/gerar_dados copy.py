# Gerar dados aleatorios para testes demonstrações e treinamento de modelos de ML

from pathlib import Path

import pandas as pd          # manipulação de tabelas
import numpy as np           # arrays e matemática vetorizada
from faker import Faker      # gerador de dados fictícios
import random                # números aleatórios simples
from datetime import datetime, timedelta  # manipulação de datas

# Faker com localização brasileira — gera nomes e textos em pt-BR
fake = Faker('pt_BR')

np.random.seed(42)  # para reprodutibilidade
random.seed(42)

# Lista de produtos que a importadora vende USD - BRL
produtos = [
    {"nome": "Teclado Mecânico",   "custo_usd": 35.0,  "preco_venda": 380.0},
    {"nome": "Mouse Gamer",        "custo_usd": 18.0,  "preco_venda": 210.0},
    {"nome": "Monitor 24 Pol",     "custo_usd": 120.0, "preco_venda": 980.0},
    {"nome": "Headset USB",        "custo_usd": 22.0,  "preco_venda": 260.0},
    {"nome": "Webcam Full HD",     "custo_usd": 28.0,  "preco_venda": 310.0},
    {"nome": "SSD 1TB",            "custo_usd": 45.0,  "preco_venda": 420.0},
    {"nome": "Hub USB-C",          "custo_usd": 12.0,  "preco_venda": 150.0},
    {"nome": "Placa de Vídeo RTX", "custo_usd": 310.0, "preco_venda": 2800.0},
]

canais = ["Instagram", "Google Ads", "Influenciadores", "Email Marketing", "Orgânico"]
regioes = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF"]

# Dólar médio por mês — simula a flutuação real do câmbio
# Chave = número do mês, Valor = cotação média simulada
dolar_historico = {
    6: 5.20, 7: 5.35, 8: 5.40, 9: 5.55, 10: 5.70,
    11: 5.80, 12: 5.90, 1: 6.05, 2: 6.10, 3: 5.95,
    4: 6.00, 5: 6.15
}

# Ponto de início do histórico: junho de 2024
data_inicio = datetime(2024, 6, 1)

vendas = [] # lista para armazenar os registros de vendas

for i in range(1200): # Gerar 1200 dados
    data = data_inicio + timedelta(days=random.randint(0, 364))  # data aleatória dentro de um ano
    produto = random.choice(produtos)  # produto aleatório
    canal = random.choices(canais, weights=[30,25,20,15,10])[0]   # canal de venda aleatório
    dolar = dolar_historico.get(data.month, 5.80) + random.uniform(-0.10, 0.10)  # cotação do dólar com pequena variação
    custo_importacao = produto["custo_usd"] * dolar  # custo em BRL
    imposto = custo_importacao*0.60 # (Imposto de Importação) + IPI + ICMS somam ~60% sobre o custo
    custo_total_unitario = custo_importacao + imposto
    preco = produto["preco_venda"]  * random.uniform(0.95, 1.05)  # preço de venda com variação de até 5%
    desconto = random.choices([0,0.05,0.10,0.15], weights = [50,25,15,10])[0]
    preco_final = preco * (1 - desconto)  # preço final após desconto
    qtd = random.randint(1,5) # quantidade vendida
    satisfacao = random.choices([1,2,3,4,5], weights=[5,10,20,40,25])[0] # satisfação do cliente (1 a 5)
    
    # Montar a planilha de vendas
    vendas.append({
        "id_venda":           f"VND-{10000 + i}",
        "data_venda":         data.strftime("%Y-%m-%d"),
        "produto":            produto["nome"],         # ← nome da coluna aqui
        "categoria":          "Hardware" if produto["custo_usd"] >= 100 else "Periférico",
        "regiao":             random.choice(regioes),
        "canal_origem":       canal,
        "quantidade":         qtd,
        "preco_unitario":     round(preco_final, 2),
        "receita_total":      round(preco_final * qtd, 2),
        "custo_unitario_brl": round(custo_total_unitario, 2),
        "custo_total_brl":    round(custo_total_unitario * qtd, 2),
        "custo_produto_usd":  produto["custo_usd"],
        "dolar_na_compra":    round(dolar, 4),
        "desconto_aplicado":  desconto,
        "satisfacao_cliente": satisfacao,
        "nps_comentario":     fake.sentence(nb_words=8) if satisfacao <= 2 else "",
        "id_cliente":         f"CLI-{random.randint(1000, 9999)}",
        "nome_cliente":       fake.name(),
    })

#Converte em dataframe do pandas
df_vendas = pd.DataFrame(vendas)

#ordena por data
df_vendas = df_vendas.sort_values("data_venda").reset_index(drop=True)

# Gerando planilhar de marketing

marketing = []
campanha_id = 5000

for mes_offsert in range(12):
    data_campanha = data_inicio + timedelta(days=30*mes_offsert)
    
    for canal in canais:
        for produto in produtos:
            if random.random() < 0.65: # 65% de chance de um produto ter campanha
                receita_esperada_mes = produto["preco_venda"] * 8
                orcamento = round(random.uniform(
                    receita_esperada_mes * 0.05,   # mínimo: 5% da receita esperada
                    receita_esperada_mes * 0.20,   # máximo: 20% da receita esperada
                ), 2)
                impressoes  = random.randint(5000, 200000)
                ctr         = round(random.uniform(0.01, 0.08), 4)  # taxa de clique
                cliques     = int(impressoes * ctr)
                conversoes  = int(cliques * random.uniform(0.02, 0.12))

                marketing.append({
                    "id_campanha":    f"MKT-{campanha_id}",
                    "mes_referencia": data_campanha.strftime("%Y-%m"),  # ← formato diferente de data_venda!
                    "produto_alvo":   produto["nome"],              # ← nome diferente de "produto"!
                    "canal":          canal,                        # ← nome diferente de "canal_origem"!
                    "orcamento_gasto": orcamento,
                    "impressoes":     impressoes,
                    "cliques":        cliques,
                    "ctr":            ctr,
                    "conversoes":     conversoes,
                    "custo_por_lead": round(orcamento / max(conversoes, 1), 2),
                    "objetivo":       random.choice(["Awareness", "Conversão", "Retargeting"]),
                    "publico_alvo":   random.choice(["18-24", "25-34", "35-44", "45+"]),
                    "criativo":       random.choice(["Vídeo", "Carrossel", "Banner", "Story"]),
                })
                campanha_id += 1

df_marketing = pd.DataFrame(marketing)

# Salvar os dados em arquivos Excel

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"
if not data_dir.exists():
    data_dir = Path.cwd() / "data"

df_vendas.to_excel(data_dir / "vendas.xlsx", index=False)
df_marketing.to_excel(data_dir / "marketing.xlsx", index=False)

# Prints

print("=" * 55)
print("VENDAS")
print("=" * 55)
print(f"Linhas × Colunas: {df_vendas.shape}")       # shape = (linhas, colunas)
print(f"\nTipos de cada coluna:")
print(df_vendas.dtypes)                             # tipo inferido automaticamente
print(f"\nPrimeiras 3 linhas:")
print(df_vendas.head(3).to_string())
print(f"\nEstatísticas numéricas:")
print(df_vendas[["receita_total", "custo_total_brl", "dolar_na_compra"]].describe())

print("\n" + "=" * 55)
print("MARKETING")
print("=" * 55)
print(f"Linhas × Colunas: {df_marketing.shape}")
print(f"\nPrimeiras 3 linhas:")
print(df_marketing.head(3).to_string())

print("\n✅ Arquivos salvos em data/vendas.xlsx e data/marketing.xlsx")