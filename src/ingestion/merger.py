# Usar o Ollama para descobrir automaticamento como cruzar duas planilhas com nomes de colunas diferentes
# LEFT JOIN - Merge

import json
import re
import requests
import pandas as pd

#API do Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "llama3.1:latest"

def resumir_schema(df: pd.DataFrame, none: str) -> str:
    linhas = [f"Planilha: {none}"]
    linhas.append(f"Total de linhas: {len(df)}")
    linhas.append("Colunas:")

    for col in df.columns:
        # Pega 3 valores não-nulos como exemplo
        exemplos = df[col].dropna().head(3).tolist()
        tipo     = str(df[col].dtype)
        linhas.append(f"  - {col} ({tipo}): exemplos → {exemplos}")

    return "\n".join(linhas)

def ask_ollama(prompt: str) ->str:
    payload = {
        "model": MODELO,
        "prompt": prompt,
        "stream": False,
        #Controle comportamental do modelo:
        "options":{
            "temperatura":0.1, # Baixa temperatura = respostas mais objetivas e menos criativas
            "num_predict": 512 # Limite tokens
        }   
    }
    try:
        resposta = requests.post(OLLAMA_URL, json=payload, timeout=150)
        resposta.raise_for_status()   # lança exceção se status != 200
        return resposta.json()["response"]

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Ollama não está rodando. Execute: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Ollama demorou mais de 150s. Tente um modelo menor ou aguarde."
        )
        
def extrair_json(texto: str) -> dict:
    # Tenta parser direto
    try:
        return json.loads(texto.strip())
    except json.JSONDecodeError:
        pass
    
    #remover markdown
    texto_limpo = re.sub(r"```json|```", "", texto).strip()
    try:
        return json.loads(texto_limpo)
    except json.JSONDecodeError:
        pass
    
    # Ultima tentativa
    
    match = re.search(r"\{.*\}", texto_limpo, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    # Se tudo falhar, retorna configuração padrão
    print("⚠️  LLM não retornou JSON válido. Usando configuração padrão.")
    return {
        "tipo_join":       "left",
        "chave_esquerda":  ["produto", "mes_referencia"],
        "chave_direita":   ["produto_alvo", "mes_referencia"],
        "justificativa":   "fallback automático"
    }
    
def detectar_join(df_vendas: pd.DataFrame, df_marketing: pd.DataFrame) -> dict:
    # Enviar para LLM e recebe a estratégia do JOIN
    
    #Resumir os schemas para o modelo entender o formato dos dados
    schema_vendas = resumir_schema(df_vendas, "vendas")
    schema_marketing = resumir_schema(df_marketing, "marketing")
    
    prompt = f"""Você é um engenheiro de dados. Analise os dois schemas abaixo.
    e decida como cruzar as planilhas para montar um dataset analítico completo.

    {schema_vendas}

    {schema_marketing}

    Regras:
    - Use LEFT JOIN para manter todas as vendas mesmo sem campanha
    - O cruzamento deve ser por produto E por mês
    - Em vendas, o mês está dentro da coluna data_venda (formato YYYY-MM-DD)
    - Em marketing, o mês é a coluna mes_referencia (formato YYYY-MM)
    - Após o merge, colunas de marketing sem correspondência devem virar 0

    Responda SOMENTE com JSON válido, sem texto antes ou depois, sem markdown:
    {{
    "tipo_join": "left",
    "chave_esquerda": ["coluna_de_vendas_1", "coluna_de_vendas_2"],
    "chave_direita":  ["coluna_de_marketing_1", "coluna_de_marketing_2"],
    "justificativa":  "explicação em uma frase"
    }}"""
    
    print("Enviando schemas para o Ollama...")
    resposta_texto = ask_ollama(prompt)
    
    print(f"\nResposta bruta do modelo: {resposta_texto}")
    
    config = extrair_json(resposta_texto)
    print(f"\nConfiguração extraída: {config}")
    return config

def validar_e_corrigir_config(config: dict, df_vendas: pd.DataFrame) -> dict:
    """
    A LLM pode sugerir chaves que não casam por diferença de formato.
    Essa função verifica e corrige antes do merge acontecer.

    Regra específica desse projeto:
    - Se a LLM sugeriu data_venda como chave temporal, troca por mes_referencia
      porque data_venda é YYYY-MM-DD e mes_referencia é YYYY-MM
    - mes_referencia já foi derivada do data_venda antes de chegar aqui
    """
    chave_esq = config.get("chave_esquerda", [])

    # Se a LLM sugeriu data_venda, corrige para mes_referencia
    if "data_venda" in chave_esq:
        print("⚠️  LLM sugeriu data_venda como chave — corrigindo para mes_referencia")
        chave_esq = [
            "mes_referencia" if c == "data_venda" else c
            for c in chave_esq
        ]
        config["chave_esquerda"] = chave_esq
        config["corrigido"] = True

    return config


def executar_merge(
    df_vendas: pd.DataFrame,
    df_marketing: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    # Executa o merge com base na configuração da LLM
    
    # Vendas nao tem mes separado e marketing temos formado YYYY-MM, entao precisamos criar uma coluna de mes em vendas
    df_v = df_vendas.copy()
    df_m = df_marketing.copy()
    
    df_v["mes_referencia"]=(
        pd.to_datetime(df_v["data_venda"])
        .dt.to_period("M") # Converte para mensal
        .astype(str) # Converte de volta para string no formato YYYY-MM
    )
    
    # Evita linha de venda duplicada por causa do merge (Ex: Se houver 3 campanhas de um produto X ele não vai repetir 3x)
    df_mkt_agg = (
        df_m
        .groupby(["produto_alvo", "mes_referencia"], as_index=False)
        .agg(
            orcamento_marketing=("orcamento_gasto",  "sum"),
            conversoes_mkt     =("conversoes",        "sum"),
            cpl_medio          =("custo_por_lead",    "mean"),
            impressoes_total   =("impressoes",        "sum"),
        )
    )
    
    # Valida e corrige sugestão da LLM antes de usar
    config = validar_e_corrigir_config(config, df_v)
    
    chave_esq = config["chave_esquerda"]   # ["produto", "mes_referencia"]
    chave_dir = config["chave_direita"]    # ["produto_alvo", "mes_referencia"]

    print(f"   Chave esquerda: {chave_esq}")
    print(f"   Chave direita:  {chave_dir}")
    
    df_merged = df_v.merge(
        df_mkt_agg,
        left_on = chave_esq,
        right_on= chave_dir,
        how     = config.get("tipo_join", "left")
    )
    
    cols_mkt = ["orcamento_marketing", "conversoes_mkt", "cpl_medio", "impressoes_total"]
    df_merged[cols_mkt] = df_merged[cols_mkt].fillna(0)

    return df_merged

