# 📊 Dashboard Inteligente — Importadora Tech BR

> Projeto de portfólio desenvolvido durante minha jornada de aprendizado em Machine Learning aplicado.  
> Versão **1.0 - BETA**

---

## Sobre o projeto

A ideia foi criar algo com contexto de negócio real: um dashboard para um importador de componentes de tecnologia que precisa tomar decisões com base em dados.

O domínio escolhido foi fictício mas realista: uma empresa que importa produtos em dólar, paga impostos de importação no Brasil (~60% sobre o custo), investe em marketing por canal e precisa entender quais produtos estão dando lucro e o que pode acontecer se o dólar subir mês que vem.

---

## O que o sistema faz hoje

### Parte 1 — Visão do presente (Analytics)

O sistema carrega duas planilhas — uma de vendas e uma de campanhas de marketing — e usa um modelo de linguagem local (Ollama) para descobrir automaticamente como cruzar essas planilhas, mesmo que os nomes das colunas sejam diferentes entre elas.

Depois do cruzamento, calcula duas métricas de negócio:

**Métrica X — Margem líquida por produto**
```
margem_bruta   = receita_total - custo_importação
margem_líquida = margem_bruta - investimento_em_marketing
```

**Métrica Y — Eficiência por canal de marketing**

Combina ROAS (retorno sobre o investimento em marketing) com satisfação média do cliente num score único, mostrando qual canal traz o melhor resultado pelo menor custo.

### Parte 2 — Visão do futuro (Machine Learning + Simulação)

Com o histórico treinado, o usuário pode simular cenários:

- 🎚️ Slider do dólar: de R$ 5,00 a R$ 7,00
- 🎚️ Slider de marketing: de -30% a +80%

O modelo projeta para os próximos 30 dias: receita esperada, custo projetado e margem por produto. Produtos com margem negativa no cenário simulado são sinalizados com alerta.

### Parte 3 — Conselho executivo com IA local

Após a simulação, um agente de IA (Ollama com llama3.1:8b rodando localmente) lê os resultados e escreve um parágrafo de orientação em linguagem natural — citando produtos pelo nome, identificando o maior risco e sugerindo uma ação imediata.

A escolha de rodar o modelo localmente foi intencional: zero custo por token, os dados não saem da máquina e o projeto funciona sem depender de nenhuma API externa.

---

## Stack

| Camada | Tecnologia | Por quê |
|--------|-----------|---------|
| Linguagem | Python 3.10+ | — |
| Dados | Pandas + OpenPyXL | manipulação de tabelas e leitura de Excel |
| Machine Learning | Scikit-learn (GradientBoosting) | regressão para previsão de receita |
| LLM local | Ollama (llama3.1:8b) | cruzamento de planilhas + conselho executivo |
| Dashboard | Streamlit + Plotly | interface interativa sem frontend customizado |
| Ambiente | WSL + venv | desenvolvimento isolado no Linux |

---

## Algoritmo de ML — por que GradientBoosting

O modelo aprende com o histórico de 1.200 vendas a relação entre as variáveis de entrada (cotação do dólar, investimento em marketing, mês, produto, quantidade, desconto) e a receita gerada por transação.

GradientBoosting funciona treinando árvores de decisão em sequência — cada nova árvore aprende com os erros da anterior. É mais robusto que uma única árvore e mais rápido de treinar que uma rede neural para dados tabulares nessa escala.

O modelo atual atingiu **MAPE de 13,2%** no conjunto de teste — ou seja, erra em média 13% para cima ou para baixo nas previsões. Para dados fictícios com ruído alto por design, esse número é aceitável para uma primeira versão.

---

## Problemas conhecidos e limitações da v1.0

**Dados fictícios com margens irrealistas**
Os dados gerados têm produtos com custo de importação superando o preço de venda em alguns meses, o que gera margens negativas frequentes. Num negócio real existe uma margem mínima protegida e descontos respeitam um piso de lucro. Isso será corrigido na próxima versão.

**Preparação manual dos dados**
Atualmente o projeto depende de scripts utilitários que precisam ser rodados em ordem antes do dashboard:

```
1. utility/gerar_dados.py          → gera as planilhas fictícias
2. utility/testar_merger.py        → cruza as planilhas com a LLM
3. utility/testar_metrics.py       → calcula as métricas de negócio
4. utility/testar_MachineLearning.py → treina e salva o modelo
```

