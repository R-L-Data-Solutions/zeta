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

Metodologia de Análise:
----------------------
1. Seleção de Métricas:
   - Popularidade (30%): Quantidade de clientes únicos que compram o produto
     Justificativa: Produtos populares têm maior probabilidade de venda e
     menor risco de estoque parado.
   
   - Faturamento (40%): Valor total de vendas
     Justificativa: Maior peso pois representa o volume de negócios e
     a capacidade de geração de receita. Produtos com alto faturamento
     geralmente têm boa aceitação no mercado.
   
   - Margem (30%): Percentual de lucro
     Justificativa: Importante para a rentabilidade, mas balanceado com
     outros fatores para não privilegiar apenas produtos caros com pouco
     giro.

2. Processo de Scoring:
   - Todas as métricas são normalizadas (0-1) para permitir comparação justa
   - Score final = (Popularidade * 0.3) + (Faturamento * 0.4) + (Margem * 0.3)
   - Esta fórmula equilibra volume, receita e lucratividade

3. Critérios de Seleção:
   - Top 5 Subcategorias: Selecionadas pelo maior score combinado
   - Top 10 SKUs: Escolhidos dentro de cada subcategoria usando a mesma metodologia

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

# Configuração dos pesos para o cálculo do score
# Estes pesos podem ser ajustados conforme a estratégia do negócio
PESO_POPULARIDADE = 0.3  # Representa a importância do alcance do produto
PESO_FATURAMENTO = 0.4   # Maior peso devido ao impacto direto no negócio
PESO_MARGEM = 0.3        # Equilibra rentabilidade com volume

def carregar_dados():
    """
    Carrega e prepara os dados das bases de clientes e vendas.
    
    Returns:
        tuple: (DataFrame clientes, DataFrame vendas) com dados normalizados
    """
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
    """
    Calcula métricas agregadas por subcategoria e canal.
    
    Processo:
    1. Agrega dados por canal e subcategoria
    2. Calcula métricas chave (popularidade, faturamento, margem)
    3. Normaliza métricas para comparação justa
    4. Aplica pesos para gerar score final
    
    Args:
        vendas_df (DataFrame): Base de vendas
        clientes_df (DataFrame): Base de clientes
    
    Returns:
        DataFrame: Métricas calculadas com score final
    """
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
    
    # Cria score final aplicando os pesos definidos
    metricas['SCORE'] = (
        metricas['ID_CLIENTE_NORM'] * PESO_POPULARIDADE +  # Popularidade
        metricas['VENDA_VALOR_NORM'] * PESO_FATURAMENTO +  # Faturamento
        metricas['MARGEM_NORM'] * PESO_MARGEM             # Margem
    )
    
    return metricas

def selecionar_top_skus(vendas_df, clientes_df, subcategorias_selecionadas):
    """
    Seleciona os 10 melhores SKUs para cada subcategoria em cada canal.
    
    Metodologia:
    1. Filtra dados por canal e subcategoria
    2. Calcula métricas individuais por SKU
    3. Aplica a mesma lógica de scoring das subcategorias
    4. Seleciona os 10 produtos com maior score
    
    Args:
        vendas_df (DataFrame): Base de vendas
        clientes_df (DataFrame): Base de clientes
        subcategorias_selecionadas (dict): Dicionário com top subcategorias por canal
    
    Returns:
        dict: Dicionário com os 10 melhores SKUs por subcategoria e canal
    """
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
            
            # Aplica os mesmos pesos usados na análise de subcategorias
            skus['SCORE'] = (
                skus['ID_CLIENTE_NORM'] * PESO_POPULARIDADE +
                skus['VENDA_VALOR_NORM'] * PESO_FATURAMENTO +
                skus['MARGEM_NORM'] * PESO_MARGEM
            )
            
            # Seleciona top 10 SKUs
            top_skus = skus.nlargest(10, 'SCORE')
            resultados[canal][subcategoria] = list(zip(top_skus['ID_SKU'], top_skus['NOME_SKU']))
    
    return resultados

def main():
    """
    Função principal que executa o processo completo de análise.
    
    Processo:
    1. Carrega e prepara os dados
    2. Calcula métricas por subcategoria
    3. Identifica principais canais
    4. Seleciona melhores subcategorias
    5. Identifica melhores produtos
    6. Apresenta resultados
    """
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
            print(f"- {row['SUBCATEGORIA_SKU']}")
            print(f"  Score: {row['SCORE']:.3f}")
            print(f"  Popularidade: {row['ID_CLIENTE']:.0f} clientes")
            print(f"  Faturamento: R$ {row['VENDA_VALOR']:,.2f}")
            print(f"  Margem média: {row['MARGEM']*100:.1f}%")
    
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
