Testando com modelo llama3.1:latest e deu time out e realmente as requisições demoraram muito. testando novo modelo.

Machine Learning
 -Target receita total por venda
 -Features sao as variaveis de entrada para previsão:
 dolar_na_compra      → afeta custo, que afeta preço, que afeta demanda
 orcamento_marketing  → mais marketing tende a gerar mais vendas
 mes_num              → captura sazonalidade (dezembro vende mais)
 produto_enc          → cada produto tem elasticidade diferente
 quantidade           → vendas em volume maior têm dinâmica diferente
 desconto_aplicado    → desconto aumenta volume mas reduz ticket
 
Note: Testes iniciais com MAPE em 13.2%, foi estipulado uma meta incial de 25% já estamos melhor que a meta
n_estimators=200,    # número de árvores na sequência
learning_rate=0.08,  # tamanho do passo de correção a cada árvore
max_depth=4,         # menor = aprende mais devagar mas generaliza melhor

## Lições aprendidas

### Fan-out em JOIN
Ao fazer LEFT JOIN entre vendas e marketing agregado, o valor de
orcamento_marketing se repete em cada linha de venda do mês.
Somar diretamente infla o marketing em até 12x.
Solução: groupby por produto+mês com first() antes de somar.

### Marketing zero no último mês
Produtos sem campanha no último mês tinham orcamento_marketing=0,
fazendo a simulação retornar o mesmo valor para qualquer variação de marketing.
Solução: usar média histórica ignorando zeros em vez do valor do último mês.