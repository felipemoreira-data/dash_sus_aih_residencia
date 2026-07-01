import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from db_connect import (
    obter_opcoes_filtros,
    obter_dados_orcamento,
    obter_dados_pressao,
    obter_dados_cirurgias,
    obter_dados_mapa,
    LABELS_CIRURGICAS,
    LABELS_CIRURGICAS_VL,
)

# ===========================================================================
# GEOJSON LOCAL - CARREGAMENTO ÚNICO
# =======================================================================
with open('municipios_br.json', encoding='utf-8') as f: 
    GEOJSON_ESTADO = json.load(f)
    
for feature in GEOJSON_ESTADO['features']:
    cod = str(feature['properties']['codarea'])
    feature['properties']['codarea_6'] = cod[:6] # Remove dígito verificador
# =======================================================================

# ===========================================================================
# Inicialização do App
# ===========================================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
    title="BI — Produção Hospitalar SIH/SUS",
)

# ===========================================================================
# Pré-carregamento das opções de filtro
# ===========================================================================

try:
    opcoes = obter_opcoes_filtros()
except Exception as e:
    print(f"[AVISO] Falha ao carregar opções de filtro: {e}")
    opcoes = {"anos": [], "meses": [], "municipios": []}

# ===========================================================================
# Paleta de cores alinhada ao tema FLATLY
# ===========================================================================

COR_PRIMARIA  = "#2C3E50"   # azul-escuro FLATLY
COR_SECUNDARIA = "#18BC9C"  # verde-teal FLATLY
COR_PERIGO    = "#E74C3C"   # vermelho
COR_AVISO     = "#F39C12"   # laranja/amarelo
COR_INFO      = "#3498DB"   # azul claro
COR_CINZA     = "#95A5A6"
SEQUENCIA_BLOCOS = [COR_SECUNDARIA, COR_INFO, COR_AVISO, COR_PERIGO]

# ===========================================================================
# Componentes Reutilizáveis
# ===========================================================================

def cartao_kpi(titulo: str, valor_id: str, cor: str = COR_PRIMARIA) -> dbc.Card:
    """Retorna um card de KPI com título e valor dinâmico."""
    return dbc.Card(
        dbc.CardBody([
            html.P(titulo, className="text-muted mb-1",
                   style={"fontSize": "0.78rem", "fontWeight": "600",
                          "textTransform": "uppercase", "letterSpacing": "0.05em"}),
            html.H4(id=valor_id, children="—",
                    style={"color": cor, "fontWeight": "700", "marginBottom": 0}),
        ]),
        className="shadow-sm border-0 h-100",
        style={"borderRadius": "10px"},
    )


def spinner(children) -> dcc.Loading:
    """Envolve conteúdo em um spinner de carregamento padrão."""
    return dcc.Loading(type="circle", color=COR_SECUNDARIA, children=children)


# ===========================================================================
# Sidebar de Filtros
# ===========================================================================

sidebar = html.Div(
    [
        html.Div([
            html.Img(
                src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRCHHarE6sabOGPvflJlAnH2BDx8Hz3n_UQN06_xWDJ9BcHZhBrBrhKJlo&s=10",
                style={"width": "60px", "marginBottom": "10px"},
            ),
            html.H5("SIH / SUS", className="fw-bold mb-0", style={"color": COR_PRIMARIA}),
            html.Small("Produção Hospitalar", className="text-muted"),
        ], className="text-center mb-4"),

        html.Hr(),

        html.Label("Ano", className="fw-semibold small text-muted"),
        dcc.Dropdown(
            id="filtro-ano",
            options=opcoes["anos"],
            placeholder="Todos os anos",
            clearable=True,
            className="mb-3",
        ),

        html.Label("Mês", className="fw-semibold small text-muted"),
        dcc.Dropdown(
            id="filtro-mes",
            options=opcoes["meses"],
            placeholder="Todos os meses",
            clearable=True,
            className="mb-3",
        ),

        html.Label("Município", className="fw-semibold small text-muted"),
        dcc.Dropdown(
            id="filtro-municipio",
            options=opcoes["municipios"],
            placeholder="Todos os municípios",
            clearable=True,
            className="mb-3",
        ),

        html.Hr(),

        dbc.Button(
            [html.I(className="bi bi-arrow-clockwise me-2"), "Limpar Filtros"],
            id="btn-limpar",
            color="outline-secondary",
            size="sm",
            className="w-100 mb-2",
        ),

        html.Hr(),

        html.P(
            "As Autorizações de Internação Hospitalar (AIH) são consolidadas "
            "por local de residência do paciente.",
            className="text-muted",
            style={"fontSize": "0.75rem", "textAlign": "justify"},
        ),
    ],
    style={
        "position": "sticky",
        "top": "0",
        "height": "100vh",
        "overflowY": "auto",
        "padding": "1.5rem 1rem",
        "backgroundColor": "#f8f9fa",
        "borderRight": "1px solid #dee2e6",
    },
)

