"""
========================================================================
Projeto: Dashboard de Análise de Portfolio - MAIS MERCANTIL
Desenvolvido por: Ronaldo Pereira
Data: 12 de Dezembro de 2024
Empresa: Zeta Dados

Descrição:
-----------
Dashboard interativo para análise do portfolio de produtos da MAIS MERCANTIL.
Metodologia baseada em score composto que considera:
- Faturamento (40%): Impacto direto no resultado financeiro
- Popularidade (30%): Número de clientes únicos
- Margem (30%): Lucratividade do produto

Funcionalidades:
---------------
- Visualização interativa de dados
- Filtros por canal e subcategoria
- Análise detalhada de SKUs
- Métricas em tempo real
- Score composto para avaliação

Tecnologias utilizadas:
---------------------
- Python 3.9
- Dash
- Plotly
- Pandas
- NumPy

Última atualização: 12/12/2024
========================================================================
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc

# Cores da Zeta Dados
ZETA_COLORS = {
    'primary': '#1A237E',    # Azul escuro
    'secondary': '#42A5F5',  # Azul claro
    'accent': '#4DB6AC',     # Verde água
    'white': '#FFFFFF',      # Branco
    'text': '#666666',       # Cinza para texto
    'background': '#F5F7FA', # Cinza claro para fundo
    'success': '#4CAF50',    # Verde para indicadores positivos
    'warning': '#FFC107',    # Amarelo para alertas
    'danger': '#F44336',     # Vermelho para indicadores negativos
    'light_gray': '#D3D3D3', # Cinza claro
    'dark_gray': '#333333',  # Cinza escuro
    'light_blue': '#ADD8E6', # Azul claro
    'dark_blue': '#03055B'   # Azul escuro
}

# Estilo global
GLOBAL_STYLE = {
    'backgroundColor': ZETA_COLORS['background'],
    'color': ZETA_COLORS['text'],
    'fontFamily': 'Arial, sans-serif'
}

CARD_STYLE = {
    'backgroundColor': ZETA_COLORS['white'],
    'borderRadius': '10px',
    'padding': '20px',
    'marginBottom': '20px',
    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
}

# Inicializa o app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Análise de Portfolio - MAIS MERCANTIL",
    suppress_callback_exceptions=True
)

def carregar_dados():
    """Carrega e prepara os dados das bases de vendas e clientes."""
    # Carrega as bases de dados
    clientes_df = pd.read_excel('bd_clientes.xlsx')
    vendas_df = pd.read_excel('bd_vendas.xlsx')
    
    # Padroniza os nomes das colunas para maiúsculas
    clientes_df.columns = clientes_df.columns.str.upper()
    vendas_df.columns = vendas_df.columns.str.upper()
    
    # Converte a coluna MARGEM de percentual para decimal
    vendas_df['MARGEM'] = vendas_df['MARGEM'].str.rstrip('%').astype('float') / 100.0
    
    # Merge dos dataframes para incluir o canal
    vendas_df = pd.merge(vendas_df, clientes_df[['ID_CLIENTE', 'CANAL']], on='ID_CLIENTE', how='left')
    
    # Debug: mostrar canais disponíveis
    print("\nCanais disponíveis:")
    print(sorted(vendas_df['CANAL'].unique()))
    
    return clientes_df, vendas_df

def calcular_metricas_subcategoria(vendas_df):
    """Calcula métricas agregadas por subcategoria e canal."""
    metricas = vendas_df.groupby(['CANAL', 'SUBCATEGORIA_SKU']).agg({
        'ID_SKU': 'nunique',
        'ID_CLIENTE': 'nunique',
        'VENDA_VALOR': 'sum',
        'MARGEM': 'mean'
    }).reset_index()
    
    # Normalização das métricas por canal
    for canal in metricas['CANAL'].unique():
        mask = metricas['CANAL'] == canal
        for col in ['ID_SKU', 'ID_CLIENTE', 'VENDA_VALOR', 'MARGEM']:
            min_val = metricas.loc[mask, col].min()
            max_val = metricas.loc[mask, col].max()
            if max_val > min_val:
                metricas.loc[mask, f'{col}_NORM'] = (metricas.loc[mask, col] - min_val) / (max_val - min_val)
            else:
                metricas.loc[mask, f'{col}_NORM'] = 1.0
    
    # Score composto com pesos definidos na metodologia
    metricas['SCORE'] = (
        metricas['VENDA_VALOR_NORM'] * 0.4 +  # Faturamento: 40%
        metricas['ID_CLIENTE_NORM'] * 0.3 +   # Popularidade: 30%
        metricas['MARGEM_NORM'] * 0.3         # Margem: 30%
    )
    
    return metricas

# Carrega os dados
clientes_df, vendas_df = carregar_dados()
metricas_df = calcular_metricas_subcategoria(vendas_df)

# Layout do dashboard
app.layout = dbc.Container([
    # Header com logo e título
    dbc.Row([
        dbc.Col([
            html.Img(src='assets/images.png', style={'height': '80px'}),
        ], width=2),
        dbc.Col([
            html.H1(
                "Dashboard - Análise de Portfolio MAIS MERCANTIL",
                style={
                    'color': ZETA_COLORS['primary'],
                    'paddingTop': '20px'
                }
            ),
            html.P([
                "Análise por canal de distribuição | ",
                "Score composto: ",
                html.Span("Faturamento (40%)", style={'color': ZETA_COLORS['success']}),
                " | ",
                html.Span("Popularidade (30%)", style={'color': ZETA_COLORS['accent']}),
                " | ",
                html.Span("Margem (30%)", style={'color': ZETA_COLORS['warning']})
            ], style={'color': ZETA_COLORS['text']})
        ], width=10)
    ], className='mb-4'),
    
    # Filtros
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Seleção de Canal", style={'color': ZETA_COLORS['primary']}),
                    html.P("Selecione o canal para análise detalhada:", style={'color': ZETA_COLORS['text']}),
                    dcc.Dropdown(
                        id='canal-dropdown',
                        options=[{'label': canal, 'value': canal} for canal in sorted(metricas_df['CANAL'].unique())],
                        value=sorted(metricas_df['CANAL'].unique())[0],
                        style={'marginBottom': '10px'}
                    )
                ])
            ], style=CARD_STYLE)
        ])
    ]),
    
    # KPIs principais
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("💰 Faturamento Total", className="card-title", style={'color': ZETA_COLORS['primary']}),
                    html.Div(id='kpi-faturamento', className="display-4"),
                    html.P("40% do score composto", style={'color': ZETA_COLORS['success']})
                ])
            ], style=CARD_STYLE)
        ]),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("👥 Total de Clientes", className="card-title", style={'color': ZETA_COLORS['primary']}),
                    html.Div(id='kpi-clientes', className="display-4"),
                    html.P("30% do score composto", style={'color': ZETA_COLORS['accent']})
                ])
            ], style=CARD_STYLE)
        ]),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📈 Margem Média", className="card-title", style={'color': ZETA_COLORS['primary']}),
                    html.Div(id='kpi-margem', className="display-4"),
                    html.P("30% do score composto", style={'color': ZETA_COLORS['warning']})
                ])
            ], style=CARD_STYLE)
        ])
    ]),
    
    # Gráficos principais
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🏆 Top 5 Subcategorias", style={'color': ZETA_COLORS['primary']}),
                    html.P([
                        "Ranking das 5 melhores subcategorias baseado no score composto. ",
                        "As linhas mostram a contribuição de cada componente para o score final."
                    ], style={'color': ZETA_COLORS['text']}),
                    dcc.Graph(id='graph-top5')
                ])
            ], style=CARD_STYLE)
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📊 Análise Margem x Faturamento", style={'color': ZETA_COLORS['primary']}),
                    html.P([
                        "Visualização da relação entre margem e faturamento. ",
                        "O tamanho dos pontos representa o número de clientes e as cores indicam o quartil do score."
                    ], style={'color': ZETA_COLORS['text']}),
                    dcc.Graph(id='graph-scatter')
                ])
            ], style=CARD_STYLE)
        ], width=6)
    ]),
    
    # Tabela detalhada
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🔍 Top 10 SKUs por Subcategoria", style={'color': ZETA_COLORS['primary']}),
                    html.P([
                        "Selecione uma subcategoria para ver os 10 melhores SKUs, ",
                        "ordenados pelo mesmo score composto usado na análise."
                    ], style={'color': ZETA_COLORS['text']}),
                    dcc.Dropdown(
                        id='subcategoria-dropdown',
                        style={'marginBottom': '20px'}
                    ),
                    dcc.Graph(id='table-skus')
                ])
            ], style=CARD_STYLE)
        ])
    ]),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.Hr(),
            html.P([
                "Dashboard desenvolvido por Ronaldo Pereira | ",
                html.A("Zeta Dados", href="#", style={'color': ZETA_COLORS['primary']}),
                " | Dezembro 2024"
            ], style={
                'textAlign': 'center',
                'color': ZETA_COLORS['text'],
                'padding': '20px'
            })
        ])
    ])
], fluid=True, style=GLOBAL_STYLE)

# Callbacks
@app.callback(
    [Output('kpi-faturamento', 'children'),
     Output('kpi-clientes', 'children'),
     Output('kpi-margem', 'children')],
    Input('canal-dropdown', 'value')
)
def update_kpis(canal):
    """Atualiza os KPIs com base no canal selecionado."""
    df_canal = vendas_df[vendas_df['CANAL'] == canal]
    
    faturamento = df_canal['VENDA_VALOR'].sum()
    clientes = df_canal['ID_CLIENTE'].nunique()
    margem = df_canal['MARGEM'].mean()
    
    return [
        f"R$ {faturamento:,.2f}",
        f"{clientes:,}",
        f"{margem:.1%}"
    ]

@app.callback(
    Output('subcategoria-dropdown', 'options'),
    Output('subcategoria-dropdown', 'value'),
    Input('canal-dropdown', 'value')
)
def update_subcategoria_options(canal):
    """Atualiza as opções do dropdown de subcategorias."""
    subcategorias = sorted(vendas_df[vendas_df['CANAL'] == canal]['SUBCATEGORIA_SKU'].unique())
    options = [{'label': sub, 'value': sub} for sub in subcategorias]
    value = subcategorias[0] if subcategorias else None
    return options, value

@app.callback(
    Output('graph-top5', 'figure'),
    Input('canal-dropdown', 'value')
)
def update_top5_graph(canal):
    """Atualiza o gráfico de top 5 subcategorias."""
    df_canal = metricas_df[metricas_df['CANAL'] == canal].sort_values('SCORE', ascending=False).head(5)
    
    fig = go.Figure()
    
    # Barra principal - Score total
    fig.add_trace(go.Bar(
        name='Score Total',
        x=df_canal['SUBCATEGORIA_SKU'],
        y=df_canal['SCORE'],
        marker_color=ZETA_COLORS['primary'],
        opacity=0.7
    ))
    
    # Linhas para cada componente do score
    fig.add_trace(go.Scatter(
        name='Faturamento (40%)',
        x=df_canal['SUBCATEGORIA_SKU'],
        y=df_canal['VENDA_VALOR_NORM'] * 0.4,
        mode='lines+markers',
        line=dict(color=ZETA_COLORS['success'], width=2),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        name='Popularidade (30%)',
        x=df_canal['SUBCATEGORIA_SKU'],
        y=df_canal['ID_CLIENTE_NORM'] * 0.3,
        mode='lines+markers',
        line=dict(color=ZETA_COLORS['accent'], width=2),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        name='Margem (30%)',
        x=df_canal['SUBCATEGORIA_SKU'],
        y=df_canal['MARGEM_NORM'] * 0.3,
        mode='lines+markers',
        line=dict(color=ZETA_COLORS['warning'], width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f'Top 5 Subcategorias - {canal}',
        xaxis_title='Subcategoria',
        yaxis_title='Score Composto',
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

@app.callback(
    Output('graph-scatter', 'figure'),
    [Input('canal-dropdown', 'value')]
)
def update_scatter_graph(canal):
    """Atualiza o gráfico de dispersão Margem x Faturamento."""
    df_canal = metricas_df[metricas_df['CANAL'] == canal]
    
    # Normalizar o tamanho dos pontos
    size_norm = (df_canal['ID_CLIENTE'] - df_canal['ID_CLIENTE'].min()) / \
                (df_canal['ID_CLIENTE'].max() - df_canal['ID_CLIENTE'].min()) * 40 + 10
    
    # Calcular quartis para coloração
    df_canal['SCORE_QUARTILE'] = pd.qcut(df_canal['SCORE'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
    
    color_map = {
        'Q1': ZETA_COLORS['danger'],
        'Q2': ZETA_COLORS['warning'],
        'Q3': ZETA_COLORS['accent'],
        'Q4': ZETA_COLORS['success']
    }
    
    fig = go.Figure()
    
    for quartile in ['Q4', 'Q3', 'Q2', 'Q1']:
        mask = df_canal['SCORE_QUARTILE'] == quartile
        df_quartile = df_canal[mask]
        
        fig.add_trace(go.Scatter(
            x=df_quartile['VENDA_VALOR'],
            y=df_quartile['MARGEM'],
            mode='markers',
            name=f'Score {quartile}',
            marker=dict(
                size=size_norm[mask],
                color=color_map[quartile],
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            text=df_quartile['SUBCATEGORIA_SKU'],
            hovertemplate="<b>%{text}</b><br>" +
                         "Faturamento: R$ %{x:,.2f}<br>" +
                         "Margem: %{y:.1%}<br>" +
                         "Clientes: %{marker.size:.0f}<br>" +
                         "<extra></extra>"
        ))
    
    # Adicionar linhas de média
    fig.add_hline(y=df_canal['MARGEM'].mean(), line_dash="dash", line_color=ZETA_COLORS['primary'],
                  annotation_text="Margem Média", annotation_position="bottom right")
    fig.add_vline(x=df_canal['VENDA_VALOR'].mean(), line_dash="dash", line_color=ZETA_COLORS['primary'],
                  annotation_text="Faturamento Médio", annotation_position="top right")
    
    fig.update_layout(
        title=f'Análise Margem x Faturamento - {canal}',
        xaxis_title='Faturamento (R$)',
        yaxis_title='Margem (%)',
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Formatação dos eixos
    fig.update_xaxes(tickformat=",.0f", tickprefix="R$ ")
    fig.update_yaxes(tickformat=".1%")
    
    return fig

@app.callback(
    Output('table-skus', 'figure'),
    [Input('canal-dropdown', 'value'),
     Input('subcategoria-dropdown', 'value')]
)
def update_skus_table(canal, subcategoria):
    """Atualiza a tabela de SKUs com informações detalhadas."""
    if not subcategoria:
        return go.Figure()
    
    # Filtrar dados
    mask = (vendas_df['CANAL'] == canal) & (vendas_df['SUBCATEGORIA_SKU'] == subcategoria)
    df_skus = vendas_df[mask].groupby('ID_SKU').agg({
        'VENDA_VALOR': 'sum',
        'MARGEM': 'mean',
        'ID_CLIENTE': 'nunique'
    }).reset_index()
    
    # Normalizar métricas
    for col in ['VENDA_VALOR', 'MARGEM', 'ID_CLIENTE']:
        min_val = df_skus[col].min()
        max_val = df_skus[col].max()
        if max_val > min_val:
            df_skus[f'{col}_NORM'] = (df_skus[col] - min_val) / (max_val - min_val)
        else:
            df_skus[f'{col}_NORM'] = 1.0
    
    # Calcular score
    df_skus['SCORE'] = (
        df_skus['VENDA_VALOR_NORM'] * 0.4 +  # Faturamento: 40%
        df_skus['ID_CLIENTE_NORM'] * 0.3 +   # Popularidade: 30%
        df_skus['MARGEM_NORM'] * 0.3         # Margem: 30%
    )
    
    # Ordenar e pegar top 10
    df_skus = df_skus.nlargest(10, 'SCORE')
    
    # Criar tabela
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>SKU</b>', '<b>Score</b>', '<b>Faturamento</b>', '<b>Margem</b>', '<b>Clientes</b>'],
            fill_color=ZETA_COLORS['primary'],
            align=['left', 'center', 'right', 'right', 'right'],
            font=dict(color='white', size=12),
            height=40
        ),
        cells=dict(
            values=[
                df_skus['ID_SKU'],
                df_skus['SCORE'].apply(lambda x: f"{x:.2f}"),
                df_skus['VENDA_VALOR'].apply(lambda x: f"R$ {x:,.2f}"),
                df_skus['MARGEM'].apply(lambda x: f"{x:.1%}"),
                df_skus['ID_CLIENTE'].apply(lambda x: f"{int(x):,}")
            ],
            fill_color=[
                [ZETA_COLORS['white']]*10,
                [ZETA_COLORS['background']]*10,
                [ZETA_COLORS['white']]*10,
                [ZETA_COLORS['background']]*10,
                [ZETA_COLORS['white']]*10
            ],
            align=['left', 'center', 'right', 'right', 'right'],
            font=dict(color=ZETA_COLORS['text'], size=11),
            height=30
        )
    )])
    
    fig.update_layout(
        title=f'Top 10 SKUs - {subcategoria}',
        margin=dict(l=10, r=10, t=30, b=10),
        height=400
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
