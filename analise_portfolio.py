"""
========================================================================
Projeto: Análise de Portfolio - MAIS MERCANTIL
Desenvolvido por: Ronaldo Pereira
Data: 10 de Dezembro de 2024
Empresa: Zeta Dados

Descrição:
-----------
Este script realiza uma análise completa do portfolio de produtos da
MAIS MERCANTIL, distribuidora de produtos de Higiene, Limpeza e Alimentos.
O objetivo é identificar as melhores subcategorias e produtos para cada
canal de clientes, considerando métricas como margem, popularidade e
faturamento.

Funcionalidades:
---------------
- Análise de dados de vendas e clientes
- Cálculo de métricas por subcategoria
- Seleção das top 5 subcategorias por canal
- Identificação dos 10 melhores SKUs por subcategoria

Última atualização: 10/12/2024
========================================================================
"""

import pandas as pd
import numpy as np

def carregar_dados():
    # Carrega as bases de dados
    clientes_df = pd.read_excel('bd_clientes.xlsx')
    vendas_df = pd.read_excel('bd_vendas.xlsx')
    
    # Padroniza os nomes das colunas para maiúsculas
    clientes_df.columns = clientes_df.columns.str.upper()
    vendas_df.columns = vendas_df.columns.str.upper()
    
    # Renomeia a coluna canal para CANAL
    clientes_df = clientes_df.rename(columns={'CANAL': 'CANAL'})
    
    # Converte a coluna MARGEM de percentual para decimal
    vendas_df['MARGEM'] = vendas_df['MARGEM'].str.rstrip('%').astype('float') / 100.0
    
    return clientes_df, vendas_df

def calcular_metricas_subcategoria(vendas_df, clientes_df):
    # Merge com a base de clientes para ter informação do canal
    df_analise = pd.merge(vendas_df, clientes_df, on='ID_CLIENTE', how='left')
    
    # Agrupa por canal e subcategoria
    metricas = df_analise.groupby(['CANAL', 'SUBCATEGORIA_SKU']).agg({
        'ID_SKU': 'nunique',  # Quantidade de SKUs diferentes
        'ID_CLIENTE': 'nunique',  # Popularidade (quantidade de clientes)
        'VENDA_VALOR': 'sum',  # Faturamento total
        'MARGEM': 'mean'  # Margem média
    }).reset_index()
    
    # Normaliza as métricas para criar um score
    for col in ['ID_SKU', 'ID_CLIENTE', 'VENDA_VALOR', 'MARGEM']:
        metricas[f'{col}_NORM'] = (metricas[col] - metricas[col].min()) / (metricas[col].max() - metricas[col].min())
    
    # Cria score final (peso igual para cada métrica)
    metricas['SCORE'] = (
        metricas['ID_CLIENTE_NORM'] * 0.3 +  # Popularidade
        metricas['VENDA_VALOR_NORM'] * 0.4 +  # Faturamento
        metricas['MARGEM_NORM'] * 0.3         # Margem
    )
    
    return metricas

def selecionar_top_skus(vendas_df, clientes_df, subcategorias_selecionadas):
    # Merge com a base de clientes
    df_analise = pd.merge(vendas_df, clientes_df, on='ID_CLIENTE', how='left')
    
    resultados = {}
    for canal in subcategorias_selecionadas.keys():
        resultados[canal] = {}
        for subcategoria in subcategorias_selecionadas[canal]:
            # Filtra dados do canal e subcategoria
            mask = (df_analise['CANAL'] == canal) & (df_analise['SUBCATEGORIA_SKU'] == subcategoria)
            df_filtrado = df_analise[mask]
            
            # Agrupa por SKU e calcula métricas
            skus = df_filtrado.groupby(['ID_SKU', 'NOME_SKU']).agg({
                'ID_CLIENTE': 'nunique',  # Popularidade
                'VENDA_VALOR': 'sum',     # Faturamento
                'MARGEM': 'mean'          # Margem média
            }).reset_index()
            
            # Normaliza e calcula score
            for col in ['ID_CLIENTE', 'VENDA_VALOR', 'MARGEM']:
                skus[f'{col}_NORM'] = (skus[col] - skus[col].min()) / (skus[col].max() - skus[col].min())
            
            skus['SCORE'] = (
                skus['ID_CLIENTE_NORM'] * 0.3 +
                skus['VENDA_VALOR_NORM'] * 0.4 +
                skus['MARGEM_NORM'] * 0.3
            )
            
            # Seleciona top 10 SKUs
            top_skus = skus.nlargest(10, 'SCORE')
            resultados[canal][subcategoria] = list(zip(top_skus['ID_SKU'], top_skus['NOME_SKU']))
    
    return resultados

def main():
    # Carrega os dados
    print("Carregando dados...")
    clientes_df, vendas_df = carregar_dados()
    
    # Calcula métricas por subcategoria
    print("Calculando métricas por subcategoria...")
    metricas = calcular_metricas_subcategoria(vendas_df, clientes_df)
    
    # Identifica os dois principais canais por volume de vendas
    principais_canais = vendas_df.merge(clientes_df, on='ID_CLIENTE')['CANAL'].value_counts().nlargest(2).index.tolist()
    
    # Seleciona top 5 subcategorias para cada canal principal
    subcategorias_selecionadas = {}
    for canal in principais_canais:
        top_subcategorias = metricas[metricas['CANAL'] == canal].nlargest(5, 'SCORE')
        subcategorias_selecionadas[canal] = top_subcategorias['SUBCATEGORIA_SKU'].tolist()
        
        print(f"\nTop 5 Subcategorias para {canal}:")
        for idx, row in top_subcategorias.iterrows():
            print(f"- {row['SUBCATEGORIA_SKU']} (Score: {row['SCORE']:.3f})")
    
    # Seleciona top 10 SKUs para cada subcategoria
    print("\nSelecionando top 10 SKUs para cada subcategoria...")
    resultados_skus = selecionar_top_skus(vendas_df, clientes_df, subcategorias_selecionadas)
    
    # Exibe resultados
    for canal in resultados_skus:
        print(f"\nCanal: {canal}")
        for subcategoria, skus in resultados_skus[canal].items():
            print(f"\nSubcategoria: {subcategoria}")
            print("Top 10 SKUs:")
            for sku_id, sku_nome in skus:
                print(f"- {sku_nome} (ID: {sku_id})")

if __name__ == "__main__":
    main()