# ===========================================================================
# Abas
# ===========================================================================

# --- ABA 1: EFICIÊNCIA ORÇAMENTÁRIA ----------------------------------------
aba_orcamento = dbc.Container([
    # KPIs
    dbc.Row([
        dbc.Col(cartao_kpi("Valor Total Aprovado", "kpi-vl-total",  COR_PRIMARIA),   md=3),
        dbc.Col(cartao_kpi("Custos Clínicos",   "kpi-vl-03",     COR_SECUNDARIA), md=3),
        dbc.Col(cartao_kpi("Custos Cirúrgicos", "kpi-vl-04",     COR_AVISO),      md=3),
        dbc.Col(cartao_kpi("Outros Custos",     "kpi-vl-outros", COR_INFO),       md=3),
    ], className="mb-4 g-3"),

    # Gráficos
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Evolução Histórica do Gasto por Bloco", className="fw-semibold"),
                dbc.CardBody(spinner(dcc.Graph(id="graph-evolucao-orcamento", config={"displayModeBar": False}))),
            ], className="shadow-sm border-0"),
            md=7,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Distribuição dos Custos Cirúrgicos (Treemap)", className="fw-semibold"),
                dbc.CardBody(spinner(dcc.Graph(id="graph-treemap-orcamento", config={"displayModeBar": False}))),
            ], className="shadow-sm border-0"),
            md=5,
        ),
    ], className="g-3"),
], fluid=True, className="py-3")


# --- ABA 2: PRESSÃO ASSISTENCIAL -------------------------------------------
aba_pressao = dbc.Container([
    # KPIs
    dbc.Row([
        dbc.Col(cartao_kpi("Procedimentos Clínicos",  "kpi-qtd-03",   COR_PRIMARIA),   md=4),
        dbc.Col(cartao_kpi("Casos de Oncologia",      "kpi-qtd-0304", COR_PERIGO),     md=4),
        dbc.Col(cartao_kpi("Casos de Nefrologia",     "kpi-qtd-0305", COR_AVISO),      md=4),
    ], className="mb-4 g-3"),

    # Gráficos
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Pressão Assistencial por Município (Bubble Chart)", className="fw-semibold"),
                dbc.CardBody(spinner(dcc.Graph(id="graph-scatter-pressao", config={"displayModeBar": False}))),
            ], className="shadow-sm border-0"),
            md=6,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Evolução Temporal da Demanda Oncológica (Área)", className="fw-semibold"),
                dbc.CardBody(spinner(dcc.Graph(id="graph-area-oncologia", config={"displayModeBar": False}))),
            ], className="shadow-sm border-0"),
            md=6,
        ),
    ], className="g-3"),
], fluid=True, className="py-3")


# --- ABA 3: PRODUTIVIDADE CIRÚRGICA -----------------------------
aba_cirurgias = dbc.Container([
    # KPIs
    dbc.Row([
        dbc.Col(cartao_kpi("Total de Cirurgias",           "kpi-qtd-04",          COR_PRIMARIA),   md=4),
        dbc.Col(cartao_kpi("Média de Cirurgias / Mês",     "kpi-media-cirurgias", COR_SECUNDARIA), md=4),
        dbc.Col(cartao_kpi("Especialidade + Demandada",    "kpi-top-especialidade", COR_AVISO),    md=4),
    ], className="mb-4 g-3"),

    # Gráficos
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top 10 Municípios por Volume Cirúrgico", className="fw-semibold"),
                dbc.CardBody(spinner(dcc.Graph(id="graph-barras-cirurgias", config={"displayModeBar": False}))),
            ], className="shadow-sm border-0"),
            md=7,
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Alta Complexidade Cirúrgica — Circulatório & Oncologia", className="fw-semibold"),
                dbc.CardBody(spinner(dcc.Graph(id="graph-donut-cirurgias", config={"displayModeBar": False}))),
            ], className="shadow-sm border-0"),
            md=5,
        ),
    ], className="g-3"),
], fluid=True, className="py-3")