Isso será unificado em uma API que o frontend vai chamar automaticamente.

**Sensibilidade do marketing limitada**
Produtos sem campanha de marketing no último mês recebem a média histórica como base para simulação. A correlação entre marketing e receita capturada pelo modelo ainda é fraca para alguns produtos.

---

## Aprendizados reais durante o desenvolvimento

Dois bugs encontrados e corrigidos durante o desenvolvimento que valem registro:

**Fan-out em JOIN**
Ao fazer LEFT JOIN entre vendas e marketing agregado, o valor de `orcamento_marketing` se repetia em cada linha de venda do mês. Somar diretamente inflava o marketing em até 12x a receita total. A correção foi usar `first()` em vez de `sum()` na agregação de marketing, já que o valor mensal já tinha sido consolidado antes do merge.

**Marketing zero no último mês**
Produtos sem campanha no último mês tinham `orcamento_marketing = 0`, fazendo a simulação retornar o mesmo resultado independente do slider de marketing. A correção foi usar a média histórica do produto ignorando os meses zerados, em vez de olhar só o último mês.

Esses bugs não quebraram o código — produziram números errados silenciosamente. Aprender a identificar resultados absurdos e rastrear a causa até a origem foi o aprendizado mais valioso da primeira entrega.

---

## Como rodar localmente

### Pré-requisitos

- Python 3.10+
- WSL (recomendado no Windows)
- Ollama instalado com o modelo `llama3.1:8b`

```bash
# Instala o Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
```

### Setup

```bash
git clone https://github.com/Guivieira26/dashboard_inteligente
cd dashboard_inteligente

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Preparação dos dados e modelo

```bash
# Rode na ordem:
python3 utility/gerar_dados.py
python3 utility/testar_merger.py
python3 utility/testar_metrics.py
python3 utility/testar_MachineLearning.py
```

### Subindo o dashboard

```bash
# Certifique que o Ollama está rodando
ollama serve &

# Sempre da raiz do projeto
streamlit run src/dashboard/app.py
```

Acesse `http://localhost:8501` no browser.

---

## Roadmap — próximas entregas

**v1.1 — Dados e modelo mais realistas**
- Dados fictícios com margem mínima protegida por produto
- Desconto nunca reduz margem abaixo de 10%
- Reajuste automático de preço de venda quando custo supera receita
- Re-treinamento do modelo com os dados corrigidos

**v1.2 — API unificada**
- Backend em FastAPI unificando todos os scripts utilitários
- Pipeline automático: se `modelo.joblib` não existir, treina antes de subir
- Endpoint para aceitar novas planilhas e incorporar ao histórico existente (ex: adicionar o mês atual às planilhas dos últimos 11 meses)

**v2.0 — Frontend customizado**
- Interface React substituindo o Streamlit
- Frontend chama a API diretamente
- Upload de planilhas pela interface
- Terceiro slider: simulação de reajuste de preço de venda
- Orientações de marketing por produto geradas pela LLM

---

## Estrutura do projeto

```
dashboard_inteligente/
│
├── data/                        # planilhas e arquivos gerados
│   ├── vendas.xlsx
│   ├── marketing.xlsx
│   ├── merged.parquet
│   ├── margem.parquet
│   ├── canais.parquet
│   └── modelo.joblib
│
├── src/
│   ├── ingestion/merger.py      # LLM detecta e executa o JOIN
│   ├── analytics/metrics.py     # Métrica X (margem) e Y (eficiência canal)
│   ├── ml/predictor.py          # treino e simulação What-If
│   ├── llm/advisor.py           # conselho executivo via Ollama
│   └── dashboard/app.py         # interface Streamlit
│
├── utility/                     # scripts de preparação (serão unificados)
│   ├── gerar_dados.py
│   ├── testar_merger.py
│   ├── testar_metrics.py
│   ├── testar_MachineLearning.py
│   └── testar_advisor.py
│
├── requirements.txt
└── .env.example
```

---

## Contexto

Projeto desenvolvido como portfólio durante o 7º período de Ciência da Computação. Meu TCC envolve conceitos de GNNs mas eu ainda não tinha aplicado ML na prática. Esse projeto foi a ponte entre teoria e aplicação — entender na prática como dados viram modelos, como modelos viram previsões e como LLMs e ML trabalham juntos com papéis diferentes num mesmo sistema.

Feedbacks são bem-vindos.