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
    h1 {
        color: #333333;
        font-weight: 600;
    }
    h2 {
        color: #333333;
        font-weight: 500;
    }
    h3 {
        color: #333333;
        font-weight: 500;
    }
    p {
        color: #333333;
    }
    .stMarkdown {
        color: #333333;
    }
    .metric-label {
        color: #333333 !important;
        font-weight: 500;
    }
    .metric-value {
        color: #333333 !important;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] > div {
        color: #333333;
        font-weight: 600;
    }
    div[data-testid="stMetricLabel"] > div {
        color: #333333;
    }
    /* Ajustes específicos para a sidebar */
    .sidebar .sidebar-content {
        background-color: #F8F9FA;
    }
    .sidebar h1, .sidebar h2, .sidebar h3, .sidebar p {
        color: #333333 !important;
    }
    /* Ajustes para links e texto selecionado */
    a {
        color: #1A73E8;
    }
    ::selection {
        background: #E8F0FE;
        color: #333333;
    }
    /* Ajustes para elementos do Streamlit */
    .stSelectbox label {
        color: #333333 !important;
    }
    .stSelectbox div[data-baseweb="select"] {
        background-color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# Configurações de tema para os gráficos
CHART_THEME = {
    'bgcolor': '#FFFFFF',
    'font_color': '#333333',
    'title_color': '#333333',
    'grid_color': '#E0E0E0',
    'axis_color': '#757575'
}

def criar_grafico_barras(df, x, y, title):
    """Cria gráfico de barras com estilo padronizado."""
    # Definir uma paleta de cores mais distintas
    colors = ['#4CAF50', '#2196F3', '#FFC107', '#E91E63', '#9C27B0']
    
    # Criar o gráfico com mais informações no hover
    fig = px.bar(
        df, 
        x=x, 
        y=y, 
        title=title,
        color=x,  # Usar subcategoria para colorir
        color_discrete_sequence=colors,
        text=y,  # Mostrar valores nas barras
        hover_data={
            'VENDA_VALOR': ':,.2f',
            'MARGEM': ':.1%',
            'ID_CLIENTE': ':,d'
        }
    )
    
    # Atualizar o layout com mais customizações
    fig.update_layout(
        plot_bgcolor=CHART_THEME['bgcolor'],
        paper_bgcolor=CHART_THEME['bgcolor'],
        font={'color': CHART_THEME['font_color'], 'size': 12},
        title={
            'font': {'color': CHART_THEME['title_color'], 'size': 16},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis={
            'gridcolor': CHART_THEME['grid_color'],
            'color': CHART_THEME['axis_color'],
            'tickangle': 45,
            'title': None  # Remover título do eixo x
        },
        yaxis={
            'gridcolor': CHART_THEME['grid_color'],
            'color': CHART_THEME['axis_color'],
            'title': 'Score'
        },
        showlegend=False,
        margin=dict(t=60, b=120, l=60, r=20)  # Ajustar margens
    )
    
    # Atualizar o texto nas barras
    fig.update_traces(
        texttemplate='%{text:.2f}',
        textposition='outside',
        textfont=dict(size=12, color=CHART_THEME['font_color'])
    )
    
    return fig

def criar_grafico_scatter(df, x, y, color, title):
    """Cria gráfico de dispersão com estilo padronizado."""
    # Criar o gráfico com mais informações
    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        color_continuous_scale='viridis',
        size='VENDA_VALOR',  # Tamanho dos pontos baseado no valor de venda
        hover_data={
            'NOME_SKU': True,
            'VENDA_VALOR': ':,.2f',
            'MARGEM': ':.1%',
            'ID_CLIENTE': ':,d'
        },
        labels={
            'VENDA_VALOR': 'Valor de Venda (R$)',
            'MARGEM': 'Margem (%)',
            'NOME_SKU': 'Produto'
        }
    )
    
    # Atualizar o layout
    fig.update_layout(
        plot_bgcolor=CHART_THEME['bgcolor'],
        paper_bgcolor=CHART_THEME['bgcolor'],
        font={'color': CHART_THEME['font_color'], 'size': 12},
        title={
            'font': {'color': CHART_THEME['title_color'], 'size': 16},
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis={
            'gridcolor': CHART_THEME['grid_color'],
            'color': CHART_THEME['axis_color'],
            'title': 'Margem (%)',
            'tickformat': '.1%'
        },
        yaxis={
            'gridcolor': CHART_THEME['grid_color'],
            'color': CHART_THEME['axis_color'],
            'title': 'Valor de Venda (R$)',
            'tickformat': ',.0f'
        },
        coloraxis_colorbar={
            'title': 'Margem',
            'tickformat': '.1%'
        },
        margin=dict(t=60, b=60, l=80, r=20)
    )
    
    return fig

def carregar_dados():
    """Carrega e prepara os dados das bases de vendas e clientes."""
    try:
        # Usar st.file_uploader para permitir upload dos arquivos
        st.sidebar.markdown("### 📂 Upload de Dados")
        
        uploaded_vendas = st.sidebar.file_uploader(
            "Upload da base de vendas (Excel)",
            type=['xlsx'],
            key='vendas'
        )
        
        uploaded_clientes = st.sidebar.file_uploader(
            "Upload da base de clientes (Excel)",
            type=['xlsx'],
            key='clientes'
        )
        
        if uploaded_vendas is None or uploaded_clientes is None:
            st.warning("⚠️ Por favor, faça o upload dos arquivos de vendas e clientes para continuar.")
            return None
            
        # Ler os dados dos arquivos enviados
        vendas_df = pd.read_excel(uploaded_vendas)
        clientes_df = pd.read_excel(uploaded_clientes)
        
        # Padroniza os nomes das colunas
        clientes_df.columns = clientes_df.columns.str.upper()
        vendas_df.columns = vendas_df.columns.str.upper()
        
        # Converte margem para decimal
        if 'MARGEM' in vendas_df.columns:
            vendas_df['MARGEM'] = vendas_df['MARGEM'].str.rstrip('%').astype('float') / 100.0
        
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

def formatar_valor(valor):
    """Formata valores monetários."""
    return f"R$ {valor:,.2f}"

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
    
    # Calcula scores para todas as subcategorias
    subcategorias_score = calcular_score(df_canal, 'SUBCATEGORIA_SKU')
    
    # Garante que temos pelo menos algumas subcategorias
    if len(subcategorias_score) == 0:
        st.warning("Não há subcategorias disponíveis para este canal.")
        return
    
    # Seleciona top 5
    top5_subcategorias = subcategorias_score.nlargest(5, 'SCORE')
    
    # Adicionar colunas formatadas para o hover
    top5_subcategorias['MARGEM'] = top5_subcategorias['MARGEM'] / 100  # Converter para decimal para formatação
    
    # Cria o gráfico de barras
    fig_top5 = criar_grafico_barras(
        top5_subcategorias,
        x='SUBCATEGORIA_SKU',
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
        top5_display[['SUBCATEGORIA_SKU', 'Valor Total', 'Qtd. Clientes', 'Margem Média', 'Score Final']].rename(columns={
            'SUBCATEGORIA_SKU': 'Subcategoria'
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Análise detalhada das subcategorias
    st.markdown("---")
    st.header("📊 Análise Detalhada por Subcategoria")
    
    if len(top5_subcategorias) > 0:
        subcategoria_selecionada = st.selectbox(
            "Escolha uma subcategoria para análise aprofundada:",
            options=top5_subcategorias['SUBCATEGORIA_SKU'].tolist(),
            key='subcategoria_selector'
        )
        
        # Dados da subcategoria selecionada
        df_subcategoria = df_canal[df_canal['SUBCATEGORIA_SKU'] == subcategoria_selecionada].copy()
        
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
            df_scatter = df_subcategoria.copy()
            df_scatter['MARGEM'] = df_scatter['MARGEM'] / 100  # Converter para decimal para formatação
            
            fig_scatter = criar_grafico_scatter(
                df_scatter,
                x='MARGEM',
                y='VENDA_VALOR',
                color='MARGEM',
                title=f"Análise de Produtos - {subcategoria_selecionada}"
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Top 10 SKUs
            st.markdown("---")
            st.header("🌟 Top 10 Produtos Recomendados")
            
            skus_score = calcular_score(df_subcategoria, 'ID_SKU')
            if not skus_score.empty:
                top10_skus = skus_score.nlargest(10, 'SCORE')
                
                # Adiciona nome do SKU à tabela
                top10_skus = pd.merge(
                    top10_skus,
                    df_subcategoria[['ID_SKU', 'NOME_SKU']].drop_duplicates(),
                    left_on='ID_SKU',
                    right_on='ID_SKU'
                )
                
                # Formata a tabela para exibição
                top10_skus_display = top10_skus.copy()
                top10_skus_display['Valor Total'] = top10_skus_display['VENDA_VALOR'].apply(formatar_valor)
                top10_skus_display['Margem'] = top10_skus_display['MARGEM'].apply(lambda x: f"{x:.1%}")
                top10_skus_display['Score'] = top10_skus_display['SCORE'].apply(lambda x: f"{x:.3f}")
                top10_skus_display['Qtd. Clientes'] = top10_skus_display['ID_CLIENTE']
                
                st.dataframe(
                    top10_skus_display[['NOME_SKU', 'Valor Total', 'Qtd. Clientes', 'Margem', 'Score']].rename(columns={
                        'NOME_SKU': 'Produto'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("Não há produtos disponíveis nesta subcategoria.")
        else:
            st.warning("Não há dados disponíveis para esta subcategoria.")
    else:
        st.warning("Não há subcategorias disponíveis para análise detalhada.")
    
    # Rodapé
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666666; padding: 20px;'>
            <p>Dashboard desenvolvido por Ronaldo Pereira | Zeta Dados</p>
            <p>Última atualização: Dezembro 2024</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
