"""
Dashboard · Recomendador de lecturas con reglas de asociación (goodbooks-10k)
Ejecutar localmente:  streamlit run app.py
Lee los CSV exportados por el notebook (carpeta data/); no mina reglas.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

st.set_page_config(page_title="Recomendador de lecturas", page_icon="📚", layout="wide")

AZUL, ROJO, GRIS = "#1f3a5f", "#b23a48", "#6b7280"
SEP = " | "   # separador de libros dentro de un antecedente


# ------------------------------------------------------------------ datos
@st.cache_data
def cargar():
    reglas = pd.read_csv("data/reglas.csv")
    populares = pd.read_csv("data/populares.csv")
    hitrate = pd.read_csv("data/hitrate.csv")
    cobertura = pd.read_csv("data/cobertura.csv")
    resumen = pd.read_csv("data/resumen.csv").set_index("indicador")["valor"]
    # Reconstruimos los conjuntos para poder activar reglas
    reglas["antecedente_set"] = reglas["antecedente"].str.split(SEP, regex=False).apply(frozenset)
    reglas["regla"] = "{" + reglas["antecedente"].str.replace(SEP, ", ", regex=False) + "} ⇒ {" + reglas["consecuente"] + "}"
    return reglas, populares, hitrate, cobertura, resumen


reglas, populares, hitrate, cobertura, resumen = cargar()
libros = sorted(populares["libro"])


def recomendar(canasta, reglas, populares, top=5, orden="lift", lift_minimo=None):
    """Misma lógica que el notebook: activa reglas cuyo antecedente está en la canasta."""
    canasta = set(canasta)
    activa = reglas["antecedente_set"].apply(lambda x: x <= canasta)
    nueva = ~reglas["consecuente"].isin(canasta)
    candidatas = reglas[activa & nueva]
    if lift_minimo is not None and (candidatas.empty or candidatas["lift"].max() < lift_minimo):
        candidatas = candidatas.iloc[0:0]
    candidatas = (candidatas.sort_values([orden, "confianza"], ascending=False)
                  .drop_duplicates("consecuente").head(top))
    filas = [{"libro": r.consecuente, "origen": "regla", "regla": r.regla,
              "confianza": r.confianza, "lift": r.lift} for r in candidatas.itertuples()]
    ya = {f["libro"] for f in filas}
    for libro in populares:
        if len(filas) >= top:
            break
        if libro not in canasta and libro not in ya:
            filas.append({"libro": libro, "origen": "respaldo: más gustado", "regla": "—",
                          "confianza": np.nan, "lift": np.nan})
    return pd.DataFrame(filas)


def mapa_flujo(seleccion, alto=620):
    red = Network(height=f"{alto}px", width="100%", directed=True, cdn_resources="remote")
    soporte = populares.set_index("libro")["soporte"]
    lmin, lmax = seleccion["lift"].min(), seleccion["lift"].max()
    for libro in set(seleccion["antecedente"]) | set(seleccion["consecuente"]):
        red.add_node(libro, label=libro, shape="dot", color=AZUL, size=10 + 60 * soporte.get(libro, 0.05),
                     font={"size": 18, "color": AZUL, "strokeWidth": 4, "strokeColor": "white"},
                     title=f"{libro}\nsoporte: {soporte.get(libro, 0):.3f}")
    for r in seleccion.itertuples():
        t = (r.lift - lmin) / (lmax - lmin) if lmax > lmin else 1
        color = f"rgba(178,58,72,{0.3 + 0.7 * t:.2f})"
        red.add_edge(r.antecedente, r.consecuente, width=1 + 8 * r.confianza, color=color,
                     title=f"{r.antecedente} ⇒ {r.consecuente}\nconfianza: {r.confianza:.3f}\nlift: {r.lift:.2f}")
    red.barnes_hut(gravity=-9000, spring_length=170)
    return red.generate_html()


# ------------------------------------------------------------------ encabezado
st.title(" Recomendador de lecturas")
st.caption("Reglas de asociación sobre *goodbooks-10k* · transacción = lector · ítem = libro calificado con 4 o 5 ★")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Resumen de datos", "Explorador de reglas", "Visualizaciones", "Recomendador", "Evaluación"])

# ------------------------------------------------------------------ 1. resumen
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lectores (transacciones)", f"{int(resumen['transacciones']):,}".replace(",", "."))
    c2.metric("Libros (ítems)", int(resumen["items"]))
    c3.metric("Densidad de la matriz", f"{resumen['densidad']:.1%}")
    c4.metric("Libros por lector (prom.)", f"{resumen['promedio_items']:.1f}")

    st.subheader("Libros más gustados")
    n_top = st.slider("Cantidad de libros", 10, 100, 20, step=5)
    top = populares.head(n_top).sort_values("soporte")
    fig = px.bar(top, x="soporte", y="libro", orientation="h", hover_data=["autor", "lectores"],
                 color_discrete_sequence=[AZUL], height=max(400, 22 * n_top))
    fig.update_layout(yaxis_title=None, xaxis_title="soporte (proporción de lectores)")
    st.plotly_chart(fig, width="stretch")
    st.caption("Cola larga: el libro más gustado aparece en ~36 % de los lectores y el n.º 100 en ~8 %.")

# ------------------------------------------------------------------ 2. explorador
with tab2:
    st.subheader("Explorador de reglas")
    c1, c2, c3 = st.columns(3)
    sop_min = c1.slider("Soporte mínimo", 0.03, 0.30, 0.05, 0.01)
    conf_min = c2.slider("Confianza mínima", 0.30, 1.00, 0.50, 0.05)
    lift_min = c3.slider("Lift mínimo", 1.0, 10.0, 1.5, 0.1)

    c4, c5, c6 = st.columns([2, 2, 1])
    en_ant = c4.multiselect("Libro en el antecedente (si…)", libros)
    en_con = c5.multiselect("Libro en el consecuente (…entonces)", libros)
    with c6:
        solo_sig = st.checkbox("Solo significativas (Fisher + Holm)", True)
        sin_red = st.checkbox("Quitar redundantes", True)

    f = reglas[(reglas["soporte"] >= sop_min) & (reglas["confianza"] >= conf_min) & (reglas["lift"] >= lift_min)]
    if en_ant:
        f = f[f["antecedente_set"].apply(lambda x: bool(x & set(en_ant)))]
    if en_con:
        f = f[f["consecuente"].isin(en_con)]
    if solo_sig:
        f = f[f["significativa"]]
    if sin_red:
        f = f[~f["redundante"]]

    st.write(f"**{len(f):,}** reglas de {len(reglas):,}".replace(",", "."))
    tabla = f[["regla", "soporte", "confianza", "lift", "leverage", "conviccion", "p_ajustado"]].sort_values("lift", ascending=False)
    st.dataframe(tabla, width="stretch", hide_index=True, height=450,
                 column_config={c: st.column_config.NumberColumn(format="%.3f")
                                for c in ["soporte", "confianza", "lift", "leverage", "conviccion"]} |
                               {"p_ajustado": st.column_config.NumberColumn(format="%.2e")})
    st.download_button("⬇️ Descargar CSV", tabla.to_csv(index=False).encode("utf-8"),
                       "reglas_filtradas.csv", "text/csv")

# ------------------------------------------------------------------ 3. visualizaciones
with tab3:
    st.subheader("Dispersión de reglas: soporte vs. confianza (color = lift)")
    lift_disp = st.slider("Lift mínimo a mostrar", 1.0, 5.0, 1.0, 0.1, key="ld")
    d = reglas[reglas["lift"] >= lift_disp]
    fig = px.scatter(d, x="soporte", y="confianza", color="lift", hover_name="regla",
                     hover_data={"soporte": ":.3f", "confianza": ":.3f", "lift": ":.2f"},
                     color_continuous_scale="Reds", height=520)
    fig.update_traces(marker=dict(size=6, line=dict(width=0.3, color="white")))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Mapa de flujo libro → libro")
    st.caption("Grosor = confianza · color = lift · tamaño del nodo = soporte. Puedes arrastrar los nodos y hacer zoom.")
    c1, c2 = st.columns(2)
    lift_flujo = c1.slider("Lift mínimo", 1.5, 6.0, 2.5, 0.1, key="lf")
    excluir_saga = c2.checkbox("Solo libros de autores distintos (excluir sagas)", False)
    simples = reglas[(reglas["n_antecedente"] == 1) & (reglas["lift"] >= lift_flujo)]
    if excluir_saga:
        autor = populares.set_index("libro")["autor"]
        simples = simples[simples["antecedente"].map(autor) != simples["consecuente"].map(autor)]
    st.write(f"{len(simples)} reglas")
    if len(simples) > 0:
        components.html(mapa_flujo(simples.head(150)), height=640)  # grafo pyvis
    else:
        st.info("No hay reglas con ese filtro.")

# ------------------------------------------------------------------ 4. recomendador
with tab4:
    st.subheader("Arma la lista de libros que te gustaron")
    canasta = st.multiselect("Libros favoritos", libros, default=["The Hobbit", "The Fellowship of the Ring"])
    c1, c2, c3 = st.columns(3)
    top = c1.slider("N recomendaciones", 1, 10, 5)
    orden = c2.radio("Ordenar por", ["lift", "confianza"], horizontal=True)
    hibrido = c3.checkbox("Híbrido conmutado")
    lift_h = c3.slider("Lift mínimo del híbrido", 1.0, 5.0, 2.0, 0.1, disabled=not hibrido)

    rec = recomendar(canasta, reglas, populares["libro"].tolist(), top=top, orden=orden,
                     lift_minimo=lift_h if hibrido else None)

    usa_respaldo = (rec["origen"] != "regla").any()
    if not canasta:
        st.warning("🧊 Arranque en frío: sin libros favoritos no se activa ninguna regla → se recomiendan los más gustados.")
    elif (rec["origen"] != "regla").all():
        st.warning("🧊 Ninguna regla se activó (o ninguna supera el lift del híbrido) → respaldo de los más gustados.")
    elif usa_respaldo:
        st.info("Algunas posiciones se completaron con el respaldo de los más gustados.")
    else:
        st.success(f"Todas las recomendaciones provienen de reglas activas (ordenadas por {orden}).")

    st.dataframe(rec, width="stretch", hide_index=True,
                 column_config={"confianza": st.column_config.NumberColumn(format="%.3f"),
                                "lift": st.column_config.NumberColumn(format="%.2f")})

# ------------------------------------------------------------------ 5. evaluación
with tab5:
    st.subheader("Evaluación offline: HitRate@N (leave-one-out, 80/20, semilla 42)")
    st.caption(f"{int(resumen['casos_prueba']):,} lectores de prueba: se oculta un libro al azar y se mide si aparece "
               "entre las N recomendaciones.".replace(",", "."))
    tabla_hr = hitrate.pivot(index="N", columns="estrategia", values="hitrate")
    fig = px.line(hitrate, x="N", y="hitrate", color="estrategia", markers=True, height=450,
                  color_discrete_sequence=[AZUL, "#3f7cac", "#8fb8de", ROJO])
    fig.update_layout(xaxis=dict(tickvals=[1, 3, 5, 10]), yaxis_title="HitRate@N")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(tabla_hr.style.format("{:.3f}"), width="stretch")
    st.subheader("Cobertura y uso de reglas")
    st.dataframe(cobertura.set_index("estrategia").style.format("{:.1%}"), width="stretch")
    st.markdown(
        "- Las reglas aciertan **≈ 2 veces más** que recomendar lo más popular.\n"
        "- **Confianza** gana con listas cortas (más precisa, recomienda libros populares); "
        "**lift** gana en N = 10 y cubre más catálogo (más novedad).")