# --- ABA 4: VISÃO TERRITORIAL ---
aba_territorial = dbc.Container([
    dbc.Row([
        # Painel de controle do mapa
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Variável do Mapa", className="fw-semibold"),
                dbc.CardBody([
                    dcc.RadioItems(
                        id="seletor-mapa",
                        options=[
                            {"label": " Investimento Total (R$)",     "value": "vl_total"},
                            {"label": " Volume de Atendimentos",      "value": "qtd_total"},
                            {"label": " Concentração Oncológica",     "value": "qtd_0304"},
                        ],
                        value="vl_total",
                        labelStyle={"display": "block", "marginBottom": "12px",
                                    "cursor": "pointer", "fontSize": "0.9rem"},
                        inputStyle={"marginRight": "8px"},
                    ),
                    html.Hr(),
                    html.P(
                        "O mapa utiliza a coluna 'codigo_municipio_dv' (7 dígitos) "
                        "para cruzar com o arquivo GeoJSON.",
                        className="text-muted", style={"fontSize": "0.75rem"},
                    ),
                ]),
            ], className="shadow-sm border-0"),
        ], md=4),

        # Mapa coroplético
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(id="titulo-mapa", className="fw-semibold"),
                dbc.CardBody(spinner(dcc.Graph(
                    id="mapa-coropletico-sus",
                    config={"displayModeBar": True},
                    style={"height": "65vh"},
                ))),
            ], className="shadow-sm border-0"),
        ], md=8),
    ], className="g-3"),
], fluid=True, className="py-3")


# ======================
# Layout Principal
# ======================

TOPBAR_STYLE = {
    "backgroundColor": COR_PRIMARIA,
    "padding": "14px 28px",
    "marginBottom": "0",
}

app.layout = dbc.Container([

    # Top Bar
    dbc.Row(
        dbc.Col(
            html.Div([
                html.H4(
                    "BUSINESS INTELLIGENCE — PRODUÇÃO HOSPITALAR (SIH/SUS)",
                    style={"color": "#FFFFFF", "fontWeight": "700", "margin": 0, "fontSize": "1.1rem"},
                ),
                html.Small(
                    "Análise de Custos, Linhas de Cuidado e Alta Complexidade — FUNASA",
                    style={"color": "#BDC3C7"},
                ),
            ]),
            style=TOPBAR_STYLE,
        ),
        className="mb-0",
    ),

    # Corpo: Sidebar + Conteúdo
    dbc.Row([

        # Sidebar (2 colunas)
        dbc.Col(sidebar, xs=12, md=2, className="p-0"),

        # Área principal (10 colunas)
        dbc.Col([
            dcc.Tabs(
                id="tabs-main",
                value="aba-orcamento",
                className="mt-3",
                children=[
                    dcc.Tab(label="💰 Eficiência Orçamentária",  value="aba-orcamento",
                            className="custom-tab", selected_className="custom-tab--selected"),
                    dcc.Tab(label="🩺 Pressão Assistencial",     value="aba-pressao",
                            className="custom-tab", selected_className="custom-tab--selected"),
                    dcc.Tab(label="🔪 Produtividade Cirúrgica",  value="aba-cirurgias",
                            className="custom-tab", selected_className="custom-tab--selected"),
                    dcc.Tab(label="🗺️ Visão Territorial",        value="aba-territorial",
                            className="custom-tab", selected_className="custom-tab--selected"),
                ],
            ),
            html.Div(id="conteudo-aba", className="mt-2"),
        ], xs=12, md=10, style={"padding": "0 1.5rem"}),

    ], className="g-0"),

], fluid=True, style={"backgroundColor": "#F4F6F7", "minHeight": "100vh", "padding": 0})


# ==================
# CSS inline para as abas
# ===================

