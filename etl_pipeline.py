import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

# ==========================================
# CONFIGURAÇÃO DE LOGS
# ==========================================

logging.basicConfig(
    filename='logs/etl.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info('Iniciando pipeline ETL...')

# ==========================================
# EXTRAÇÃO (EXTRACT)
# ==========================================

try:
    vendas = pd.read_csv('data/vendas.csv')
    clientes = pd.read_csv('data/clientes.csv')
    produtos = pd.read_csv('data/produtos.csv')

    logging.info('Arquivos carregados com sucesso.')

except Exception as e:
    logging.error(f'Erro ao carregar arquivos: {e}')
    raise

# ==========================================
# TRANSFORMAÇÃO (TRANSFORM)
# ==========================================

# Convertendo data
vendas['data'] = pd.to_datetime(vendas['data'])

# Criando faturamento
vendas['faturamento'] = (
    vendas['quantidade'] * vendas['valor_unitario']
)

# Merge entre tabelas
base_final = vendas.merge(
    clientes,
    on='id_cliente',
    how='left'
)

base_final = base_final.merge(
    produtos,
    on='id_produto',
    how='left'
)

# Tratando valores nulos
base_final.fillna('Não Informado', inplace=True)

# Removendo duplicados
base_final.drop_duplicates(inplace=True)

# Criando colunas analíticas
base_final['mes'] = base_final['data'].dt.month
base_final['ano'] = base_final['data'].dt.year

base_final['ticket_medio'] = (
    base_final['faturamento'] /
    base_final['quantidade']
)

logging.info('Transformações realizadas com sucesso.')

# ==========================================
# ANÁLISES
# ==========================================

# Faturamento total
faturamento_total = base_final['faturamento'].sum()

# Produto mais vendido
produto_mais_vendido = (
    base_final.groupby('produto')['quantidade']
    .sum()
    .sort_values(ascending=False)
)

# Cidade com maior faturamento
cidade_faturamento = (
    base_final.groupby('cidade')['faturamento']
    .sum()
    .sort_values(ascending=False)
)

print('\n===== INSIGHTS =====')

print(f'Faturamento Total: R$ {faturamento_total:,.2f}')

print('\nProdutos mais vendidos:')
print(produto_mais_vendido)

print('\nFaturamento por cidade:')
print(cidade_faturamento)

# ==========================================
# VISUALIZAÇÃO
# ==========================================

plt.figure(figsize=(10, 6))

sns.barplot(
    x=produto_mais_vendido.index,
    y=produto_mais_vendido.values
)

plt.title('Produtos Mais Vendidos')
plt.xlabel('Produto')
plt.ylabel('Quantidade')

plt.tight_layout()

plt.savefig('output/dashboard.png')

logging.info('Dashboard gerado com sucesso.')

# ==========================================
# LOAD
# ==========================================

# Salvando CSV
base_final.to_csv(
    'output/relatorio_final.csv',
    index=False
)

# Salvando SQLite
engine = create_engine(
    'sqlite:///output/banco.db'
)

base_final.to_sql(
    'fato_vendas',
    con=engine,
    if_exists='replace',
    index=False
)

logging.info('Dados carregados no SQLite.')

# ==========================================
# KPI'S
# ==========================================

kpis = {
    'Faturamento Total': faturamento_total,
    'Quantidade de Vendas': len(base_final),
    'Clientes Únicos': base_final['id_cliente'].nunique(),
    'Produtos Únicos': base_final['produto'].nunique(),
    'Ticket Médio Geral': round(
        base_final['ticket_medio'].mean(),
        2
    )
}

print('\n===== KPI\'S =====')

for chave, valor in kpis.items():
    print(f'{chave}: {valor}')

logging.info('Pipeline ETL finalizado com sucesso.')