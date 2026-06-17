# First version front-end: 2024-06-05
# src/dashboard/app.py
#
# Execute com: streamlit run src/dashboard/app.py
# (sempre da raiz do projeto, não de dentro de src/)

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Inteligente — Importadora Tech",
    page_icon="📊",
    layout="wide",           # ocupa a largura toda do browser
)

# ── Carregamento de dados e modelo ───────────────────────────────────────────
# @st.cache_data: executa só uma vez e cacheia o resultado
# Sem isso, cada interação do usuário re-leria os parquets do disco
@st.cache_data
def carregar_dados():
    base = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    return {
        "merged":   pd.read_parquet(os.path.join(base, "merged.parquet")),
        "margem":   pd.read_parquet(os.path.join(base, "margem.parquet")),
        "canais":   pd.read_parquet(os.path.join(base, "canais.parquet")),
    }

# O modelo não pode ser cacheado com @st.cache_data (não é serializável)
# @st.cache_resource cacheia objetos que ficam em memória entre sessões
@st.cache_resource
def carregar_modelo():
    from ml.predictor import carregar_modelo as _load
    _load()
    # Importa as funções após carregar — o estado global já está preenchido
    from ml.predictor import simular
    return simular

try:
    dados   = carregar_dados()
    simular = carregar_modelo()
except FileNotFoundError as e:
    st.error(f"⚠️ Arquivo não encontrado: {e}")
    st.info("Execute os scripts de preparação antes do dashboard:\n" # ALERTA: toda operação deve ser feita pelo front sem necessidade de 
            "1. python3 gerar_dados.py\n"                            # rodar scripts isso devera ser ajustado depois    
            "2. python3 testar_merger.py\n"
            "3. python3 testar_metrics.py\n"
            "4. python3 testar_ml.py")
    st.stop()

