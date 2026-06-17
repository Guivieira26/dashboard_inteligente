# Treinar modelo de regressão para prever receita com base em marketing e preço

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor # modelo de regressão avançado
from sklearn.preprocessing import LabelEncoder # para transformar categorias em números
from sklearn.model_selection import train_test_split # para dividir banco em treino e teste
from sklearn.metrics import mean_absolute_percentage_error # métrica de erro percentual
import joblib # para salvar o modelo treinado em disco

# ── Estado global do modelo ───────────────────────────────────────────────────
# Ficam em memória depois do treino — o dashboard acessa sem re-treinar
_modelo:          GradientBoostingRegressor | None = None
_encoder_produto: LabelEncoder | None              = None
_media_por_produto: dict                           = {}

# Assume the project root is duas pastas acima de `src/ml` (dashboard_inteligente/)
# Ex: /.../dashboard_inteligente/src/ml/predictor.py -> root = parents[2]
base_dir = Path(__file__).resolve().parents[2]
data_dir = base_dir / "data"
# Assegura que `data/` na raiz do projeto exista — é o local canônico dos artefatos
data_dir.mkdir(parents=True, exist_ok=True)

def salvar_modelo(path: str | Path = data_dir / "modelo.joblib") -> None:
    """Persiste o modelo e o encoder em disco.

    Garante que o diretório exista antes de gravar para evitar
    FileNotFoundError quando o script for executado de outra pasta.
    """
    if _modelo is None:
        raise RuntimeError("Treine o modelo antes de salvar.")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "modelo":            _modelo,
        "encoder_produto":   _encoder_produto,
        "media_por_produto": _media_por_produto,
    }, path)
    print(f"Modelo salvo em {path}")


def carregar_modelo(path: str = data_dir / "modelo.joblib") -> None:
    """Carrega modelo do disco para a memória global."""
    global _modelo, _encoder_produto, _media_por_produto
    dados = joblib.load(path)
    _modelo            = dados["modelo"]
    _encoder_produto   = dados["encoder_produto"]
    _media_por_produto = dados["media_por_produto"]
    print(f"Modelo carregado de {path}")


def treinar(df: pd.DataFrame) -> dict:
    """
    Treina o modelo com o histórico completo do merged.parquet.
    Retorna as métricas de avaliação para você saber se o modelo é confiável.
    """
    global _modelo, _encoder_produto, _media_por_produto

    df = df.copy()

    # ── Feature engineering ───────────────────────────────────────────────────
    # Extrai o número do mês da data — o modelo não entende strings de data (Janeiro - 0 fevereiro - 2....)
    df["mes_num"] = pd.to_datetime(df["data_venda"]).dt.month

    # LabelEncoder: converte strings em inteiros
    # "Headset USB" → 0, "Hub USB-C" → 1, "Monitor 24 Pol" → 2 ...
    # O modelo só trabalha com números — não entende texto
    enc = LabelEncoder()
    df["produto_enc"] = enc.fit_transform(df["produto"])
    _encoder_produto = enc   # salva para usar na simulação depois

    # Guarda médias por produto para usar como base da simulação
    # (quantidade média, desconto médio — o usuário não vai mexer nesses)
    _media_por_produto = (
        df.groupby("produto")
        .agg(
            qtd_media      = ("quantidade",        "mean"),
            desconto_medio = ("desconto_aplicado", "mean"),
        )
        .to_dict(orient="index")
    )

    # ── Define features e target ──────────────────────────────────────────────
    features = [
        "dolar_na_compra",
        "orcamento_marketing",
        "mes_num",
        "produto_enc",
        "quantidade",
        "desconto_aplicado",
    ]

    X = df[features].fillna(0) # Features: o que o modelo vai usar para aprender a prever
    y = df["receita_total"] # Nosso target é a receita total da venda — o que queremos prever

    # ── Divide o banco em treino e teste ──────────────────────────────────────────────
    # test_size=0.2 → 80% para treinar, 20% para avaliar
    # random_state fixo → mesma divisão toda vez (reprodutibilidade)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── Treina o modelo ───────────────────────────────────────────────────────
    modelo = GradientBoostingRegressor(
        n_estimators=200,    # número de árvores na sequência
        learning_rate=0.08,  # tamanho do passo de correção a cada árvore
                             # menor = aprende mais devagar mas generaliza melhor
        max_depth=4,         # profundidade máxima de cada árvore - Permite que o modelo cruze até 4 features para aprender padrões
                             # profundo demais → decora os dados (overfitting)
        random_state=42,
    )
    modelo.fit(X_train, y_train)
    _modelo = modelo

    # ── Avalia no conjunto de teste (dados que o modelo nunca viu) ────────────
    y_pred = modelo.predict(X_test)
    mape   = mean_absolute_percentage_error(y_test, y_pred)
    # MAPE = Mean Absolute Percentage Error
    # Se MAPE = 0.15 → o modelo erra em média 15% para cima ou para baixo
    # Para dados financeiros com ruído, abaixo de 25% é aceitável

    print(f"   Amostras treino: {len(X_train)}")
    print(f"   Amostras teste:  {len(X_test)}")
    print(f"   MAPE:            {mape*100:.1f}%")

    return {"mape": round(mape * 100, 2), "n_treino": len(X_train)}

