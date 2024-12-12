"""
========================================================================
Projeto: Dashboard de Análise de Portfolio - MAIS MERCANTIL
Desenvolvido por: Ronaldo Pereira
Data: 10 de Dezembro de 2024
Empresa: Zeta Dados

Descrição:
-----------
Dashboard interativo para análise do portfolio de produtos da MAIS MERCANTIL.
Permite visualização e análise dinâmica das principais métricas de vendas,
margem e popularidade por canal e subcategoria.

Funcionalidades:
---------------
- Visualização interativa de dados
- Filtros por canal e subcategoria
- Gráficos de performance
- Análise detalhada de SKUs
- Métricas em tempo real

Tecnologias utilizadas:
---------------------
- Python 3.9
- Streamlit
- Plotly
- Pandas
- NumPy

Última atualização: 10/12/2024
========================================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from PIL import Image

# Configuração da página
st.set_page_config(
    page_title="Análise de Portfolio - MAIS MERCANTIL",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Customização do tema com informações do desenvolvedor
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stTitle {
        color: #1E3D59;
        font-size: 3rem !important;
        padding-bottom: 2rem;
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .developer-info {
        font-size: 0.8rem;
        color: #666;
        text-align: right;
        padding: 5px;
        position: fixed;
        bottom: 0;
        right: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho com logo
col1, col2 = st.columns([1, 4])

with col1:
    # Carrega e exibe a imagem
    try:
        image = Image.open('images.png')
        st.image(image, width=150)
    except:
        st.write("Imagem 'images.png' não encontrada")

with col2:
    st.title("Dashboard - Análise de Portfolio MAIS MERCANTIL")
    st.markdown("---")

# Título
# st.title("Dashboard - Análise de Portfolio MAIS MERCANTIL")

@st.cache_data
def carregar_dados():
    # Carrega as bases de dados
    clientes_df = pd.read_excel('bd_clientes.xlsx')
    vendas_df = pd.read_excel('bd_vendas.xlsx')
    
    # Padroniza os nomes das colunas para maiúsculas
    clientes_df.columns = clientes_df.columns.str.upper()
    vendas_df.columns = vendas_df.columns.str.upper()
    
    # Converte a coluna MARGEM de percentual para decimal
    vendas_df['MARGEM'] = vendas_df['MARGEM'].str.rstrip('%').astype('float') / 100.0
    
    return clientes_df, vendas_df

def calcular_metricas_subcategoria(vendas_df, clientes_df):
    # Merge com a base de clientes
    df_analise = pd.merge(vendas_df, clientes_df, on='ID_CLIENTE', how='left')
    
    # Agrupa por canal e subcategoria
    metricas = df_analise.groupby(['CANAL', 'SUBCATEGORIA_SKU']).agg({
        'ID_SKU': 'nunique',  # Quantidade de SKUs diferentes
        'ID_CLIENTE': 'nunique',  # Popularidade (quantidade de clientes)
        'VENDA_VALOR': 'sum',  # Faturamento total
        'MARGEM': 'mean'  # Margem média
    }).reset_index()
    
    # Normaliza as métricas
    for col in ['ID_SKU', 'ID_CLIENTE', 'VENDA_VALOR', 'MARGEM']:
        metricas[f'{col}_NORM'] = (metricas[col] - metricas[col].min()) / (metricas[col].max() - metricas[col].min())
    
    # Calcula score
    metricas['SCORE'] = (
        metricas['ID_CLIENTE_NORM'] * 0.3 +  # Popularidade
        metricas['VENDA_VALOR_NORM'] * 0.4 +  # Faturamento
        metricas['MARGEM_NORM'] * 0.3         # Margem
    )
    
    return metricas

# Carrega os dados
clientes_df, vendas_df = carregar_dados()

# Calcula métricas
metricas_df = calcular_metricas_subcategoria(vendas_df, clientes_df)

# Sidebar para filtros
st.sidebar.image('images.png', width=100)
st.sidebar.markdown("## Filtros de Análise")
st.sidebar.markdown("---")

canal_selecionado = st.sidebar.selectbox(
    "Selecione o Canal",
    options=metricas_df['CANAL'].unique(),
    help="Escolha o canal de vendas para análise"
)

# Filtra dados pelo canal selecionado
dados_canal = metricas_df[metricas_df['CANAL'] == canal_selecionado]

# Container para KPIs principais
st.markdown("### Visão Geral do Canal")
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    total_vendas = vendas_df.merge(clientes_df, on='ID_CLIENTE')
    total_vendas = total_vendas[total_vendas['CANAL'] == canal_selecionado]['VENDA_VALOR'].sum()
    st.metric(
        "Faturamento Total",
        f"R$ {total_vendas:,.2f}",
        help="Faturamento total do canal selecionado"
    )

with kpi2:
    total_clientes = vendas_df.merge(clientes_df, on='ID_CLIENTE')
    total_clientes = total_clientes[total_clientes['CANAL'] == canal_selecionado]['ID_CLIENTE'].nunique()
    st.metric(
        "Total de Clientes",
        f"{total_clientes:,}",
        help="Número total de clientes únicos no canal"
    )

with kpi3:
    margem_media = vendas_df.merge(clientes_df, on='ID_CLIENTE')
    margem_media = margem_media[margem_media['CANAL'] == canal_selecionado]['MARGEM'].mean()
    st.metric(
        "Margem Média",
        f"{margem_media:.1%}",
        help="Margem média de lucro no canal"
    )

st.markdown("---")

# Layout em colunas para gráficos
col1, col2 = st.columns(2)

with col1:
    # Gráfico de Top 5 Subcategorias por Score
    fig_score = px.bar(
        dados_canal.nlargest(5, 'SCORE'),
        x='SUBCATEGORIA_SKU',
        y='SCORE',
        title=f'Top 5 Subcategorias por Score - {canal_selecionado}',
        color='SCORE',
        color_continuous_scale='Viridis'
    )
    fig_score.update_layout(
        xaxis_title="Subcategoria",
        yaxis_title="Score",
        showlegend=False,
        height=400,
        template='none',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#f0f0f0'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    )
    st.plotly_chart(fig_score, use_container_width=True)

with col2:
    # Gráfico de dispersão Margem x Faturamento
    fig_scatter = px.scatter(
        dados_canal,
        x='MARGEM',
        y='VENDA_VALOR',
        size='ID_CLIENTE',
        color='SCORE',
        hover_data=['SUBCATEGORIA_SKU'],
        title=f'Margem x Faturamento - {canal_selecionado}'
    )
    fig_scatter.update_layout(
        xaxis_title="Margem",
        yaxis_title="Faturamento (R$)",
        height=400,
        template='none',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='#f0f0f0'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    )
    fig_scatter.update_traces(
        marker=dict(line=dict(width=1, color='DarkSlateGrey')),
        selector=dict(mode='markers')
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# Top 10 SKUs da subcategoria selecionada
st.header("Análise Detalhada de SKUs")
subcategoria_selecionada = st.selectbox(
    "Selecione a Subcategoria para análise detalhada",
    options=dados_canal['SUBCATEGORIA_SKU'].unique(),
    help="Escolha uma subcategoria para ver os top 10 SKUs"
)

# Filtra vendas para a subcategoria selecionada
vendas_subcategoria = vendas_df.merge(clientes_df, on='ID_CLIENTE')
vendas_subcategoria = vendas_subcategoria[
    (vendas_subcategoria['CANAL'] == canal_selecionado) &
    (vendas_subcategoria['SUBCATEGORIA_SKU'] == subcategoria_selecionada)
]

# Agrupa por SKU
skus_metrics = vendas_subcategoria.groupby(['ID_SKU', 'NOME_SKU']).agg({
    'ID_CLIENTE': 'nunique',
    'VENDA_VALOR': 'sum',
    'MARGEM': 'mean'
}).reset_index()

# Normaliza e calcula score
for col in ['ID_CLIENTE', 'VENDA_VALOR', 'MARGEM']:
    skus_metrics[f'{col}_NORM'] = (skus_metrics[col] - skus_metrics[col].min()) / (skus_metrics[col].max() - skus_metrics[col].min())

skus_metrics['SCORE'] = (
    skus_metrics['ID_CLIENTE_NORM'] * 0.3 +
    skus_metrics['VENDA_VALOR_NORM'] * 0.4 +
    skus_metrics['MARGEM_NORM'] * 0.3
)

# Mostra top 10 SKUs
top_skus = skus_metrics.nlargest(10, 'SCORE')
st.subheader(f"Top 10 SKUs - {subcategoria_selecionada}")

# Cria uma tabela formatada com cores mais atraentes
fig_table = go.Figure(data=[go.Table(
    header=dict(
        values=['SKU', 'Nome', 'Qtd. Clientes', 'Faturamento', 'Margem', 'Score'],
        fill_color='#1E3D59',
        font=dict(color='white', size=12),
        align='left',
        height=40
    ),
    cells=dict(
        values=[
            top_skus['ID_SKU'],
            top_skus['NOME_SKU'],
            top_skus['ID_CLIENTE'].apply(lambda x: f"{x:,}"),
            top_skus['VENDA_VALOR'].apply(lambda x: f"R$ {x:,.2f}"),
            (top_skus['MARGEM'] * 100).round(2).astype(str) + '%',
            top_skus['SCORE'].round(3)
        ],
        fill_color=['#F5F7FA']*6,
        font=dict(color=['#1E3D59']*6),
        align='left',
        height=30
    )
)])

fig_table.update_layout(
    margin=dict(t=5, b=5),
    height=350
)

st.plotly_chart(fig_table, use_container_width=True)

# Métricas gerais em cards mais atraentes
st.markdown("### Métricas Gerais da Subcategoria")
st.markdown("""
    <style>
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1E3D59;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(skus_metrics):,}</div>
            <div class="metric-label">Total SKUs</div>
        </div>
    """, unsafe_allow_html=True)
    
with col2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{vendas_subcategoria['ID_CLIENTE'].nunique():,}</div>
            <div class="metric-label">Total Clientes</div>
        </div>
    """, unsafe_allow_html=True)
    
with col3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">R$ {vendas_subcategoria['VENDA_VALOR'].sum():,.2f}</div>
            <div class="metric-label">Faturamento Total</div>
        </div>
    """, unsafe_allow_html=True)
    
with col4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{(vendas_subcategoria['MARGEM'].mean() * 100):.2f}%</div>
            <div class="metric-label">Margem Média</div>
        </div>
    """, unsafe_allow_html=True)

# Adiciona informações do desenvolvedor no footer
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        Desenvolvido por Ronaldo Pereira | Zeta Dados<br>
        Análise de Portfolio MAIS MERCANTIL<br>
        Dezembro 2024
    </div>
""", unsafe_allow_html=True)