df        = dados["merged"]
df_margem = dados["margem"]
df_canais = dados["canais"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Painel de Controle")
    st.caption("Ajuste os parâmetros e clique em Simular")

    st.divider()
    st.subheader("🔮 Simulador de Cenário")

    dolar_sim = st.slider(
        "💵 Cotação do Dólar (R$)",
        min_value=5.00,
        max_value=7.00,
        value=5.80,          # valor padrão = média histórica dos dados
        step=0.05,
        format="R$ %.2f",
    )

    mkt_delta = st.slider(
        "📣 Variação no Marketing",
        min_value=-30,
        max_value=80,
        value=0,
        step=5,
        format="%d%%",
    )

    simular_btn = st.button(
        "▶ Simular Cenário",
        type="primary",
        use_container_width=True,
    )

    st.divider()
    st.caption(
        f"📅 Período: {df['data_venda'].min()} → {df['data_venda'].max()}\n\n"
        f"📦 {len(df):,} transações · {df['produto'].nunique()} produtos"
    )
    
# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.title("📊 Dashboard Inteligente — Importadora Tech BR")
st.caption("Visão executiva de operações · Histórico + Simulação de Cenários")
st.divider()

# ── KPIs de topo ──────────────────────────────────────────────────────────────
# Calcula os totais reais (sem fan-out) agrupando por produto+mês primeiro
por_mes = (
    df.groupby(["produto", "mes_referencia"])
    .agg(
        receita   = ("receita_total",       "sum"),
        custo     = ("custo_total_brl",     "sum"),
        marketing = ("orcamento_marketing", "first"),
    )
    .reset_index()
)
por_mes["margem"] = por_mes["receita"] - por_mes["custo"] - por_mes["marketing"]

receita_total  = por_mes["receita"].sum()
custo_total    = por_mes["custo"].sum()
mkt_total      = por_mes["marketing"].sum()
margem_total   = por_mes["margem"].sum()
nps_medio      = df["satisfacao_cliente"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Receita Total",     f"R$ {receita_total:,.0f}")
c2.metric("📦 Custo Importação",  f"R$ {custo_total:,.0f}")
c3.metric("📣 Inv. Marketing",    f"R$ {mkt_total:,.0f}")
c4.metric(
    "📈 Margem Líquida",
    f"R$ {margem_total:,.0f}",
    delta=f"{margem_total/receita_total*100:.1f}%",
)
c5.metric("⭐ Satisfação Média",  f"{nps_medio:.2f} / 5")

st.divider()

# ── Parte 1: Histórico ────────────────────────────────────────────────────────
st.subheader("📊 Visão do Agora — Histórico")

col_esq, col_dir = st.columns(2)

with col_esq:
    st.markdown("**Métrica X — Margem Líquida por Produto**")

    # Cria coluna de cor: verde se positivo, vermelho se negativo
    df_margem["cor"] = df_margem["margem_liquida"].apply(
        lambda x: "Positiva" if x >= 0 else "Negativa"
    )

    fig_x = px.bar(
        df_margem,
        x="produto",
        y="margem_liquida",
        color="cor",
        color_discrete_map={"Positiva": "#2ecc71", "Negativa": "#e74c3c"},
        labels={"margem_liquida": "Margem Líquida (R$)", "produto": ""},
        text_auto=".2s",
    )
    fig_x.update_layout(
        showlegend=False,
        height=360,
        xaxis_tickangle=-30,
    )
    st.plotly_chart(fig_x, use_container_width=True)

with col_dir:
    st.markdown("**Métrica Y — Eficiência por Canal**")

    fig_y = px.bar(
        df_canais,
        x="canal_origem",
        y="score_eficiencia",
        color="satisfacao_media",
        color_continuous_scale="Blues",
        labels={
            "score_eficiencia": "Score de Eficiência",
            "canal_origem":     "",
            "satisfacao_media": "Satisfação",
        },
        text_auto=".2f",
    )
    fig_y.update_layout(height=360, xaxis_tickangle=-30)
    st.plotly_chart(fig_y, use_container_width=True)

# ── Linha do tempo ────────────────────────────────────────────────────────────
st.markdown("**Evolução Mensal — Receita vs Custo vs Margem**")

df_mensal = (
    por_mes
    .groupby("mes_referencia")
    .agg(receita=("receita","sum"), custo=("custo","sum"), margem=("margem","sum"))
    .reset_index()
    .sort_values("mes_referencia")
)

fig_linha = go.Figure()
fig_linha.add_trace(go.Scatter(
    x=df_mensal["mes_referencia"], y=df_mensal["receita"],
    name="Receita", mode="lines+markers",
    line=dict(color="#2ecc71", width=2),
))
fig_linha.add_trace(go.Scatter(
    x=df_mensal["mes_referencia"], y=df_mensal["custo"],
    name="Custo", mode="lines+markers",
    line=dict(color="#e74c3c", width=2),
))
fig_linha.add_trace(go.Scatter(
    x=df_mensal["mes_referencia"], y=df_mensal["margem"],
    name="Margem Líquida", mode="lines+markers",
    line=dict(color="#3498db", width=2, dash="dot"),
))
fig_linha.update_layout(height=300, legend=dict(orientation="h"))
st.plotly_chart(fig_linha, use_container_width=True)

# ── Parte 2: Simulação ────────────────────────────────────────────────────────
st.divider()
st.subheader("🔮 Visão do Futuro — Simulador de Cenários")

if simular_btn:
    with st.spinner("Calculando projeção com ML..."):
        df_proj = simular(
            df,
            dolar_simulado   = dolar_sim,
            variacao_mkt_pct = mkt_delta / 100,
        )

    # Gráfico de comparação: receita atual vs projetada
    col_graf, col_tab = st.columns([3, 2])

    with col_graf:
        fig_proj = px.bar(
            df_proj,
            x="produto",
            y=["receita_atual", "receita_projetada"],
            barmode="group",
            color_discrete_map={
                "receita_atual":     "#95a5a6",
                "receita_projetada": "#3498db",
            },
            labels={"value": "Receita (R$)", "variable": "Período", "produto": ""},
            title=f"Receita Atual vs Projetada · Dólar R${dolar_sim:.2f} · Marketing {mkt_delta:+d}%",
        )
        # Anota produtos em alerta
        for _, row in df_proj[df_proj["alerta"]].iterrows():
            fig_proj.add_annotation(
                x=row["produto"],
                y=row["receita_projetada"],
                text="⚠️",
                showarrow=False,
                yshift=12,
                font=dict(size=16),
            )
        fig_proj.update_layout(height=380, xaxis_tickangle=-30)
        st.plotly_chart(fig_proj, use_container_width=True)

    with col_tab:
        st.markdown("**Projeção detalhada**")
        df_exibir = df_proj[[
            "produto", "margem_projetada", "variacao_receita_pct", "alerta"
        ]].copy()
        df_exibir.columns = ["Produto", "Margem Proj. (R$)", "Δ Receita %", "Alerta"]
        df_exibir["Alerta"] = df_exibir["Alerta"].map({True: "🔴", False: "✅"})
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)

    # Conselho da LLM
    st.markdown("**🤖 Conselho do Assistente IA**")
    with st.spinner("Gerando análise com Ollama... (10-30 segundos)"):
        from llm.advisor import gerar_conselho
        conselho = gerar_conselho(df_proj, dolar_sim, mkt_delta / 100)

    st.info(conselho)

else:
    st.info("👈 Ajuste os sliders no painel lateral e clique em **▶ Simular Cenário** para ver a projeção.")