def simular(
    df_base:             pd.DataFrame,
    dolar_simulado:      float,
    variacao_mkt_pct:    float,
) -> pd.DataFrame:
    """
    Dado um cenário hipotético, projeta receita e custo por produto
    para os próximos 30 dias.

    Parâmetros:
        dolar_simulado   — ex: 6.20
        variacao_mkt_pct — ex: 0.20 para +20%, -0.10 para -10%

    Retorna DataFrame com uma linha por produto contendo:
        receita_projetada, custo_projetado, margem_projetada,
        receita_atual (baseline), variacao_pct
    """
    if _modelo is None:
        raise RuntimeError("Modelo não treinado. Execute treinar() antes.")

    df_base  = df_base.copy()
    df_base["data_dt"] = pd.to_datetime(df_base["data_venda"])

    # Pega o último mês do histórico como referência
    ultimo_mes  = df_base["data_dt"].max().to_period("M")
    df_ultimo   = df_base[df_base["data_dt"].dt.to_period("M") == ultimo_mes]
    proximo_mes = (df_base["data_dt"].max().month % 12) + 1

    resultados = []

    for produto in df_base["produto"].unique():

        df_prod    = df_ultimo[df_ultimo["produto"] == produto]
        medias     = _media_por_produto.get(produto, {})

        # Custo futuro: aplica o novo dólar + impostos de importação
        custo_usd        = df_base[df_base["produto"] == produto]["custo_produto_usd"].mean()
        custo_brl_unit   = custo_usd * dolar_simulado * 1.60  # 60% de imposto

        # Marketing futuro: pega a média do último mês e aplica a variação
        mkt_historico = (
            df_base[df_base["produto"] == produto]["orcamento_marketing"]
            .replace(0, float("nan"))   # exclui meses sem campanha da média
            .mean()
        )
        # Se o produto nunca teve campanha, usa 5% da receita média como base
        if pd.isna(mkt_historico):
            mkt_historico = df_base[df_base["produto"] == produto]["receita_total"].mean() * 0.05

        mkt_futuro = mkt_historico * (1 + variacao_mkt_pct)

        # Produto codificado para o modelo
        if produto in list(_encoder_produto.classes_): # Tipo mouse - 1 Monitor - 2 ... se existir assimila se nao padrao 0
            produto_enc = list(_encoder_produto.classes_).index(produto)
        else:
            produto_enc = 0

        # Monta as features do cenário simulado
        # Usamos médias históricas para quantidade e desconto
        # (o usuário só controla dólar e marketing)
        X_sim = pd.DataFrame([{
            "dolar_na_compra":     dolar_simulado,
            "orcamento_marketing": mkt_futuro,
            "mes_num":             proximo_mes,
            "produto_enc":         produto_enc,
            "quantidade":          medias.get("qtd_media", 2),
            "desconto_aplicado":   medias.get("desconto_medio", 0.05),
        }])

        # Previsão de receita por transação gerada pelo modelo
        receita_transacao = float(_modelo.predict(X_sim)[0])

        # Escala para o mês: multiplica pela quantidade de transações
        # do último mês (assumimos mesma frequência de vendas)
        n_transacoes     = len(df_prod) if len(df_prod) > 0 else 10
        receita_proj     = receita_transacao * n_transacoes
        custo_proj       = custo_brl_unit * medias.get("qtd_media", 2) * n_transacoes
        margem_proj      = receita_proj - custo_proj - mkt_futuro

        # Receita atual do último mês (baseline de comparação)
        receita_atual    = df_prod["receita_total"].sum()
        variacao_pct     = ((receita_proj / (receita_atual + 1)) - 1) * 100

        resultados.append({
            "produto":             produto,
            "receita_atual":       round(receita_atual, 2),
            "receita_projetada":   round(receita_proj, 2),
            "custo_projetado":     round(custo_proj, 2),
            "marketing_futuro":    round(mkt_futuro, 2),
            "margem_projetada":    round(margem_proj, 2),
            "variacao_receita_pct": round(variacao_pct, 1),
            "alerta":              margem_proj < 0,
        })

    return (
        pd.DataFrame(resultados)
        .sort_values("margem_projetada", ascending=True)
        .reset_index(drop=True)
    )