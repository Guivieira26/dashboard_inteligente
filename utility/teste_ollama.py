import requests
import json

# O Ollama expõe uma API HTTP simples no localhost
# Não precisa de chave — ele roda local
url = "http://localhost:11434/api/generate"

payload = {
    "model": "llama3.1:latest",      # o modelo que você baixou
    "prompt": "Qual sentido da vida?",
    "stream": False            # False = espera a resposta completa antes de retornar
}

print("Enviando para o Ollama...")
resposta = requests.post(url, json=payload)

# A resposta vem como JSON
dados = resposta.json()
print("\nResposta do modelo:")
print(dados["response"])