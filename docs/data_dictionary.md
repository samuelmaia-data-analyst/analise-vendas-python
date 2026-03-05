# Data Dictionary

Fonte principal: `data/raw/sales_data_sample.csv`

| Coluna | Definição | Tipo esperado | Regra de qualidade |
|---|---|---|---|
| ORDERNUMBER | Identificador do pedido | Inteiro | Não nulo |
| ORDERLINENUMBER | Número da linha do item no pedido | Inteiro | Não nulo e > 0 |
| ORDERDATE | Data da transação | Data | Conversível para `datetime` |
| SALES | Receita do item | Numérico | Não nulo e >= 0 |
| QUANTITYORDERED | Quantidade vendida | Inteiro | >= 1 |
| PRICEEACH | Preço unitário | Numérico | >= 0 |
| PRODUCTCODE | Código único do produto | Texto | Não nulo |
| PRODUCTLINE | Linha/categoria de produto | Texto | Não nulo |
| CUSTOMERNAME | Nome do cliente | Texto | Não nulo |
| COUNTRY | País do cliente | Texto | Não nulo |
| STATUS | Status do pedido | Texto | Domínio controlado (ex.: `Shipped`, `Cancelled`) |
| DEALSIZE | Porte do pedido | Texto | Domínio controlado (`Small`, `Medium`, `Large`) |

## Observações

- Colunas usadas nas métricas principais: `ORDERDATE`, `SALES`.
- Colunas usadas na análise de concentração: `PRODUCTLINE`, `CUSTOMERNAME`, `COUNTRY`.
- Regras de schema base implementadas em `src/data_contract.py`.
