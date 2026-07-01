import traceback

print("=== 1. Testando imports de db_connect ===")
try:
    from db_connect import (
        obter_opcoes_filtros, obter_dados_orcamento,
        obter_dados_pressao, obter_dados_cirurgias, obter_dados_mapa,
        LABELS_CIRURGICAS, LABELS_CIRURGICAS_VL,
    )
    print("  OK: imports carregados")
except Exception:
    traceback.print_exc()

print()
print("=== 2. Testando obter_opcoes_filtros ===")
try:
    opt = obter_opcoes_filtros()
    print("  anos (3 primeiros):", opt["anos"][:3])
    print("  meses (3 primeiros):", opt["meses"][:3])
    print("  municipios count:", len(opt["municipios"]))
except Exception:
    traceback.print_exc()

print()
print("=== 3. Testando obter_dados_orcamento (sem filtro) ===")
try:
    df = obter_dados_orcamento()
    print("  shape:", df.shape)
    print("  colunas:", list(df.columns))
    print("  dtypes:\n", df.dtypes)
    print("  head(2):\n", df.head(2).to_string())
except Exception:
    traceback.print_exc()

print()
print("=== 4. Testando obter_dados_pressao (sem filtro) ===")
try:
    df = obter_dados_pressao()
    print("  shape:", df.shape)
    print("  colunas:", list(df.columns))
    print("  head(2):\n", df.head(2).to_string())
except Exception:
    traceback.print_exc()

print()
print("=== 5. Testando obter_dados_cirurgias (sem filtro) ===")
try:
    df = obter_dados_cirurgias()
    print("  shape:", df.shape)
    print("  colunas:", list(df.columns))
    print("  head(2):\n", df.head(2).to_string())
except Exception:
    traceback.print_exc()

print()
print("=== 6. Testando obter_dados_mapa (sem filtro) ===")
try:
    df = obter_dados_mapa()
    print("  shape:", df.shape)
    print("  colunas:", list(df.columns))
    print("  head(2):\n", df.head(2).to_string())
except Exception:
    traceback.print_exc()

print()
print("=== 7. Testando dashboard imports ===")
try:
    import dash
    import dash_bootstrap_components as dbc
    from dash import dcc, html, Input, Output
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    print("  OK: todos os imports do dashboard")
except Exception:
    traceback.print_exc()

print()
print("=== 8. Testando scatter com size=0 (bug conhecido do Plotly) ===")
try:
    import pandas as pd
    import plotly.express as px
    df_test = pd.DataFrame({
        "qtd_0303": [0, 10, 5],
        "complexidade": [0, 20, 3],
        "qtd_total": [0, 100, 50],
        "nome_municipio": ["A", "B", "C"],
    })
    # Plotly lança erro se size tiver valores 0 ou negativos
    df_test["qtd_total"] = df_test["qtd_total"].clip(lower=1)
    fig = px.scatter(df_test, x="qtd_0303", y="complexidade",
                     size="qtd_total", size_max=55)
    print("  OK: scatter com size clip(1) funciona")
except Exception:
    traceback.print_exc()

print()
print("=== 9. Testando treemap com px.treemap ===")
try:
    import plotly.express as px
    import pandas as pd
    df_t = pd.DataFrame({"Especialidade": ["A", "B"], "Valor": [100.0, 200.0]})
    fig = px.treemap(df_t, path=["Especialidade"], values="Valor")
    print("  OK: treemap funciona")
except Exception:
    traceback.print_exc()

print()
print("=== Diagnóstico concluído ===")
