"""
db_connect.py
=============
Módulo de acesso a dados para o Dashboard SIH/SUS.
Responsabilidade: conexão com o banco de dados PostgreSQL e funções de
busca/agregação analítica por meio de queries SQL otimizadas.

Todas as funções aceitam filtros opcionais (ano_aih, mes_aih, nome_municipio).
Quando um filtro for None ou string vazia, ele é ignorado e a query retorna
o consolidado completo.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# -------------
# Mapeamento de rótulos amigáveis para as sub-variáveis cirúrgicas (Bloco 04)
# -------------
LABELS_CIRURGICAS = {
    "qtd_0401": "Pequenas Cirurgias / Pele",
    "qtd_0402": "Glândulas Endócrinas",
    "qtd_0403": "Sistema Nervoso",
    "qtd_0404": "Vias Aéreas / Face / Cabeça",
    "qtd_0405": "Aparelho da Visão",
    "qtd_0406": "Aparelho Circulatório",
    "qtd_0407": "Aparelho Digestivo",
    "qtd_0408": "Sistema Osteomuscular",
    "qtd_0409": "Aparelho Geniturinário",
    "qtd_0410": "Mama",
    "qtd_0411": "Obstétrica",
    "qtd_0412": "Torácica",
    "qtd_0413": "Reparadora",
    "qtd_0414": "Bucomaxilofacial",
    "qtd_0415": "Outras Cirurgias",
    "qtd_0416": "Oncologia Cirúrgica",
}

LABELS_CIRURGICAS_VL = {
    "vl_0401": "Pequenas Cirurgias / Pele",
    "vl_0402": "Glândulas Endócrinas",
    "vl_0403": "Sistema Nervoso",
    "vl_0404": "Vias Aéreas / Face / Cabeça",
    "vl_0405": "Aparelho da Visão",
    "vl_0406": "Aparelho Circulatório",
    "vl_0407": "Aparelho Digestivo",
    "vl_0408": "Sistema Osteomuscular",
    "vl_0409": "Aparelho Geniturinário",
    "vl_0410": "Mama",
    "vl_0411": "Obstétrica",
    "vl_0412": "Torácica",
    "vl_0413": "Reparadora",
    "vl_0414": "Bucomaxilofacial",
    "vl_0415": "Outras Cirurgias",
    "vl_0416": "Oncologia Cirúrgica",
}


# ---------------------
# Conexão
# --------------------

def obter_conexao():
    """
    Cria e retorna o motor SQLAlchemy conectado ao banco PostgreSQL.
    As credenciais são lidas das variáveis de ambiente definidas no .env.
    """
    host = os.getenv("DB_HOST")
    database = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([host, database, user, password]):
        raise ValueError(
            "Credenciais incompletas. Verifique DB_HOST, DB_NAME, DB_USER e "
            "DB_PASSWORD no arquivo .env."
        )

    port_env = os.getenv("DB_PORT")
    port = 5432 if not port_env or str(port_env).strip() in ("None", "") else int(port_env)

    url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(url)


# --------------
# Utilitário interno: construção dinâmica da cláusula WHERE
# -------------

def _build_where(params: dict) -> tuple[str, dict]:
    """
    Recebe um dict {coluna: valor} e retorna a cláusula WHERE e o dict de
    bindings para o SQLAlchemy. Filtros com valor None ou '' são ignorados.
    """
    clauses = []
    bindings = {}
    for col, val in params.items():
        if val is not None and str(val).strip() != "":
            clauses.append(f"{col} = :{col}")
            bindings[col] = val
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, bindings


# ------------------
# 1. Opções para os Dropdowns da Sidebar
# ------------------
def obter_opcoes_filtros() -> dict:
    """
    Retorna um dicionário com as listas únicas e ordenadas de:
        - anos    : lista de anos disponíveis (ano_aih)
        - meses   : lista de meses disponíveis (mes_aih)
        - municipios: lista de municípios disponíveis (nome_municipio)
    Usado para alimentar os Dropdowns da Sidebar.
    """
    engine = obter_conexao()
    query = text("""
        SELECT
            ARRAY(SELECT DISTINCT ano_aih  FROM sus_aih_residencia ORDER BY ano_aih)  AS anos,
            ARRAY(SELECT DISTINCT mes_aih  FROM sus_aih_residencia ORDER BY mes_aih)  AS meses,
            ARRAY(SELECT DISTINCT nome_municipio FROM sus_aih_residencia ORDER BY nome_municipio) AS municipios
    """)
    with engine.connect() as conn:
        row = conn.execute(query).fetchone()

    return {
        "anos":       [{"label": a, "value": a} for a in row.anos],
        "meses":      [{"label": m, "value": m} for m in row.meses],
        "municipios": [{"label": n, "value": n} for n in row.municipios],
    }


# --------------
# 2. Dados para a Aba 1 — Eficiência Orçamentária
# -------------

def obter_dados_orcamento(
    ano_aih: str | None = None,
    mes_aih: str | None = None,
    nome_municipio: str | None = None,
) -> pd.DataFrame:
    where, bindings = _build_where(
        {"ano_aih": ano_aih, "mes_aih": mes_aih, "nome_municipio": nome_municipio}
    )

    # TRAVA CIRÚRGICA: Para orçamento, só importam as linhas de valor financeiro
    clausula_conteudo = f"{where} AND conteudo = 'Valor_total'" if where else "WHERE conteudo = 'Valor_total'"

    sql = f"""
        SELECT
            ano_aih,
            mes_aih,
            SUM(vl_total)  AS vl_total,
            SUM(vl_02)     AS vl_02,
            SUM(vl_03)     AS vl_03,
            SUM(vl_04)     AS vl_04,
            SUM(vl_05)     AS vl_05,
            SUM(vl_0401)   AS vl_0401,
            SUM(vl_0402)   AS vl_0402,
            SUM(vl_0403)   AS vl_0403,
            SUM(vl_0404)   AS vl_0404,
            SUM(vl_0405)   AS vl_0405,
            SUM(vl_0406)   AS vl_0406,
            SUM(vl_0407)   AS vl_0407,
            SUM(vl_0408)   AS vl_0408,
            SUM(vl_0409)   AS vl_0409,
            SUM(vl_0410)   AS vl_0410,
            SUM(vl_0411)   AS vl_0411,
            SUM(vl_0412)   AS vl_0412,
            SUM(vl_0413)   AS vl_0413,
            SUM(vl_0414)   AS vl_0414,
            SUM(vl_0415)   AS vl_0415,
            SUM(vl_0416)   AS vl_0416
        FROM sus_aih_residencia
        {clausula_conteudo}
        GROUP BY ano_aih, mes_aih
        ORDER BY ano_aih, mes_aih
    """

    engine = obter_conexao()
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=bindings)

    df.fillna(0, inplace=True)
    df["periodo"] = df["ano_aih"].astype(str) + "/" + df["mes_aih"].astype(str).str.zfill(2)
    return df


# ==================
# 3. Dados para a Aba 2 — Pressão Assistencial
# ==================

# =====================
# 3. Dados para a Aba 2 — Pressão Assistencial
# =====================

def obter_dados_pressao(
    ano_aih: str | None = None,
    mes_aih: str | None = None,
    nome_municipio: str | None = None,
) -> pd.DataFrame:
    where, bindings = _build_where(
        {"ano_aih": ano_aih, "mes_aih": mes_aih, "nome_municipio": nome_municipio}
    )

    # ESTRATÉGIA BLINDADA: Se não for valor, é quantidade. Zero problemas com acentuação!
    clausula_conteudo = f"{where} AND conteudo != 'Valor_total'" if where else "WHERE conteudo != 'Valor_total'"

    sql = f"""
        SELECT
            nome_municipio,
            ano_aih,
            mes_aih,
            SUM(qtd_03)    AS qtd_03,
            SUM(qtd_0303)  AS qtd_0303,
            SUM(qtd_0304)  AS qtd_0304,
            SUM(qtd_0305)  AS qtd_0305,
            SUM(qtd_total) AS qtd_total
        FROM sus_aih_residencia
        {clausula_conteudo}
        GROUP BY nome_municipio, ano_aih, mes_aih
    """

    engine = obter_conexao()
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=bindings)

    df.fillna(0, inplace=True)
    
    # Proteção extra para garantir que as colunas de data sejam strings limpas antes de juntar
    if not df.empty:
        df["ano_aih"] = df["ano_aih"].astype(str).str.strip()
        df["mes_aih"] = df["mes_aih"].astype(str).str.strip().str.zfill(2)
        df["periodo"] = df["ano_aih"] + "/" + df["mes_aih"]
    else:
        # Cria um DataFrame estruturado mínimo para o Dash não estourar erro de falta de colunas
        df = pd.DataFrame(columns=["nome_municipio", "ano_aih", "mes_aih", "qtd_03", "qtd_0303", "qtd_0304", "qtd_0305", "qtd_total", "periodo"])
        
    return df


# ===================
# 4. Dados para a Aba 3 — Produtividade Cirúrgica
# ==================

def obter_dados_cirurgias(
    ano_aih: str | None = None,
    mes_aih: str | None = None,
    nome_municipio: str | None = None,
) -> pd.DataFrame:
    where, bindings = _build_where(
        {"ano_aih": ano_aih, "mes_aih": mes_aih, "nome_municipio": nome_municipio}
    )

    # ESTRATÉGIA BLINDADA: Mesma lógica reversa
    clausula_conteudo = f"{where} AND conteudo != 'Valor_total'" if where else "WHERE conteudo != 'Valor_total'"

    sql = f"""
        SELECT
            nome_municipio,
            SUM(qtd_04)    AS qtd_04,
            SUM(qtd_0401)  AS qtd_0401,
            SUM(qtd_0402)  AS qtd_0402,
            SUM(qtd_0403)  AS qtd_0403,
            SUM(qtd_0404)  AS qtd_0404,
            SUM(qtd_0405)  AS qtd_0405,
            SUM(qtd_0406)  AS qtd_0406,
            SUM(qtd_0407)  AS qtd_0407,
            SUM(qtd_0408)  AS qtd_0408,
            SUM(qtd_0409)  AS qtd_0409,
            SUM(qtd_0410)  AS qtd_0410,
            SUM(qtd_0411)  AS qtd_0411,
            SUM(qtd_0412)  AS qtd_0412,
            SUM(qtd_0413)  AS qtd_0413,
            SUM(qtd_0414)  AS qtd_0414,
            SUM(qtd_0415)  AS qtd_0415,
            SUM(qtd_0416)  AS qtd_0416
        FROM sus_aih_residencia
        {clausula_conteudo}
        GROUP BY nome_municipio
    """

    engine = obter_conexao()
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=bindings)

    df.fillna(0, inplace=True)
    
    if df.empty:
        # Evita o retorno None que quebra os gráficos do Plotly
        df = pd.DataFrame(columns=["nome_municipio", "qtd_04"] + [f"qtd_04{str(i).zfill(2)}" for i in range(1, 17)])
        
    return df


# ==================
# 5. Dados para a Aba 4 — Visão Territorial (Mapa)
# ==================

def obter_dados_mapa(
    ano_aih: str | None = None,
    mes_aih: str | None = None,
    nome_municipio: str | None = None,
) -> pd.DataFrame:
    where, bindings = _build_where(
        {"ano_aih": ano_aih, "mes_aih": mes_aih, "nome_municipio": nome_municipio}
    )

    # Voltou para codigo_municipio (sua coluna real) agrupando corretamente
    sql = f"""
        SELECT
            codigo_municipio AS codigo_municipio_dv,
            nome_municipio,
            SUM(CASE WHEN conteudo = 'Valor_total' THEN vl_total ELSE 0 END) AS vl_total,
            SUM(CASE WHEN conteudo != 'Valor_total' THEN qtd_total ELSE 0 END) AS qtd_total,
            SUM(CASE WHEN conteudo != 'Valor_total' THEN qtd_0304 ELSE 0 END) AS qtd_0304
        FROM sus_aih_residencia
        {where}
        GROUP BY codigo_municipio, nome_municipio
    """

    engine = obter_conexao()
    with engine.connect() as conn:
        df = pd.read_sql(text(sql), conn, params=bindings)

    df.fillna(0, inplace=True)
    return df