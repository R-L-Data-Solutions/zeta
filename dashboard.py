"""
Dashboard Interativo - Análise de Portfolio MAIS MERCANTIL
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from PIL import Image
import os

# Configuração da página
st.set_page_config(
    page_title="Análise de Portfolio - MAIS MERCANTIL",
    page_icon="📊",
    layout="wide"
)

# Estilo personalizado
st.markdown("""
    <style>
    .main {
        background-color: #FFFFFF;
        color: #333333;
    }
    .stMetric {
        background-color: #F8F9FA;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #333333;
    }
    .reportview-container {
        background: #FFFFFF;
        color: #333333;
    }
    .sidebar .sidebar-content {
        background: #F8F9FA;
        color: #333333;
    }
    h1, h2, h3 {
        color: #333333;
        font-weight: 500;
    }
    p, .stMarkdown {
        color: #333333;
    }
    </style>
""", unsafe_allow_html=True)

def formatar_valor(valor):
    """Formata valores monetários."""
    return f"R$ {valor:,.2f}"

def criar_grafico_barras(df, x, y, title):
    """Cria gráfico de barras com estilo padronizado."""
    # Definir cores diferentes para cada barra
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    fig = go.Figure()
    
    # Adiciona as barras uma por uma para ter cores diferentes
    for i, (index, row) in enumerate(df.iterrows()):
        fig.add_trace(go.Bar(
            x=[row[x]],
            y=[row[y]],
            text=[f"{row[y]:.3f}"],
            textposition='auto',
            name=row[x],
            marker_color=colors[i % len(colors)]
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x.replace('_', ' ').title(),
        yaxis_title='Score',
        plot_bgcolor='white',
        showlegend=False,
        height=400,
        bargap=0.2
    )
    
    return fig

def criar_grafico_scatter(df, x, y, color, title):
    """Cria gráfico de dispersão com estilo padronizado."""
    # Criar o gráfico
    fig = go.Figure()
    
    # Adicionar os pontos
    fig.add_trace(go.Scatter(
        x=df[x],
        y=df[y],
        mode='markers',
        marker=dict(
            size=10,
            color=df[color],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Margem')
        ),
        hovertemplate="<br>".join([
            "Margem: %{x:.1%}",
            "Valor: R$ %{y:,.2f}",
            "<extra></extra>"
        ])
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Margem (%)',
        yaxis_title='Valor de Venda (R$)',
        plot_bgcolor='white',
        height=400,
        xaxis=dict(
            tickformat='.0%',
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        ),
        yaxis=dict(
            tickformat='R$ ,.0f',
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        )
    )
    
    return fig

def criar_grafico_detalhado(df_subcategoria, title):
    """Cria gráfico de barras horizontal para análise da subcategoria."""
    # Preparar os dados
    df_analise = df_subcategoria.copy()
    
    # Calcular os limites para as faixas de venda
    min_valor = df_analise['VENDA_VALOR'].min()
    max_valor = df_analise['VENDA_VALOR'].max()
    
    try:
        # Primeira tentativa: usar qcut para divisão em quartis
        df_analise['Faixa'] = pd.qcut(
            df_analise['VENDA_VALOR'], 
            q=3, 
            labels=['Vendas Baixas', 'Vendas Médias', 'Vendas Altas']
        )
    except ValueError:
        # Se falhar, usar cut com intervalos fixos
        bins = [
            min_valor,
            min_valor + (max_valor - min_valor)/3,
            min_valor + 2*(max_valor - min_valor)/3,
            max_valor
        ]
        df_analise['Faixa'] = pd.cut(
            df_analise['VENDA_VALOR'],
            bins=bins,
            labels=['Vendas Baixas', 'Vendas Médias', 'Vendas Altas'],
            include_lowest=True
        )
    
    # Agregar dados por faixa
    df_grouped = df_analise.groupby('Faixa').agg({
        'VENDA_VALOR': 'sum',
        'MARGEM': 'mean'
    }).reset_index()
    
    # Ordenar por valor de venda
    df_grouped = df_grouped.sort_values('VENDA_VALOR', ascending=True)
    
    # Criar o gráfico
    fig = go.Figure()
    
    # Adicionar barras horizontais
    fig.add_trace(go.Bar(
        y=df_grouped['Faixa'],
        x=df_grouped['VENDA_VALOR'],
        orientation='h',
        text=df_grouped['VENDA_VALOR'].apply(lambda x: f'R$ {x:,.0f}'),
        textposition='auto',
        marker_color=['#ff9999', '#66b3ff', '#99ff99'],
        customdata=df_grouped['MARGEM'],
        hovertemplate="<br>".join([
            "%{y}",
            "Valor: R$ %{x:,.2f}",
            "Margem Média: %{customdata:.1%}",
            "<extra></extra>"
        ])
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Valor Total de Vendas (R$)',
        yaxis_title='Faixa de Venda',
        plot_bgcolor='white',
        height=400,
        showlegend=False,
        xaxis=dict(
            tickformat='R$ ,.0f',
            showgrid=True,
            gridcolor='lightgray'
        ),
        bargap=0.3
    )
    
    return fig

def carregar_dados():
    """Carrega e prepara os dados das bases de vendas e clientes."""
    try:
        # Carrega os arquivos diretamente
        clientes_df = pd.read_excel('bd_clientes.xlsx')
        vendas_df = pd.read_excel('bd_vendas.xlsx')
        
        # Padroniza os nomes das colunas
        clientes_df.columns = clientes_df.columns.str.upper()
        vendas_df.columns = vendas_df.columns.str.upper()
        
        # Converte margem para decimal
        if 'MARGEM' in vendas_df.columns:
            vendas_df['MARGEM'] = vendas_df['MARGEM'].str.rstrip('%').astype('float') / 100.0
            
        # Verifica qual nome da coluna de subcategoria está presente
        if 'SUBCATEGORIA_SKU' in vendas_df.columns:
            vendas_df = vendas_df.rename(columns={'SUBCATEGORIA_SKU': 'SUBCATEGORIA'})
        
        # Merge dos dataframes
        df_completo = pd.merge(vendas_df, clientes_df[['ID_CLIENTE', 'CANAL']], 
                              on='ID_CLIENTE', how='left')
        
        return df_completo
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return None

def calcular_score(df, grupo):
    """Calcula o score composto para cada grupo."""
    # Primeiro, fazemos o agrupamento para calcular as métricas agregadas
    df_grouped = df.groupby(grupo).agg({
        'VENDA_VALOR': 'sum',
        'ID_CLIENTE': 'nunique',
        'MARGEM': 'mean'
    }).reset_index()
    
    # Normalização das métricas
    df_norm = df_grouped.copy()
    
    # Faturamento (VENDA_VALOR)
    min_val = df_norm['VENDA_VALOR'].min()
    max_val = df_norm['VENDA_VALOR'].max()
    if max_val > min_val:
        df_norm['FATURAMENTO_NORM'] = (df_norm['VENDA_VALOR'] - min_val) / (max_val - min_val)
    else:
        df_norm['FATURAMENTO_NORM'] = 1.0
    
    # Número de Clientes
    min_val = df_norm['ID_CLIENTE'].min()
    max_val = df_norm['ID_CLIENTE'].max()
    if max_val > min_val:
        df_norm['N_CLIENTES_NORM'] = (df_norm['ID_CLIENTE'] - min_val) / (max_val - min_val)
    else:
        df_norm['N_CLIENTES_NORM'] = 1.0
    
    # Margem
    min_val = df_norm['MARGEM'].min()
    max_val = df_norm['MARGEM'].max()
    if max_val > min_val:
        df_norm['MARGEM_NORM'] = (df_norm['MARGEM'] - min_val) / (max_val - min_val)
    else:
        df_norm['MARGEM_NORM'] = 1.0
    
    # Cálculo do score
    df_norm['SCORE'] = (
        df_norm['FATURAMENTO_NORM'] * 0.4 +
        df_norm['N_CLIENTES_NORM'] * 0.3 +
        df_norm['MARGEM_NORM'] * 0.3
    )
    
    return df_norm

def main():
    # Título e logo
    col_logo, col_title = st.columns([1, 4])
    
    with col_logo:
        if os.path.exists('images.png'):
            image = Image.open('images.png')
            st.image(image, width=150)
    
    with col_title:
        st.title("Análise de Portfolio - MAIS MERCANTIL")
        st.markdown("*Recomendação inteligente de produtos por canal*")
    
    # Carrega dados
    df = carregar_dados()
    if df is None:
        return
        
    # Verifica se as colunas necessárias existem
    required_columns = ['CANAL', 'VENDA_VALOR', 'ID_CLIENTE', 'MARGEM']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"❌ Colunas obrigatórias ausentes no arquivo: {', '.join(missing_columns)}")
        st.markdown("""
        ℹ️ O arquivo deve conter as seguintes colunas:
        - CANAL: Canal de vendas
        - VENDA_VALOR: Valor da venda
        - ID_CLIENTE: Identificador do cliente
        - MARGEM: Margem de lucro
        """)
        return
        
    # Verifica se existe pelo menos uma das colunas de subcategoria
    if 'SUBCATEGORIA' not in df.columns and 'SUBCATEGORIA_SKU' not in df.columns:
        st.error("❌ Coluna de subcategoria não encontrada!")
        st.markdown("""
        ℹ️ O arquivo deve conter uma das seguintes colunas:
        - SUBCATEGORIA
        - SUBCATEGORIA_SKU
        """)
        return
    
    # Sidebar para filtros
    with st.sidebar:
        st.header("📊 Filtros de Análise")
        st.markdown("---")
        canal_selecionado = st.selectbox(
            "Selecione o Canal de Vendas",
            options=sorted(df['CANAL'].unique())
        )
        
        st.markdown("---")
        st.markdown("""
        ### 📈 Metodologia de Score
        
        O score é calculado considerando:
        - 🎯 Faturamento (40%)
        - 👥 Popularidade (30%)
        - 💰 Margem (30%)
        """)
    
    # Filtra dados pelo canal
    df_canal = df[df['CANAL'] == canal_selecionado]
    
    # Layout em colunas para KPIs
    st.markdown("### 📊 Visão Geral do Canal")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "💰 Faturamento Total",
            formatar_valor(df_canal['VENDA_VALOR'].sum())
        )
    with col2:
        st.metric(
            "👥 Número de Clientes",
            f"{df_canal['ID_CLIENTE'].nunique():,}"
        )
    with col3:
        st.metric(
            "📈 Margem Média",
            f"{df_canal['MARGEM'].mean():.1%}"
        )
    
    st.markdown("---")
    
    # Top 5 Subcategorias
    st.header("🏆 Top 5 Subcategorias Recomendadas")
    
    # Calcula scores para subcategorias
    subcategorias_score = calcular_score(df_canal, 'SUBCATEGORIA')
    
    # Garante que temos pelo menos algumas subcategorias
    if len(subcategorias_score) == 0:
        st.warning("Não há subcategorias disponíveis para este canal.")
        return
    
    # Seleciona top 5
    top5_subcategorias = subcategorias_score.nlargest(5, 'SCORE')
    
    # Cria o gráfico de barras
    fig_top5 = criar_grafico_barras(
        top5_subcategorias,
        x='SUBCATEGORIA',
        y='SCORE',
        title='Top 5 Subcategorias por Score'
    )
    
    st.plotly_chart(fig_top5, use_container_width=True)
    
    # Mostra tabela com detalhes das top 5 subcategorias
    st.subheader("📋 Detalhamento das Top 5 Subcategorias")
    top5_display = top5_subcategorias.copy()
    top5_display['Valor Total'] = top5_display['VENDA_VALOR'].apply(formatar_valor)
    top5_display['Margem Média'] = top5_display['MARGEM'].apply(lambda x: f"{x:.1%}")
    top5_display['Qtd. Clientes'] = top5_display['ID_CLIENTE']
    top5_display['Score Final'] = top5_display['SCORE'].apply(lambda x: f"{x:.3f}")
    
    st.dataframe(
        top5_display[['SUBCATEGORIA', 'Valor Total', 'Qtd. Clientes', 'Margem Média', 'Score Final']].rename(columns={
            'SUBCATEGORIA': 'Subcategoria'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Análise detalhada das subcategorias
    st.markdown("---")
    st.header("📊 Análise Detalhada por Subcategoria")
    
    subcategoria_selecionada = st.selectbox(
        "Escolha uma subcategoria para análise aprofundada:",
        options=top5_subcategorias['SUBCATEGORIA'].tolist(),
        key='subcategoria_selector'
    )
    
    if subcategoria_selecionada:
        # Dados da subcategoria selecionada
        df_subcategoria = df_canal[df_canal['SUBCATEGORIA'] == subcategoria_selecionada].copy()
        
        if not df_subcategoria.empty:
            # Métricas da subcategoria selecionada
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "💰 Faturamento da Subcategoria",
                    formatar_valor(df_subcategoria['VENDA_VALOR'].sum())
                )
            with col2:
                st.metric(
                    "👥 Clientes na Subcategoria",
                    f"{df_subcategoria['ID_CLIENTE'].nunique():,}"
                )
            with col3:
                st.metric(
                    "📈 Margem Média",
                    f"{df_subcategoria['MARGEM'].mean():.1%}"
                )
            
            # Gráfico de dispersão Margem x Faturamento
            fig_scatter = criar_grafico_scatter(
                df_subcategoria,
                x='MARGEM',
                y='VENDA_VALOR',
                color='MARGEM',
                title='Análise de Margem x Faturamento'
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Gráfico detalhado da subcategoria
            fig_detalhado = criar_grafico_detalhado(
                df_subcategoria,
                title='Análise Detalhada da Subcategoria'
            )
            
            st.plotly_chart(fig_detalhado, use_container_width=True)

if __name__ == "__main__":
    main()