app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>BI — Produção Hospitalar SIH/SUS</title>
        {%favicon%}
        {%css%}
        <style>
            body { font-family: 'Segoe UI', Roboto, sans-serif; background-color: #F4F6F7; }
            .custom-tab {
                background-color: #ecf0f1 !important;
                color: #7f8c8d !important;
                border: none !important;
                padding: 10px 18px !important;
                font-size: 0.85rem;
                font-weight: 500;
                transition: background-color 0.2s ease, color 0.2s ease;
            }
            .custom-tab:hover { color: #2C3E50 !important; background-color: #dde1e4 !important; }
            .custom-tab--selected {
                background-color: #ffffff !important;
                color: #18BC9C !important;
                border-top: 3px solid #18BC9C !important;
                font-weight: 700;
            }
            .Select-control { border-radius: 6px !important; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""


# ========
# Utilitários de formatação
# ================

def fmt_brl(valor: float) -> str:
    """Formata um número como moeda brasileira."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(valor: float) -> str:
    """Formata um número inteiro com separador de milhar."""
    return f"{int(valor):,}".replace(",", ".")


# =======================
# Callback: Roteamento das Abas
# =======================

@app.callback(
    Output("conteudo-aba", "children"),
    Input("tabs-main", "value"),
)
def renderizar_aba(aba):
    mapa = {
        "aba-orcamento":   aba_orcamento,
        "aba-pressao":     aba_pressao,
        "aba-cirurgias":   aba_cirurgias,
        "aba-territorial": aba_territorial,
    }
    return mapa.get(aba, aba_orcamento)


# =======================
# Callback: Limpar Filtros
# =====================

@app.callback(
    Output("filtro-ano",       "value"),
    Output("filtro-mes",       "value"),
    Output("filtro-municipio", "value"),
    Input("btn-limpar",        "n_clicks"),
    prevent_initial_call=True,
)
def limpar_filtros(_):
    return None, None, None


# ====================
# Callback: ABA 1 — Eficiência Orçamentária
# ====================

@app.callback(
    Output("kpi-vl-total",           "children"),
    Output("kpi-vl-03",              "children"),
    Output("kpi-vl-04",              "children"),
    Output("kpi-vl-outros",          "children"),
    Output("graph-evolucao-orcamento","figure"),
    Output("graph-treemap-orcamento", "figure"),
    Input("filtro-ano",              "value"),
    Input("filtro-mes",              "value"),
    Input("filtro-municipio",        "value"),
)
def atualizar_orcamento(ano, mes, municipio):
    df = obter_dados_orcamento(ano, mes, municipio)

    if df.empty:
        fig_vazio = go.Figure()
        fig_vazio.update_layout(
            annotations=[{"text": "Sem dados para o filtro selecionado",
                          "x": 0.5, "y": 0.5, "showarrow": False}]
        )
        return "—", "—", "—", "—", fig_vazio, fig_vazio

    vl_total  = df["vl_total"].sum()
    vl_03     = df["vl_03"].sum()
    vl_04     = df["vl_04"].sum()
    vl_outros = df["vl_02"].sum() + df["vl_05"].sum()

    # --- Gráfico de Linhas: Evolução por Bloco ---
    fig_evolucao = go.Figure()
    blocos = [
        ("vl_total", "Total",     COR_PRIMARIA,   "dash"),
        ("vl_03",    "Clínico",   COR_SECUNDARIA, "solid"),
        ("vl_04",    "Cirúrgico", COR_AVISO,      "solid"),
        ("vl_02",    "Diagnóstico",COR_INFO,       "dot"),
        ("vl_05",    "Transplante",COR_PERIGO,     "dot"),
    ]
    for col, nome, cor, dash in blocos:
        fig_evolucao.add_trace(go.Scatter(
            x=df["periodo"], y=df[col].fillna(0),
            name=nome, mode="lines+markers",
            line=dict(color=cor, dash=dash, width=2),
            marker=dict(size=5),
        ))
    fig_evolucao.update_layout(
        template="plotly_white",
        legend=dict(orientation="h", y=-0.25),
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="Valor (R$)",
        xaxis_title="Período",
        hovermode="x unified",
    )

    # --- Treemap: Distribuição Cirúrgica ---
    cols_vl_circ = list(LABELS_CIRURGICAS_VL.keys())
    soma_circ = df[cols_vl_circ].sum()
    soma_circ = soma_circ[soma_circ > 0]

    if soma_circ.empty:
        fig_treemap = go.Figure()
        fig_treemap.update_layout(
            annotations=[{"text": "Sem custos cirúrgicos no período",
                          "x": 0.5, "y": 0.5, "showarrow": False}]
        )
    else:
        df_treemap = pd.DataFrame({
            "Especialidade": [LABELS_CIRURGICAS_VL[c] for c in soma_circ.index],
            "Valor":         soma_circ.values,
        })
        fig_treemap = px.treemap(
            df_treemap, path=["Especialidade"], values="Valor",
            color="Valor", color_continuous_scale="Teal",
        )
        fig_treemap.update_layout(
            template="plotly_white",
            margin=dict(l=5, r=5, t=5, b=5),
            coloraxis_showscale=False,
        )
        fig_treemap.update_traces(textinfo="label+percent root")

    return (
        fmt_brl(vl_total),
        fmt_brl(vl_03),
        fmt_brl(vl_04),
        fmt_brl(vl_outros),
        fig_evolucao,
        fig_treemap,
    )


# ===============
# Callback: ABA 2 — Pressão Assistencial
# ==============

@app.callback(
    Output("kpi-qtd-03",          "children"),
    Output("kpi-qtd-0304",        "children"),
    Output("kpi-qtd-0305",        "children"),
    Output("graph-scatter-pressao","figure"),
    Output("graph-area-oncologia", "figure"),
    Input("filtro-ano",            "value"),
    Input("filtro-mes",            "value"),
    Input("filtro-municipio",      "value"),
)
def atualizar_pressao(ano, mes, municipio):
    df = obter_dados_pressao(ano, mes, municipio)

    if df.empty:
        fig_vazio = go.Figure()
        fig_vazio.update_layout(
            annotations=[{"text": "Sem dados para o filtro selecionado",
                          "x": 0.5, "y": 0.5, "showarrow": False}]
        )
        return "—", "—", "—", fig_vazio, fig_vazio

    qtd_03   = df["qtd_03"].sum()
    qtd_0304 = df["qtd_0304"].sum()
    qtd_0305 = df["qtd_0305"].sum()

    # --- Scatter Plot: Pressão por Município ---
    df_mun = df.groupby("nome_municipio", as_index=False).agg({
        "qtd_0303":  "sum",
        "qtd_0304":  "sum",
        "qtd_0305":  "sum",
        "qtd_total": "sum",
    })
    df_mun["complexidade"] = df_mun["qtd_0304"] + df_mun["qtd_0305"]

    # #2: Plotly lança ValueError se size tiver valores 0 ou negativos.
    # clip(lower=1) garante que todas as bolhas fiquem visíveis.
    df_mun["qtd_total_plot"] = df_mun["qtd_total"].clip(lower=1)

    # #4: Limita a 100 municípios de maior volume para não travar o browser
    # com 5000+ pontos quando nenhum filtro está ativo.
    df_mun_plot = df_mun.nlargest(100, "qtd_total")

    fig_scatter = px.scatter(
        df_mun_plot,
        x="qtd_0303", y="complexidade",
        size="qtd_total_plot", size_max=55,
        color="qtd_total",
        color_continuous_scale="Teal",
        hover_name="nome_municipio",
        hover_data={"qtd_total_plot": False, "qtd_total": True},
        labels={
            "qtd_0303":      "Tratamentos Clínicos Gerais",
            "complexidade":  "Oncologia + Nefrologia",
            "qtd_total":     "Volume Total",
        },
        template="plotly_white",
    )
    fig_scatter.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
    )

    # --- Área: Evolução Temporal Oncológica ---
    # #3: sort_values garante ordenação cronológica correta após o groupby.
    df_temp = (
        df.groupby("periodo", as_index=False)
        .agg({"qtd_0304": "sum"})
        .sort_values("periodo")
    )
    fig_area = px.area(
        df_temp, x="periodo", y="qtd_0304",
        labels={"periodo": "Período", "qtd_0304": "Casos de Oncologia"},
        color_discrete_sequence=[COR_PERIGO],
        template="plotly_white",
    )
    fig_area.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    fig_area.update_traces(line_color=COR_PERIGO, fillcolor="rgba(231,76,60,0.15)")

    return (
        fmt_int(qtd_03),
        fmt_int(qtd_0304),
        fmt_int(qtd_0305),
        fig_scatter,
        fig_area,
    )


# ==========
# Callback: ABA 3 — Produtividade Cirúrgica
# ==========

@app.callback(
    Output("kpi-qtd-04",            "children"),
    Output("kpi-media-cirurgias",   "children"),
    Output("kpi-top-especialidade", "children"),
    Output("graph-barras-cirurgias","figure"),
    Output("graph-donut-cirurgias", "figure"),
    Input("filtro-ano",             "value"),
    Input("filtro-mes",             "value"),
    Input("filtro-municipio",       "value"),
)
def atualizar_cirurgias(ano, mes, municipio):
    df = obter_dados_cirurgias(ano, mes, municipio)

    if df.empty:
        fig_vazio = go.Figure()
        fig_vazio.update_layout(
            annotations=[{"text": "Sem dados para o filtro selecionado",
                          "x": 0.5, "y": 0.5, "showarrow": False}]
        )
        return "—", "—", "—", fig_vazio, fig_vazio

    qtd_04_total = df["qtd_04"].sum()

    # Média por município (proxy de "por mês" quando não há granularidade temporal)
    n_municipios   = max(df.shape[0], 1)
    media_cirug    = qtd_04_total / n_municipios

    # Especialidade mais demandada
    cols_qtd_circ = list(LABELS_CIRURGICAS.keys())
    soma_esp      = df[cols_qtd_circ].sum()
    top_col       = soma_esp.idxmax() if not soma_esp.empty else None
    top_label     = LABELS_CIRURGICAS.get(top_col, "N/D") if top_col else "N/D"

    # --- Barras Horizontais: Top 10 Municípios ---
    df_top10 = df.nlargest(10, "qtd_04")[["nome_municipio", "qtd_04"]].sort_values("qtd_04")
    fig_barras = px.bar(
        df_top10, x="qtd_04", y="nome_municipio", orientation="h",
        labels={"qtd_04": "Total de Cirurgias", "nome_municipio": "Município"},
        color="qtd_04", color_continuous_scale="Teal",
        template="plotly_white",
    )
    fig_barras.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
        yaxis_title="",
    )

    # --- Donut: Alta Complexidade (Circulatório + Oncologia) ---
    circ_sum  = df["qtd_0406"].sum()
    onco_sum  = df["qtd_0416"].sum()
    resto_sum = max(qtd_04_total - circ_sum - onco_sum, 0)

    fig_donut = go.Figure(go.Pie(
        labels=["Aparelho Circulatório", "Oncologia Cirúrgica", "Demais Cirurgias"],
        values=[circ_sum, onco_sum, resto_sum],
        hole=0.55,
        marker_colors=[COR_PERIGO, COR_AVISO, COR_CINZA],
        textinfo="percent+label",
    ))
    fig_donut.update_layout(
        template="plotly_white",
        showlegend=False,
        margin=dict(l=5, r=5, t=5, b=5),
        annotations=[dict(text="Alta<br>Complexidade", x=0.5, y=0.5,
                          font_size=13, showarrow=False)],
    )

    return (
        fmt_int(qtd_04_total),
        fmt_int(media_cirug),
        top_label,
        fig_barras,
        fig_donut,
    )


# ===========
# Callback: ABA 4 — Visão Territorial (Mapa Coroplético)
# ===========


@app.callback(
    Output("mapa-coropletico-sus", "figure"),
    Output("titulo-mapa",          "children"),
    Input("seletor-mapa",          "value"),
    Input("filtro-ano",            "value"),
    Input("filtro-mes",            "value"),
    Input("filtro-municipio",      "value"),
)
def atualizar_mapa(variavel, ano, mes, municipio):
    df = obter_dados_mapa(ano, mes, municipio)

    titulos = {
        "vl_total":  "Investimento Total por Município (R$)",
        "qtd_total": "Volume de Atendimentos por Município",
        "qtd_0304":  "Concentração Oncológica por Município",
    }
    titulo = titulos.get(variavel, "Mapa")

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            annotations=[{"text": "Sem dados para o filtro selecionado",
                          "x": 0.5, "y": 0.5, "showarrow": False}]
        )
        return fig, titulo

    # --- TETO DINÂMICO PARA CORRIGIR O CORTE VISUAL DE SÃO PAULO ---
    # Pegamos o percentil 96 para que o topo absoluto de SP não "apague" os outros estados
    teto_escala = df[variavel].quantile(0.96) if df[variavel].max() > 0 else 1
    if teto_escala == 0:
        teto_escala = df[variavel].max()

    fig = px.choropleth_mapbox(
        df,
        geojson=GEOJSON_ESTADO,
        locations="codigo_municipio_dv",
        featureidkey="properties.codarea_6",
        color=variavel,
        range_color=[0, teto_escala],  # <--- Mantém a barra de cores ativa e linear
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=3,
        center={"lat": -14, "lon": -55},
        opacity=0.7,
        hover_name="nome_municipio",  # <--- Mostra o NOME do município no topo do hover
        hover_data={"codigo_municipio_dv": False, variavel: True}  # <--- Oculta o ID numérico feio
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(
            title=None,
            thickness=15,
            len=0.6,
        ),
    )

    return fig, titulo


# ============
# Entry Point
# ============

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)